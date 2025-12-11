"""
Thai ID Card Agent - ส่งข้อมูลไป Railway Server
================================================
โปรแกรมอ่านบัตรประชาชนแล้วส่งข้อมูลไปเก็บที่ Railway

การใช้งาน:
1. เสียบเครื่องอ่านบัตร + ใส่บัตร
2. รันโปรแกรมนี้
3. กดปุ่ม "สแกนและส่งไป Railway"
4. Next.js เรียก Railway API เพื่อดึงข้อมูล

Build เป็น .exe:
    pyinstaller --onefile --windowed --name="ThaiIDAgent" thai_id_agent.py
"""

import sys
import os
import json
import time
import threading
import requests
from datetime import datetime

# Smart Card
try:
    from smartcard.System import readers
    from smartcard.util import toHexString, toBytes
    from smartcard.Exceptions import NoCardException, CardConnectionException
    SMARTCARD_AVAILABLE = True
except ImportError:
    SMARTCARD_AVAILABLE = False
    print("Warning: pyscard not installed. Install with: pip install pyscard")

# GUI
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# ====================================================================================
# CONFIGURATION - แก้ไข URL ตรงนี้
# ====================================================================================

RAILWAY_API_URL = "https://believable-ambition-production.up.railway.app"
RAILWAY_RECEIVE_ENDPOINT = f"{RAILWAY_API_URL}/api/thaiid/receive"


# ====================================================================================
# THAI ID CARD READER CLASS
# ====================================================================================

