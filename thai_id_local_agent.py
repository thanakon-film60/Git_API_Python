"""
GLINK Thai ID Card - Local Agent
โปรแกรมอ่านบัตรประชาชนที่รันบนเครื่อง Client
แล้วส่งข้อมูลไปยัง Railway Server

วิธีใช้:
1. เสียบเครื่องอ่านบัตร GLINK
2. รัน: python thai_id_local_agent.py
3. เปิดเว็บ Railway แล้วกดสแกน
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import base64
import requests
import os

# PC/SC Smart Card Library
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException, CardConnectionException

app = Flask(__name__)
# อนุญาตให้เรียกจากทุก domain (รวมถึง Railway)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ==================== APDU COMMANDS ====================
MOI_AID = [0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]
CMD_SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08] + MOI_AID
CMD_GET_RESPONSE = [0x00, 0xC0, 0x00, 0x00]
CMD_CID = [0x80, 0xB0, 0x00, 0x04, 0x02, 0x00, 0x0D]
CMD_FULLNAME = [0x80, 0xB0, 0x00, 0x11, 0x02, 0x00, 0xD1]
CMD_ADDRESS = [0x80, 0xB0, 0x15, 0x79, 0x02, 0x00, 0x64]
CMD_ISSUE_EXPIRE = [0x80, 0xB0, 0x01, 0x67, 0x02, 0x00, 0x12]
CMD_ISSUER = [0x80, 0xB0, 0x00, 0xF6, 0x02, 0x00, 0x64]

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
        try:
            reader_list = readers()
            return [str(r) for r in reader_list]
        except Exception as e:
            print(f"Error getting readers: {e}")
            return []
    
    def connect(self, reader_name=None):
        try:
            reader_list = readers()
            if not reader_list:
                return False, "ไม่พบเครื่องอ่านบัตร"
            
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
        if self.connection:
            try:
                self.connection.disconnect()
            except:
                pass
        self.connection = None
        self.reader_name = None
    
    def send_command(self, cmd):
        if not self.connection:
            return None
        
        try:
            response, sw1, sw2 = self.connection.transmit(cmd)
            
            if sw1 == 0x61:
                get_response = CMD_GET_RESPONSE + [sw2]
                response, sw1, sw2 = self.connection.transmit(get_response)
            
            if sw1 == 0x90 and sw2 == 0x00:
                return bytes(response)
            else:
                return None
                
        except Exception as e:
            print(f"Command error: {e}")
            return None
    
    def select_applet(self):
        result = self.send_command(CMD_SELECT)
        return result is not None
    
    def decode_thai(self, data):
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
        data = self.send_command(CMD_CID)
        if data:
            cid = self.decode_thai(data)
            if len(cid) == 13:
                return f"{cid[0]}-{cid[1:5]}-{cid[5:10]}-{cid[10:12]}-{cid[12]}"
            return cid
        return None
    
    def read_fullname(self):
        data = self.send_command(CMD_FULLNAME)
        if not data:
            return None
        
        try:
            thai_part = data[:100].decode('tis-620').strip()
            eng_part = data[100:200].decode('tis-620').strip()
            
            thai_names = thai_part.split('#')
            eng_names = eng_part.split('#')
            
            dob_raw = data[200:208].decode('tis-620').strip()
            gender_raw = data[208:209].decode('tis-620').strip()
            
            if len(dob_raw) >= 8:
                birth_date = f"{dob_raw[6:8]}/{dob_raw[4:6]}/{dob_raw[:4]}"
            else:
                birth_date = ""
            
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
        data = self.send_command(CMD_ISSUE_EXPIRE)
        if not data:
            return None
        
        try:
            text = data.decode('tis-620').strip()
            if len(text) >= 16:
                return {
                    "issueDate": f"{text[6:8]}/{text[4:6]}/{text[0:4]}",
                    "expireDate": f"{text[14:16]}/{text[12:14]}/{text[8:12]}"
                }
        except Exception as e:
            print(f"Parse date error: {e}")
        
        return None
    
    def read_issuer(self):
        data = self.send_command(CMD_ISSUER)
        if data:
            return self.decode_thai(data)
        return None
    
    def read_photo(self):
        photo_data = bytearray()
        
        for cmd in CMD_PHOTO:
            data = self.send_command(cmd)
            if data:
                photo_data.extend(data)
        
        if photo_data:
            return base64.b64encode(bytes(photo_data)).decode('utf-8')
        return None
    
    def read_all(self, include_photo=False):
        success, message = self.connect()
        if not success:
            return None, message
        
        try:
            if not self.select_applet():
                return None, "ไม่สามารถเลือก Thai ID Applet ได้"
            
            cid = self.read_citizen_id()
            if not cid:
                return None, "ไม่สามารถอ่านเลขบัตรประชาชนได้"
            
            name_data = self.read_fullname()
            address_data = self.read_address()
            date_data = self.read_issue_expire()
            issuer = self.read_issuer()
            
            result = {
                "cid": cid,
                "name": name_data if name_data else {
                    "th": {"title": "", "firstName": "", "middleName": "", "lastName": ""},
                    "en": {"title": "", "firstName": "", "middleName": "", "lastName": ""}
                },
                "birthDate": name_data.get("birthDate", "") if name_data else "",
                "gender": name_data.get("gender", "") if name_data else "",
                "religion": "พุทธ",
                "address": address_data if address_data else {
                    "houseNo": "", "moo": "", "trok": "", "soi": "", 
                    "street": "", "subDistrict": "", "district": "", "province": "", "full": ""
                },
                "issueDate": date_data.get("issueDate", "") if date_data else "",
                "expireDate": date_data.get("expireDate", "") if date_data else "",
                "issuer": issuer or "",
                "photo": None
            }
            
            if include_photo:
                result["photo"] = self.read_photo()
            
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

# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    return jsonify({
        "service": "Thai ID Card Local Agent",
        "status": "running",
        "version": "1.0.0",
        "message": "เครื่องอ่านบัตรพร้อมใช้งาน - เรียก /api/scan เพื่ออ่านบัตร"
    })

@app.route('/api/health', methods=['GET'])
def health():
    reader_list = card_reader.get_readers()
    return jsonify({
        "status": "ok",
        "readers": reader_list,
        "hasReader": len(reader_list) > 0
    })

@app.route('/api/readers', methods=['GET'])
def list_readers():
    reader_list = card_reader.get_readers()
    return jsonify({
        "success": True,
        "readers": reader_list,
        "count": len(reader_list)
    })

@app.route('/api/scan', methods=['GET', 'POST', 'OPTIONS'])
def scan_card():
    """สแกนบัตรประชาชน - เรียกจาก Railway ได้"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    include_photo = False
    if request.is_json:
        include_photo = request.json.get('includePhoto', False)
    elif request.args.get('photo'):
        include_photo = request.args.get('photo', '').lower() == 'true'
    
    start_time = datetime.now()
    
    data, message = card_reader.read_all(include_photo=include_photo)
    
    end_time = datetime.now()
    scan_time = (end_time - start_time).total_seconds()
    
    response_data = {
        "success": data is not None,
        "scanTime": round(scan_time, 2),
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "data": data
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    
    if data:
        return response
    else:
        return response, 400

@app.route('/api/scan/photo', methods=['GET', 'POST'])
def scan_with_photo():
    """สแกนบัตรพร้อมรูปถ่าย"""
    start_time = datetime.now()
    
    data, message = card_reader.read_all(include_photo=True)
    
    end_time = datetime.now()
    scan_time = (end_time - start_time).total_seconds()
    
    response = jsonify({
        "success": data is not None,
        "scanTime": round(scan_time, 2),
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "data": data
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    
    if data:
        return response
    else:
        return response, 400


# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("🎴 Thai ID Card - Local Agent")
    print("=" * 60)
    
    reader_list = card_reader.get_readers()
    if reader_list:
        print(f"✅ พบเครื่องอ่านบัตร {len(reader_list)} เครื่อง:")
        for r in reader_list:
            print(f"   - {r}")
    else:
        print("⚠️  ไม่พบเครื่องอ่านบัตร")
    
    print("")
    print("📍 Local Agent URL: http://localhost:5051")
    print("📖 API Endpoints:")
    print("   - GET  /api/health  - ตรวจสอบสถานะ")
    print("   - GET  /api/readers - ดูรายการเครื่องอ่าน")
    print("   - POST /api/scan    - สแกนบัตร")
    print("")
    print("🌐 Railway สามารถเรียก API นี้ได้ผ่าน JavaScript")
    print("=" * 60)
    
    # รันบน port 5051 เพื่อไม่ชนกับ server อื่น
    app.run(host='0.0.0.0', port=5051, debug=True)
