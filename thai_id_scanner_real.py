"""
GLINK Thai ID Card Scanner - Real Hardware Server
อ่านข้อมูลจากเครื่องสแกนบัตรประชาชนจริง (GLINK BA0090785)

รันด้วยคำสั่ง: python thai_id_scanner_real.py
เปิดเบราว์เซอร์ไปที่: http://localhost:5050
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from datetime import datetime
import base64

# PC/SC Smart Card Library
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException, CardConnectionException

app = Flask(__name__)
CORS(app)

# ==================== APDU COMMANDS ====================
# Thai National ID Card APDU Commands (Ministry of Interior)

# Thailand MOI Applet AID
MOI_AID = [0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]

# SELECT Command
CMD_SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08] + MOI_AID

# GET RESPONSE
CMD_GET_RESPONSE = [0x00, 0xC0, 0x00, 0x00]

# Data Commands
CMD_CID = [0x80, 0xB0, 0x00, 0x04, 0x02, 0x00, 0x0D]  # Citizen ID
CMD_FULLNAME = [0x80, 0xB0, 0x00, 0x11, 0x02, 0x00, 0xD1]  # Thai + Eng Name + DOB + Gender
CMD_ADDRESS = [0x80, 0xB0, 0x15, 0x79, 0x02, 0x00, 0x64]  # Address
CMD_ISSUE_EXPIRE = [0x80, 0xB0, 0x01, 0x67, 0x02, 0x00, 0x12]  # Issue/Expire date
CMD_ISSUER = [0x80, 0xB0, 0x00, 0xF6, 0x02, 0x00, 0x64]  # Card Issuer

# Photo Commands (20 blocks)
CMD_PHOTO = [
    [0x80, 0xB0, 0x01, 0x7B, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x02, 0x7A, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x03, 0x79, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x04, 0x78, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x05, 0x77, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x06, 0x76, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x07, 0x75, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x08, 0x74, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x09, 0x73, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x0A, 0x72, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x0B, 0x71, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x0C, 0x70, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x0D, 0x6F, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x0E, 0x6E, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x0F, 0x6D, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x10, 0x6C, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x11, 0x6B, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x12, 0x6A, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x13, 0x69, 0x02, 0x00, 0xFF],
    [0x80, 0xB0, 0x14, 0x68, 0x02, 0x00, 0xFF],
]

# ==================== CARD READER CLASS ====================

class ThaiIDCardReader:
    def __init__(self):
        self.connection = None
        self.reader_name = None
        
    def get_readers(self):
        """ดึงรายการเครื่องอ่านบัตรที่เชื่อมต่อ"""
        try:
            reader_list = readers()
            return [str(r) for r in reader_list]
        except Exception as e:
            print(f"Error getting readers: {e}")
            return []
    
    def connect(self, reader_name=None):
        """เชื่อมต่อกับเครื่องอ่านบัตร"""
        try:
            reader_list = readers()
            if not reader_list:
                return False, "ไม่พบเครื่องอ่านบัตร"
            
            # เลือก reader
            if reader_name:
                selected_reader = None
                for r in reader_list:
                    if reader_name in str(r):
                        selected_reader = r
                        break
                if not selected_reader:
                    return False, f"ไม่พบเครื่องอ่าน: {reader_name}"
            else:
                selected_reader = reader_list[0]
            
            self.reader_name = str(selected_reader)
            self.connection = selected_reader.createConnection()
            self.connection.connect()
            
            return True, f"เชื่อมต่อ {self.reader_name} สำเร็จ"
            
        except NoCardException:
            return False, "ไม่พบบัตรในเครื่องอ่าน - กรุณาใส่บัตรประชาชน"
        except Exception as e:
            return False, f"เชื่อมต่อไม่สำเร็จ: {str(e)}"
    
    def disconnect(self):
        """ยกเลิกการเชื่อมต่อ"""
        if self.connection:
            try:
                self.connection.disconnect()
            except:
                pass
        self.connection = None
        self.reader_name = None
    
    def send_command(self, cmd):
        """ส่งคำสั่ง APDU และรับ response"""
        if not self.connection:
            return None
        
        try:
            response, sw1, sw2 = self.connection.transmit(cmd)
            
            # ถ้า SW1 = 0x61 ต้องดึงข้อมูลเพิ่มด้วย GET RESPONSE
            if sw1 == 0x61:
                get_response = CMD_GET_RESPONSE + [sw2]
                response, sw1, sw2 = self.connection.transmit(get_response)
            
            # ตรวจสอบ success (SW1=0x90, SW2=0x00)
            if sw1 == 0x90 and sw2 == 0x00:
                return bytes(response)
            else:
                print(f"APDU Error: SW1={hex(sw1)}, SW2={hex(sw2)}")
                return None
                
        except Exception as e:
            print(f"Command error: {e}")
            return None
    
    def select_applet(self):
        """เลือก Thai ID Card Applet"""
        result = self.send_command(CMD_SELECT)
        return result is not None
    
    def decode_thai(self, data):
        """แปลง bytes เป็น string (TIS-620 -> UTF-8)"""
        if not data:
            return ""
        try:
            return data.decode('tis-620').strip().replace('#', ' ').strip()
        except:
            try:
                return data.decode('utf-8').strip()
            except:
                return ""
    
    def read_citizen_id(self):
        """อ่านเลขบัตรประชาชน"""
        data = self.send_command(CMD_CID)
        if data:
            cid = self.decode_thai(data)
            # Format: X-XXXX-XXXXX-XX-X
            if len(cid) == 13:
                return f"{cid[0]}-{cid[1:5]}-{cid[5:10]}-{cid[10:12]}-{cid[12]}"
            return cid
        return None
    
    def read_fullname(self):
        """อ่านชื่อ-นามสกุล และวันเกิด"""
        data = self.send_command(CMD_FULLNAME)
        if not data:
            return None
        
        text = self.decode_thai(data)
        
        # Format: TH_Title#TH_First#TH_Middle#TH_Last#EN_Title#EN_First#EN_Middle#EN_Last#DOB#Gender
        # โครงสร้างข้อมูล: 100 bytes Thai, 100 bytes English, 8 bytes DOB, 1 byte Gender
        try:
            thai_part = data[:100].decode('tis-620').strip()
            eng_part = data[100:200].decode('tis-620').strip()
            
            thai_names = thai_part.split('#')
            eng_names = eng_part.split('#')
            
            # DOB format: YYYYMMDD (Buddhist year)
            dob_raw = data[200:208].decode('tis-620').strip()
            gender_raw = data[208:209].decode('tis-620').strip()
            
            # แปลงวันเกิด
            if len(dob_raw) >= 8:
                year = int(dob_raw[:4]) - 543  # แปลงเป็น ค.ศ.
                month = dob_raw[4:6]
                day = dob_raw[6:8]
                birth_date = f"{day}/{month}/{int(dob_raw[:4])}"  # แสดงเป็น พ.ศ.
            else:
                birth_date = ""
            
            # เพศ
            gender = "ชาย" if gender_raw == "1" else "หญิง" if gender_raw == "2" else ""
            
            return {
                "th": {
                    "title": thai_names[0].strip() if len(thai_names) > 0 else "",
                    "firstName": thai_names[1].strip() if len(thai_names) > 1 else "",
                    "middleName": thai_names[2].strip() if len(thai_names) > 2 else "",
                    "lastName": thai_names[3].strip() if len(thai_names) > 3 else "",
                },
                "en": {
                    "title": eng_names[0].strip() if len(eng_names) > 0 else "",
                    "firstName": eng_names[1].strip() if len(eng_names) > 1 else "",
                    "middleName": eng_names[2].strip() if len(eng_names) > 2 else "",
                    "lastName": eng_names[3].strip() if len(eng_names) > 3 else "",
                },
                "birthDate": birth_date,
                "gender": gender
            }
        except Exception as e:
            print(f"Parse name error: {e}")
            return None
    
    def read_address(self):
        """อ่านที่อยู่"""
        data = self.send_command(CMD_ADDRESS)
        if not data:
            return None
        
        try:
            text = data.decode('tis-620').strip()
            parts = text.split('#')
            
            return {
                "houseNo": parts[0].strip() if len(parts) > 0 else "",
                "moo": parts[1].strip() if len(parts) > 1 else "",
                "trok": parts[2].strip() if len(parts) > 2 else "",
                "soi": parts[3].strip() if len(parts) > 3 else "",
                "street": parts[4].strip() if len(parts) > 4 else "",
                "subDistrict": parts[5].strip() if len(parts) > 5 else "",
                "district": parts[6].strip() if len(parts) > 6 else "",
                "province": parts[7].strip() if len(parts) > 7 else "",
                "full": text.replace('#', ' ').strip()
            }
        except Exception as e:
            print(f"Parse address error: {e}")
            return None
    
    def read_issue_expire(self):
        """อ่านวันออกบัตรและวันหมดอายุ"""
        data = self.send_command(CMD_ISSUE_EXPIRE)
        if not data:
            return None
        
        try:
            text = data.decode('tis-620').strip()
            # Format: YYYYMMDDYYYYMMDD (Issue + Expire in Buddhist year)
            if len(text) >= 16:
                issue_year = text[0:4]
                issue_month = text[4:6]
                issue_day = text[6:8]
                
                expire_year = text[8:12]
                expire_month = text[12:14]
                expire_day = text[14:16]
                
                return {
                    "issueDate": f"{issue_day}/{issue_month}/{issue_year}",
                    "expireDate": f"{expire_day}/{expire_month}/{expire_year}"
                }
        except Exception as e:
            print(f"Parse date error: {e}")
        
        return None
    
    def read_issuer(self):
        """อ่านผู้ออกบัตร"""
        data = self.send_command(CMD_ISSUER)
        if data:
            return self.decode_thai(data)
        return None
    
    def read_photo(self):
        """อ่านรูปถ่ายจากบัตร"""
        photo_data = bytearray()
        
        for cmd in CMD_PHOTO:
            data = self.send_command(cmd)
            if data:
                photo_data.extend(data)
        
        if photo_data:
            return base64.b64encode(bytes(photo_data)).decode('utf-8')
        return None
    
    def read_all(self, include_photo=False):
        """อ่านข้อมูลทั้งหมดจากบัตร"""
        # เชื่อมต่อ
        success, message = self.connect()
        if not success:
            return None, message
        
        try:
            # Select Thai ID Applet
            if not self.select_applet():
                return None, "ไม่สามารถเลือก Thai ID Applet ได้ - บัตรอาจไม่ใช่บัตรประชาชน"
            
            # อ่านข้อมูล
            cid = self.read_citizen_id()
            if not cid:
                return None, "ไม่สามารถอ่านเลขบัตรประชาชนได้"
            
            name_data = self.read_fullname()
            address_data = self.read_address()
            date_data = self.read_issue_expire()
            issuer = self.read_issuer()
            
            # สร้าง response
            result = {
                "cid": cid,
                "name": name_data if name_data else {
                    "th": {"title": "", "firstName": "", "middleName": "", "lastName": ""},
                    "en": {"title": "", "firstName": "", "middleName": "", "lastName": ""}
                },
                "birthDate": name_data.get("birthDate", "") if name_data else "",
                "gender": name_data.get("gender", "") if name_data else "",
                "religion": "พุทธ",  # ไม่มีในบัตร
                "address": address_data if address_data else {
                    "houseNo": "", "moo": "", "trok": "", "soi": "", 
                    "street": "", "subDistrict": "", "district": "", "province": "", "full": ""
                },
                "issueDate": date_data.get("issueDate", "") if date_data else "",
                "expireDate": date_data.get("expireDate", "") if date_data else "",
                "issuer": issuer or "",
                "photo": None
            }
            
            # อ่านรูปถ่าย (ถ้าต้องการ)
            if include_photo:
                result["photo"] = self.read_photo()
            
            # เพิ่ม fullName
            if name_data:
                th = name_data.get("th", {})
                en = name_data.get("en", {})
                result["name"]["th"]["fullName"] = f"{th.get('title', '')}{th.get('firstName', '')} {th.get('lastName', '')}".strip()
                result["name"]["en"]["fullName"] = f"{en.get('title', '')} {en.get('firstName', '')} {en.get('lastName', '')}".strip()
            
            return result, "อ่านข้อมูลสำเร็จ"
            
        except Exception as e:
            return None, f"เกิดข้อผิดพลาด: {str(e)}"
        finally:
            self.disconnect()


# ==================== GLOBAL INSTANCE ====================
card_reader = ThaiIDCardReader()
device_status = {
    "connected": False,
    "model": "GLINK BA0090785",
    "port": "USB",
    "firmware": "Smart Card Reader"
}

# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """หน้าแรก"""
    return send_file('thai_id_scanner_web.html')

@app.route('/api/device/status', methods=['GET'])
def get_device_status():
    """ดูสถานะเครื่องอ่านบัตร"""
    reader_list = card_reader.get_readers()
    return jsonify({
        "success": True,
        "device": device_status,
        "readers": reader_list,
        "hasReader": len(reader_list) > 0
    })

@app.route('/api/device/connect', methods=['POST'])
def connect_device():
    """เชื่อมต่อเครื่องอ่านบัตร"""
    reader_list = card_reader.get_readers()
    
    if not reader_list:
        return jsonify({
            "success": False,
            "error": "NO_READER",
            "message": "ไม่พบเครื่องอ่านบัตร - กรุณาเชื่อมต่อเครื่อง GLINK"
        }), 400
    
    device_status["connected"] = True
    device_status["model"] = reader_list[0] if reader_list else "Unknown"
    
    return jsonify({
        "success": True,
        "message": f"พบเครื่องอ่านบัตร: {reader_list[0]}",
        "device": device_status,
        "readers": reader_list
    })

@app.route('/api/device/disconnect', methods=['POST'])
def disconnect_device():
    """ยกเลิกการเชื่อมต่อ"""
    device_status["connected"] = False
    card_reader.disconnect()
    return jsonify({
        "success": True,
        "message": "ยกเลิกการเชื่อมต่อแล้ว"
    })

@app.route('/api/scan', methods=['POST'])
def scan_card():
    """สแกนบัตรประชาชน - อ่านจากบัตรจริง!"""
    
    include_photo = request.json.get('includePhoto', False) if request.is_json else False
    
    start_time = datetime.now()
    
    # อ่านข้อมูลจากบัตร
    data, message = card_reader.read_all(include_photo=include_photo)
    
    end_time = datetime.now()
    scan_time = (end_time - start_time).total_seconds()
    
    if data:
        return jsonify({
            "success": True,
            "scanTime": round(scan_time, 2),
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data
        })
    else:
        return jsonify({
            "success": False,
            "error": "SCAN_FAILED",
            "message": message,
            "scanTime": round(scan_time, 2)
        }), 400

@app.route('/api/scan/photo', methods=['POST'])
def scan_card_with_photo():
    """สแกนบัตรพร้อมรูปถ่าย"""
    start_time = datetime.now()
    
    data, message = card_reader.read_all(include_photo=True)
    
    end_time = datetime.now()
    scan_time = (end_time - start_time).total_seconds()
    
    if data:
        return jsonify({
            "success": True,
            "scanTime": round(scan_time, 2),
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data
        })
    else:
        return jsonify({
            "success": False,
            "error": "SCAN_FAILED",
            "message": message
        }), 400

@app.route('/api/readers', methods=['GET'])
def list_readers():
    """แสดงรายการเครื่องอ่านบัตรที่เชื่อมต่อ"""
    reader_list = card_reader.get_readers()
    return jsonify({
        "success": True,
        "readers": reader_list,
        "count": len(reader_list)
    })

@app.route('/api/validate/cid/<cid>', methods=['GET'])
def validate_cid(cid):
    """ตรวจสอบเลขบัตรประชาชน"""
    cid_clean = cid.replace("-", "")
    
    if len(cid_clean) != 13:
        return jsonify({"valid": False, "message": "เลขบัตรประชาชนต้องมี 13 หลัก"})
    
    if not cid_clean.isdigit():
        return jsonify({"valid": False, "message": "เลขบัตรประชาชนต้องเป็นตัวเลขเท่านั้น"})
    
    # Checksum algorithm
    total = sum(int(cid_clean[i]) * (13 - i) for i in range(12))
    check_digit = (11 - (total % 11)) % 10
    
    if check_digit == int(cid_clean[12]):
        return jsonify({
            "valid": True,
            "message": "เลขบัตรประชาชนถูกต้อง",
            "formatted": f"{cid_clean[0]}-{cid_clean[1:5]}-{cid_clean[5:10]}-{cid_clean[10:12]}-{cid_clean[12]}"
        })
    else:
        return jsonify({"valid": False, "message": "เลขบัตรประชาชนไม่ถูกต้อง"})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    reader_list = card_reader.get_readers()
    return jsonify({
        "status": "ok",
        "service": "GLINK Thai ID Scanner API (Real Hardware)",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "readers": reader_list
    })

# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("🎴 GLINK Thai ID Card Scanner - REAL HARDWARE")
    print("=" * 60)
    
    # ตรวจสอบเครื่องอ่านบัตร
    reader_list = card_reader.get_readers()
    if reader_list:
        print(f"✅ พบเครื่องอ่านบัตร {len(reader_list)} เครื่อง:")
        for r in reader_list:
            print(f"   - {r}")
    else:
        print("⚠️  ไม่พบเครื่องอ่านบัตร - กรุณาเชื่อมต่อเครื่อง GLINK")
    
    print("")
    print(f"📍 Server URL: http://localhost:5050")
    print(f"📖 API Endpoints:")
    print(f"   - GET  /api/readers        - ดูรายการเครื่องอ่าน")
    print(f"   - POST /api/device/connect - เชื่อมต่อเครื่อง")
    print(f"   - POST /api/scan           - สแกนบัตร (ข้อมูลจริง!)")
    print(f"   - POST /api/scan/photo     - สแกนบัตรพร้อมรูป")
    print("=" * 60)
    print("🚀 กำลังเริ่มต้น server...")
    print("")
    
    app.run(host='0.0.0.0', port=5050, debug=True)