class ThaiIDCardReader:
    """อ่านข้อมูลจากบัตรประชาชนไทยผ่าน Smart Card Reader"""
    
    # Thai National ID Card Applet (Ministry of Interior)
    MOI_AID = [0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]
    
    # APDU Commands
    APDU_SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08] + MOI_AID
    APDU_GET_CID = [0x80, 0xB0, 0x00, 0x04, 0x02, 0x00, 0x0D]
    APDU_GET_NAME_TH = [0x80, 0xB0, 0x00, 0x11, 0x02, 0x00, 0x64]
    APDU_GET_NAME_EN = [0x80, 0xB0, 0x00, 0x75, 0x02, 0x00, 0x64]
    APDU_GET_DOB = [0x80, 0xB0, 0x00, 0xD9, 0x02, 0x00, 0x08]
    APDU_GET_GENDER = [0x80, 0xB0, 0x00, 0xE1, 0x02, 0x00, 0x01]
    APDU_GET_ADDRESS = [0x80, 0xB0, 0x15, 0x79, 0x02, 0x00, 0x64]
    APDU_GET_ISSUE_DATE = [0x80, 0xB0, 0x00, 0xF6, 0x02, 0x00, 0x08]
    APDU_GET_EXPIRE_DATE = [0x80, 0xB0, 0x00, 0xFE, 0x02, 0x00, 0x08]
    APDU_GET_ISSUER = [0x80, 0xB0, 0x00, 0xE4, 0x02, 0x00, 0x64]
    
    def __init__(self):
        self.connection = None
        self.reader = None
    
    def get_readers(self):
        """ดึงรายชื่อเครื่องอ่านที่เชื่อมต่ออยู่"""
        if not SMARTCARD_AVAILABLE:
            return []
        try:
            return [str(r) for r in readers()]
        except Exception:
            return []
    
    def connect(self, reader_index=0):
        """เชื่อมต่อกับเครื่องอ่านบัตร"""
        if not SMARTCARD_AVAILABLE:
            raise Exception("pyscard library not installed")
        
        available_readers = readers()
        if not available_readers:
            raise Exception("ไม่พบเครื่องอ่านบัตร กรุณาเสียบเครื่องอ่าน")
        
        self.reader = available_readers[reader_index]
        self.connection = self.reader.createConnection()
        
        try:
            self.connection.connect()
        except NoCardException:
            raise Exception("ไม่พบบัตร กรุณาใส่บัตรประชาชน")
        except CardConnectionException as e:
            raise Exception(f"ไม่สามารถเชื่อมต่อบัตรได้: {str(e)}")
        
        # Select Thai ID Card Applet
        response, sw1, sw2 = self.connection.transmit(self.APDU_SELECT)
        
        # SW1=0x61 means "more data available" - need GET RESPONSE
        if sw1 == 0x61:
            get_response = [0x00, 0xC0, 0x00, 0x00, sw2]
            response, sw1, sw2 = self.connection.transmit(get_response)
        
        # Check if SELECT was successful
        if sw1 != 0x90 or sw2 != 0x00:
            raise Exception(f"ไม่ใช่บัตรประชาชนไทย หรือบัตรไม่รองรับ (SW: {hex(sw1)} {hex(sw2)})")
        
        return True
    
    def _send_apdu(self, apdu):
        """ส่ง APDU command และรับ response"""
        response, sw1, sw2 = self.connection.transmit(apdu)
        if sw1 == 0x90 and sw2 == 0x00:
            return bytes(response)
        elif sw1 == 0x61:
            get_response = [0x00, 0xC0, 0x00, 0x00, sw2]
            response, sw1, sw2 = self.connection.transmit(get_response)
            return bytes(response)
        return None
    
    def _decode_thai(self, data):
        """ถอดรหัส TIS-620 เป็น UTF-8"""
        if not data:
            return ""
        try:
            text = data.decode('tis-620').strip()
            text = text.replace('#', ' ').strip()
            text = ' '.join(text.split())
            return text
        except:
            return ""
    
    def _parse_name(self, name_str):
        """แยกชื่อ-นามสกุล"""
        parts = name_str.split('#') if '#' in name_str else name_str.split()
        parts = [p.strip() for p in parts if p.strip()]
        
        result = {'title': '', 'firstName': '', 'middleName': '', 'lastName': '', 'fullName': name_str}
        
        if len(parts) >= 1:
            result['title'] = parts[0]
        if len(parts) >= 2:
            result['firstName'] = parts[1]
        if len(parts) >= 4:
            result['middleName'] = parts[2]
            result['lastName'] = parts[3]
        elif len(parts) >= 3:
            result['lastName'] = parts[2]
        
        return result
    
    def _format_date(self, date_str):
        """แปลงวันที่เป็น DD/MM/YYYY"""
        if len(date_str) == 8:
            return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
        return date_str
    
    def _format_cid(self, cid):
        """แปลง CID เป็นรูปแบบ X-XXXX-XXXXX-XX-X"""
        if len(cid) == 13:
            return f"{cid[0]}-{cid[1:5]}-{cid[5:10]}-{cid[10:12]}-{cid[12]}"
        return cid
    
    def _parse_address(self, addr_str):
        """แยกที่อยู่"""
        result = {
            'full': addr_str,
            'houseNo': '',
            'village': '',
            'lane': '',
            'road': '',
            'subDistrict': '',
            'district': '',
            'province': '',
            'postalCode': ''
        }
        
        parts = [p.strip() for p in addr_str.split('#') if p.strip()]
        
        if len(parts) >= 1:
            result['houseNo'] = parts[0]
        if len(parts) >= 2:
            result['village'] = parts[1]
        if len(parts) >= 3:
            result['lane'] = parts[2]
        if len(parts) >= 4:
            result['road'] = parts[3]
        if len(parts) >= 5:
            result['subDistrict'] = parts[4]
        if len(parts) >= 6:
            result['district'] = parts[5]
        if len(parts) >= 7:
            result['province'] = parts[6]
        
        return result
    
    def read_all(self):
        """อ่านข้อมูลทั้งหมดจากบัตร"""
        data = {}
        
        # CID - filter only digits (0-9)
        raw = self._send_apdu(self.APDU_GET_CID)
        if raw:
            # Filter only ASCII digits (0x30-0x39)
            cid = ''.join(chr(b) for b in raw if 0x30 <= b <= 0x39)
            if len(cid) == 13:
                data['cid'] = self._format_cid(cid)
                data['cidRaw'] = cid
        
        # Thai Name
        raw = self._send_apdu(self.APDU_GET_NAME_TH)
        if raw:
            name_th = self._decode_thai(raw)
            data['name'] = {'th': self._parse_name(name_th)}
        
        # English Name
        raw = self._send_apdu(self.APDU_GET_NAME_EN)
        if raw:
            name_en = raw.decode('ascii', errors='ignore').strip()
            name_en = name_en.replace('#', ' ').strip()
            if 'name' not in data:
                data['name'] = {}
            data['name']['en'] = self._parse_name(name_en)
        
        # Date of Birth
        raw = self._send_apdu(self.APDU_GET_DOB)
        if raw:
            dob = raw.decode('ascii', errors='ignore').strip()
            data['birthDate'] = self._format_date(dob)
            data['birthDateRaw'] = dob
        
        # Gender
        raw = self._send_apdu(self.APDU_GET_GENDER)
        if raw:
            gender_code = raw.decode('ascii', errors='ignore').strip()
            data['gender'] = 'ชาย' if gender_code == '1' else 'หญิง'
            data['genderCode'] = gender_code
        
        # Address
        raw = self._send_apdu(self.APDU_GET_ADDRESS)
        if raw:
            addr = self._decode_thai(raw)
            data['address'] = self._parse_address(addr)
        
        # Issue Date
        raw = self._send_apdu(self.APDU_GET_ISSUE_DATE)
        if raw:
            issue = raw.decode('ascii', errors='ignore').strip()
            data['issueDate'] = self._format_date(issue)
        
        # Expire Date
        raw = self._send_apdu(self.APDU_GET_EXPIRE_DATE)
        if raw:
            expire = raw.decode('ascii', errors='ignore').strip()
            data['expireDate'] = self._format_date(expire)
        
        # Issuer
        raw = self._send_apdu(self.APDU_GET_ISSUER)
        if raw:
            data['issuer'] = self._decode_thai(raw)
        
        return data
    
    def disconnect(self):
        """ยกเลิกการเชื่อมต่อ"""
        if self.connection:
            try:
                self.connection.disconnect()
            except:
                pass
            self.connection = None


