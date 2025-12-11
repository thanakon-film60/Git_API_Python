"""
Thai ID Card Reader - Desktop Application
==========================================
โปรแกรมอ่านบัตรประชาชนไทย สำหรับติดตั้งบนเครื่องผู้ใช้
เปิด API ที่ localhost:5051 ให้เว็บไซต์เรียกใช้ได้

Build เป็น .exe ด้วยคำสั่ง:
    pyinstaller --onefile --windowed --icon=icon.ico --name="ThaiIDReader" thai_id_reader.py
"""

import sys
import os
import json
import time
import threading
import webbrowser
from datetime import datetime

# Flask for API Server
from flask import Flask, jsonify, request
from flask_cors import CORS

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
        if sw1 != 0x90 or sw2 != 0x00:
            raise Exception("ไม่ใช่บัตรประชาชนไทย หรือบัตรไม่รองรับ")
        
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
        
        # CID
        raw = self._send_apdu(self.APDU_GET_CID)
        if raw:
            cid = raw.decode('ascii').strip()
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
            dob = raw.decode('ascii').strip()
            data['birthDate'] = self._format_date(dob)
            data['birthDateRaw'] = dob
        
        # Gender
        raw = self._send_apdu(self.APDU_GET_GENDER)
        if raw:
            gender_code = raw.decode('ascii').strip()
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
            issue = raw.decode('ascii').strip()
            data['issueDate'] = self._format_date(issue)
        
        # Expire Date
        raw = self._send_apdu(self.APDU_GET_EXPIRE_DATE)
        if raw:
            expire = raw.decode('ascii').strip()
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
# FLASK API SERVER
# ====================================================================================

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Global state
server_state = {
    'reader': ThaiIDCardReader() if SMARTCARD_AVAILABLE else None,
    'last_scan': None,
    'scan_count': 0
}