# ====================================================================================
# GUI APPLICATION
# ====================================================================================

class ThaiIDAgentApp:
    """แอปพลิเคชัน GUI สำหรับอ่านบัตรแล้วส่งไป Railway"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Thai ID Card Agent v1.0")
        self.root.geometry("550x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f4f8')
        
        self.reader = ThaiIDCardReader() if SMARTCARD_AVAILABLE else None
        self.last_data = None
        
        self.setup_ui()
        self.check_reader()
    
    def setup_ui(self):
        """สร้าง UI"""
        # Header
        header = tk.Frame(self.root, bg='#4F46E5', height=100)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🪪 Thai ID Card Agent", 
                 font=('Segoe UI', 20, 'bold'), 
                 fg='white', bg='#4F46E5').pack(pady=15)
        tk.Label(header, text="อ่านบัตรแล้วส่งข้อมูลไป Railway Server", 
                 font=('Segoe UI', 11), 
                 fg='#c7d2fe', bg='#4F46E5').pack()
        
        # Main content
        content = tk.Frame(self.root, padx=25, pady=20, bg='#f0f4f8')
        content.pack(fill='both', expand=True)
        
        # Server Info
        server_frame = tk.LabelFrame(content, text="🌐 Railway Server", 
                                      font=('Segoe UI', 10, 'bold'),
                                      padx=15, pady=10, bg='#f0f4f8')
        server_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(server_frame, text=RAILWAY_API_URL, 
                 font=('Consolas', 10), fg='#4F46E5', bg='#f0f4f8').pack(anchor='w')
        
        self.server_status = tk.Label(server_frame, text="⏳ ยังไม่ได้ตรวจสอบ", 
                                       font=('Segoe UI', 9), bg='#f0f4f8')
        self.server_status.pack(anchor='w', pady=(5, 0))
        
        # Reader Status
        reader_frame = tk.LabelFrame(content, text="📟 เครื่องอ่านบัตร", 
                                      font=('Segoe UI', 10, 'bold'),
                                      padx=15, pady=10, bg='#f0f4f8')
        reader_frame.pack(fill='x', pady=(0, 15))
        
        self.reader_status = tk.Label(reader_frame, text="กำลังตรวจสอบ...", 
                                       font=('Segoe UI', 10), bg='#f0f4f8')
        self.reader_status.pack(anchor='w')
        
        # Scan Button
        self.scan_btn = tk.Button(content, 
                                   text="🔍 สแกนบัตรและส่งไป Railway",
                                   font=('Segoe UI', 14, 'bold'),
                                   bg='#10B981', fg='white',
                                   activebackground='#059669',
                                   activeforeground='white',
                                   height=2, cursor='hand2',
                                   relief='flat',
                                   command=self.scan_and_send)
        self.scan_btn.pack(fill='x', pady=(0, 15))
        
        # Status Label
        self.status_label = tk.Label(content, text="", 
                                      font=('Segoe UI', 10),
                                      bg='#f0f4f8', wraplength=480)
        self.status_label.pack(pady=(0, 10))
        
        # Result Frame
        result_frame = tk.LabelFrame(content, text="📋 ข้อมูลที่สแกนได้", 
                                      font=('Segoe UI', 10, 'bold'),
                                      padx=15, pady=10, bg='#f0f4f8')
        result_frame.pack(fill='both', expand=True)
        
        # Scrollable Text
        text_frame = tk.Frame(result_frame, bg='#f0f4f8')
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.result_text = tk.Text(text_frame, font=('Segoe UI', 10), 
                                    height=15, state='disabled',
                                    wrap='word', bg='white',
                                    yscrollcommand=scrollbar.set)
        self.result_text.pack(fill='both', expand=True)
        scrollbar.config(command=self.result_text.yview)
        
        # Footer
        footer = tk.Frame(self.root, bg='#e2e8f0', height=35)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
        tk.Label(footer, text="Next.js เรียก: GET /api/thaiid/latest เพื่อดึงข้อมูล",
                font=('Segoe UI', 9), fg='#64748b', bg='#e2e8f0').pack(pady=8)
    
    def check_reader(self):
        """ตรวจสอบเครื่องอ่านบัตร"""
        if self.reader:
            available = self.reader.get_readers()
            if available:
                self.reader_status.config(
                    text=f"✅ พบเครื่องอ่าน: {available[0][:40]}...", 
                    fg='#059669'
                )
                self.scan_btn.config(state='normal')
            else:
                self.reader_status.config(
                    text="⚠️ ไม่พบเครื่องอ่านบัตร - กรุณาเสียบ USB", 
                    fg='#D97706'
                )
                self.scan_btn.config(state='disabled')
        else:
            self.reader_status.config(
                text="❌ ไม่สามารถใช้งานได้ - ติดตั้ง pyscard", 
                fg='#DC2626'
            )
            self.scan_btn.config(state='disabled')
        
        # Check again every 3 seconds
        self.root.after(3000, self.check_reader)
    
    def scan_and_send(self):
        """สแกนบัตรแล้วส่งไป Railway"""
        self.scan_btn.config(state='disabled', text='⏳ กำลังอ่านบัตร...')
        self.status_label.config(text="", fg='#1f2937')
        self.root.update()
        
        try:
            # Step 1: อ่านบัตร
            self.status_label.config(text="📖 กำลังอ่านข้อมูลจากบัตร...")
            self.root.update()
            
            self.reader.connect()
            data = self.reader.read_all()
            self.reader.disconnect()
            
            self.last_data = data
            self.display_result(data)
            
            # Step 2: ส่งไป Railway
            self.status_label.config(text="📤 กำลังส่งข้อมูลไป Railway...")
            self.scan_btn.config(text='⏳ กำลังส่งข้อมูล...')
            self.root.update()
            
            response = requests.post(
                RAILWAY_RECEIVE_ENDPOINT,
                json={
                    'data': data,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'ThaiIDAgent'
                },
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.status_label.config(
                    text=f"✅ ส่งข้อมูลสำเร็จ! Next.js สามารถดึงข้อมูลได้แล้ว", 
                    fg='#059669'
                )
                self.server_status.config(text="✅ เชื่อมต่อสำเร็จ", fg='#059669')
            else:
                self.status_label.config(
                    text=f"⚠️ Server ตอบกลับ: {response.status_code}", 
                    fg='#D97706'
                )
            
        except requests.exceptions.ConnectionError:
            self.status_label.config(
                text="❌ ไม่สามารถเชื่อมต่อ Railway Server ได้", 
                fg='#DC2626'
            )
            self.server_status.config(text="❌ ไม่สามารถเชื่อมต่อได้", fg='#DC2626')
            
        except requests.exceptions.Timeout:
            self.status_label.config(
                text="❌ หมดเวลาเชื่อมต่อ Railway Server", 
                fg='#DC2626'
            )
            
        except Exception as e:
            self.reader.disconnect()
            self.status_label.config(text=f"❌ {str(e)}", fg='#DC2626')
        
        finally:
            self.scan_btn.config(state='normal', text='🔍 สแกนบัตรและส่งไป Railway')
    
    def display_result(self, data):
        """แสดงผลการสแกน"""
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', 'end')
        
        text = f"""✅ อ่านบัตรสำเร็จ!

📝 เลขบัตร: {data.get('cid', '-')}

👤 ชื่อ (ไทย): {data.get('name', {}).get('th', {}).get('fullName', '-')}

👤 ชื่อ (อังกฤษ): {data.get('name', {}).get('en', {}).get('fullName', '-')}

🎂 วันเกิด: {data.get('birthDate', '-')}

⚧ เพศ: {data.get('gender', '-')}

📍 ที่อยู่: {data.get('address', {}).get('full', '-')}

📅 วันออกบัตร: {data.get('issueDate', '-')}
📅 วันหมดอายุ: {data.get('expireDate', '-')}
"""
        
        self.result_text.insert('end', text)
        self.result_text.config(state='disabled')
    
    def run(self):
        """รันแอปพลิเคชัน"""
        self.root.mainloop()


# ====================================================================================
# CONSOLE MODE
# ====================================================================================

def run_console_mode():
    """รันในโหมด console"""
    import time
    
    print("=" * 50)
    print("  Thai ID Card Agent - Console Mode")
    print("=" * 50)
    print(f"\n🌐 Railway Server: {RAILWAY_API_URL}")
    print(f"📤 Endpoint: {RAILWAY_RECEIVE_ENDPOINT}")
    
    reader = ThaiIDCardReader()
    
    # Check if stdin is available (not available in --windowed mode)
    has_stdin = sys.stdin is not None and hasattr(sys.stdin, 'read')
    
    if has_stdin:
        # Interactive mode with Enter key
        while True:
            print("\n" + "-" * 40)
            try:
                input("กด Enter เพื่อสแกนบัตร (Ctrl+C เพื่อออก)...")
            except (RuntimeError, EOFError):
                # stdin lost, switch to auto mode
                has_stdin = False
                print("⚠️ สลับไปโหมดอัตโนมัติ...")
                break
            
            try:
                print("📖 กำลังอ่านบัตร...")
                reader.connect()
                data = reader.read_all()
                reader.disconnect()
                
                print(f"✅ อ่านสำเร็จ: {data.get('cid')} - {data.get('name', {}).get('th', {}).get('fullName')}")
                
                print("📤 กำลังส่งไป Railway...")
                response = requests.post(
                    RAILWAY_RECEIVE_ENDPOINT,
                    json={'data': data, 'timestamp': datetime.now().isoformat()},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    print("✅ ส่งสำเร็จ!")
                else:
                    print(f"⚠️ Server ตอบกลับ: {response.status_code}")
                    
            except KeyboardInterrupt:
                print("\n\n👋 ออกจากโปรแกรม")
                break
            except Exception as e:
                reader.disconnect()
                print(f"❌ Error: {e}")
    
    if not has_stdin:
        # Auto-scan mode (for --windowed .exe without stdin)
        print("\n🔄 โหมดอัตโนมัติ - กำลังสแกนบัตร...")
        try:
            print("📖 กำลังอ่านบัตร...")
            reader.connect()
            data = reader.read_all()
            reader.disconnect()
            
            print(f"✅ อ่านสำเร็จ: {data.get('cid')} - {data.get('name', {}).get('th', {}).get('fullName')}")
            
            print("📤 กำลังส่งไป Railway...")
            response = requests.post(
                RAILWAY_RECEIVE_ENDPOINT,
                json={'data': data, 'timestamp': datetime.now().isoformat()},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ ส่งสำเร็จ!")
            else:
                print(f"⚠️ Server ตอบกลับ: {response.status_code}")
            
            print("\n✅ เสร็จสิ้น - ปิดโปรแกรมใน 5 วินาที...")
            time.sleep(5)
                
        except Exception as e:
            reader.disconnect()
            print(f"❌ Error: {e}")
            print("\nปิดโปรแกรมใน 5 วินาที...")
            time.sleep(5)


# ====================================================================================
# MAIN
# ====================================================================================

def main():
    """Main entry point"""
    if '--console' in sys.argv or '--no-gui' in sys.argv:
        run_console_mode()
    elif TKINTER_AVAILABLE:
        app = ThaiIDAgentApp()
        app.run()
    else:
        run_console_mode()


if __name__ == '__main__':
    main()