@app.route('/api/health', methods=['GET'])
def health_check():
    """ตรวจสอบสถานะ API"""
    reader = server_state['reader']
    available_readers = reader.get_readers() if reader else []
    
    return jsonify({
        'status': 'online',
        'service': 'Thai ID Card Reader',
        'version': '1.0.0',
        'hasReader': len(available_readers) > 0,
        'readers': available_readers,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/readers', methods=['GET'])
def get_readers():
    """ดึงรายชื่อเครื่องอ่านทั้งหมด"""
    reader = server_state['reader']
    available_readers = reader.get_readers() if reader else []
    
    return jsonify({
        'success': True,
        'readers': available_readers,
        'count': len(available_readers)
    })


@app.route('/api/scan', methods=['GET', 'POST'])
def scan_card():
    """อ่านข้อมูลจากบัตรประชาชน"""
    reader = server_state['reader']
    
    if not reader:
        return jsonify({
            'success': False,
            'message': 'Smart card library not available'
        }), 500
    
    start_time = time.time()
    
    try:
        reader.connect()
        data = reader.read_all()
        reader.disconnect()
        
        scan_time = round(time.time() - start_time, 2)
        server_state['last_scan'] = data
        server_state['scan_count'] += 1
        
        return jsonify({
            'success': True,
            'data': data,
            'scanTime': scan_time,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        reader.disconnect()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


@app.route('/api/last', methods=['GET'])
def get_last_scan():
    """ดึงข้อมูลการสแกนครั้งล่าสุด"""
    return jsonify({
        'success': server_state['last_scan'] is not None,
        'data': server_state['last_scan'],
        'scanCount': server_state['scan_count']
    })


# ====================================================================================
# GUI APPLICATION
# ====================================================================================

class ThaiIDReaderApp:
    """แอปพลิเคชัน GUI สำหรับอ่านบัตรประชาชน"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Thai ID Card Reader v1.0")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # Try to set icon
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
            else:
                icon_path = 'icon.ico'
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.server_thread = None
        self.server_running = False
        
        self.setup_ui()
        self.start_server()
        self.check_reader()
    
    def setup_ui(self):
        """สร้าง UI"""
        # Header
        header = tk.Frame(self.root, bg='#4F46E5', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🪪 Thai ID Card Reader", 
                 font=('Segoe UI', 18, 'bold'), 
                 fg='white', bg='#4F46E5').pack(pady=20)
        
        # Main content
        content = tk.Frame(self.root, padx=20, pady=20)
        content.pack(fill='both', expand=True)
        
        # Status Frame
        status_frame = ttk.LabelFrame(content, text="📡 สถานะการเชื่อมต่อ", padding=15)
        status_frame.pack(fill='x', pady=(0, 15))
        
        self.server_status = tk.Label(status_frame, text="⏳ กำลังเริ่มต้น...", 
                                       font=('Segoe UI', 11))
        self.server_status.pack(anchor='w')
        
        self.reader_status = tk.Label(status_frame, text="📟 กำลังตรวจสอบ...", 
                                       font=('Segoe UI', 11))
        self.reader_status.pack(anchor='w', pady=(5, 0))
        
        # API Info
        api_frame = ttk.LabelFrame(content, text="🔗 API Endpoint", padding=15)
        api_frame.pack(fill='x', pady=(0, 15))
        
        api_url = tk.Entry(api_frame, font=('Consolas', 12), justify='center')
        api_url.insert(0, "http://localhost:5051")
        api_url.config(state='readonly')
        api_url.pack(fill='x')
        
        tk.Label(api_frame, text="คัดลอก URL นี้ไปใช้ในโค้ด React/Next.js ของคุณ",
                font=('Segoe UI', 9), fg='gray').pack(pady=(5, 0))
        
        # Scan Button
        self.scan_btn = tk.Button(content, text="🔍 สแกนบัตรประชาชน",
                                   font=('Segoe UI', 14, 'bold'),
                                   bg='#10B981', fg='white',
                                   activebackground='#059669',
                                   height=2, cursor='hand2',
                                   command=self.manual_scan)
        self.scan_btn.pack(fill='x', pady=(0, 15))
        
        # Result Frame
        result_frame = ttk.LabelFrame(content, text="📋 ผลการสแกน", padding=15)
        result_frame.pack(fill='both', expand=True)
        
        self.result_text = tk.Text(result_frame, font=('Segoe UI', 10), 
                                    height=12, state='disabled',
                                    wrap='word')
        self.result_text.pack(fill='both', expand=True)
        
        # Footer
        footer = tk.Frame(self.root, bg='#F3F4F6', height=40)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
        tk.Label(footer, text="พัฒนาโดย thanakon-film60 | Port: 5051",
                font=('Segoe UI', 9), fg='gray', bg='#F3F4F6').pack(pady=10)
    
    def start_server(self):
        """เริ่ม Flask server ใน background thread"""
        def run_server():
            self.server_running = True
            app.run(host='0.0.0.0', port=5051, threaded=True, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Update status after delay
        self.root.after(1500, self.update_server_status)
    
    def update_server_status(self):
        """อัพเดทสถานะ server"""
        self.server_status.config(text="✅ API Server พร้อมใช้งาน (Port 5051)", fg='#059669')
    
    def check_reader(self):
        """ตรวจสอบเครื่องอ่านบัตร"""
        reader = server_state['reader']
        if reader:
            available = reader.get_readers()
            if available:
                self.reader_status.config(
                    text=f"✅ พบเครื่องอ่าน: {available[0][:30]}...", 
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
    
    def manual_scan(self):
        """สแกนบัตรจากปุ่ม GUI"""
        self.scan_btn.config(state='disabled', text='⏳ กำลังอ่าน...')
        self.root.update()
        
        reader = server_state['reader']
        try:
            reader.connect()
            data = reader.read_all()
            reader.disconnect()
            
            server_state['last_scan'] = data
            server_state['scan_count'] += 1
            
            self.display_result(data)
            
        except Exception as e:
            reader.disconnect()
            self.result_text.config(state='normal')
            self.result_text.delete('1.0', 'end')
            self.result_text.insert('end', f"❌ เกิดข้อผิดพลาด:\n{str(e)}")
            self.result_text.config(state='disabled')
        
        finally:
            self.scan_btn.config(state='normal', text='🔍 สแกนบัตรประชาชน')
    
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
# MAIN
# ====================================================================================

def run_console_mode():
    """รันในโหมด console (ไม่มี GUI)"""
    print("=" * 50)
    print("  Thai ID Card Reader API Server")
    print("=" * 50)
    print(f"\n🌐 API Server running at: http://localhost:5051")
    print("\n📖 API Endpoints:")
    print("   GET  /api/health  - ตรวจสอบสถานะ")
    print("   GET  /api/readers - ดูเครื่องอ่านที่เชื่อมต่อ")
    print("   POST /api/scan    - อ่านบัตรประชาชน")
    print("   GET  /api/last    - ดึงข้อมูลสแกนล่าสุด")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5051, threaded=True)


def main():
    """Main entry point"""
    # Check for console mode flag
    if '--console' in sys.argv or '--no-gui' in sys.argv:
        run_console_mode()
    elif TKINTER_AVAILABLE:
        app_gui = ThaiIDReaderApp()
        app_gui.run()
    else:
        run_console_mode()


if __name__ == '__main__':
    main()
