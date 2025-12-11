"""
GLINK Thai ID Card Scanner - Simulation Server
จำลองการทำงานของเครื่องอ่านบัตรประชาชน GLINK

รันด้วยคำสั่ง: python thai_id_scanner_server.py
เปิดเบราว์เซอร์ไปที่: http://localhost:5050
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import random
import time
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ข้อมูลตัวอย่างจำลองบัตรประชาชน
SAMPLE_CITIZENS = [
    {
        "cid": "1-1001-12345-67-8",
        "titleTh": "นาย",
        "firstNameTh": "สมชาย",
        "middleNameTh": "",
        "lastNameTh": "ใจดี",
        "titleEn": "Mr.",
        "firstNameEn": "SOMCHAI",
        "middleNameEn": "",
        "lastNameEn": "JAIDEE",
        "birthDate": "15/03/2528",
        "gender": "ชาย",
        "religion": "พุทธ",
        "address": "123/45 หมู่ 6",
        "moo": "6",
        "trok": "",
        "soi": "สุขุมวิท 71",
        "street": "สุขุมวิท",
        "subDistrict": "บางนา",
        "district": "บางนา", 
        "province": "กรุงเทพมหานคร",
        "postalCode": "10260",
        "issueDate": "20/05/2563",
        "expireDate": "14/03/2571",
        "issuer": "เขตบางนา/กรุงเทพมหานคร"
    },
    {
        "cid": "3-4502-00987-65-4",
        "titleTh": "นางสาว",
        "firstNameTh": "สมหญิง",
        "middleNameTh": "",
        "lastNameTh": "รักไทย",
        "titleEn": "Miss",
        "firstNameEn": "SOMYING",
        "middleNameEn": "",
        "lastNameEn": "RAKTHAI",
        "birthDate": "22/08/2535",
        "gender": "หญิง",
        "religion": "พุทธ",
        "address": "789",
        "moo": "",
        "trok": "",
        "soi": "ลาดพร้าว 71",
        "street": "ลาดพร้าว",
        "subDistrict": "ลาดพร้าว",
        "district": "ลาดพร้าว",
        "province": "กรุงเทพมหานคร",
        "postalCode": "10230",
        "issueDate": "10/01/2564",
        "expireDate": "21/08/2572",
        "issuer": "เขตลาดพร้าว/กรุงเทพมหานคร"
    },
    {
        "cid": "5-7301-54321-09-2",
        "titleTh": "นาง",
        "firstNameTh": "วันดี",
        "middleNameTh": "",
        "lastNameTh": "มีสุข",
        "titleEn": "Mrs.",
        "firstNameEn": "WANDEE",
        "middleNameEn": "",
        "lastNameEn": "MEESUK",
        "birthDate": "05/12/2520",
        "gender": "หญิง",
        "religion": "พุทธ",
        "address": "456/7 หมู่ 2",
        "moo": "2",
        "trok": "",
        "soi": "",
        "street": "มิตรภาพ",
        "subDistrict": "หนองจอก",
        "district": "หนองจอก",
        "province": "กรุงเทพมหานคร",
        "postalCode": "10530",
        "issueDate": "15/06/2562",
        "expireDate": "04/12/2569",
        "issuer": "เขตหนองจอก/กรุงเทพมหานคร"
    },
    {
        "cid": "1-5099-00123-45-6",
        "titleTh": "นาย",
        "firstNameTh": "ประสิทธิ์",
        "middleNameTh": "",
        "lastNameTh": "พัฒนา",
        "titleEn": "Mr.",
        "firstNameEn": "PRASIT",
        "middleNameEn": "",
        "lastNameEn": "PATTANA",
        "birthDate": "30/06/2540",
        "gender": "ชาย",
        "religion": "พุทธ",
        "address": "99/9",
        "moo": "1",
        "trok": "",
        "soi": "รามคำแหง 24",
        "street": "รามคำแหง",
        "subDistrict": "หัวหมาก",
        "district": "บางกะปิ",
        "province": "กรุงเทพมหานคร",
        "postalCode": "10240",
        "issueDate": "01/07/2565",
        "expireDate": "29/06/2573",
        "issuer": "เขตบางกะปิ/กรุงเทพมหานคร"
    },
    {
        "cid": "2-1102-00555-77-8",
        "titleTh": "นางสาว",
        "firstNameTh": "พิมพ์ใจ",
        "middleNameTh": "",
        "lastNameTh": "งามเลิศ",
        "titleEn": "Miss",
        "firstNameEn": "PIMJAI",
        "middleNameEn": "",
        "lastNameEn": "NGAMLERT",
        "birthDate": "14/02/2538",
        "gender": "หญิง",
        "religion": "คริสต์",
        "address": "222/33",
        "moo": "",
        "trok": "ทองหล่อ",
        "soi": "สุขุมวิท 55",
        "street": "สุขุมวิท",
        "subDistrict": "คลองตันเหนือ",
        "district": "วัฒนา",
        "province": "กรุงเทพมหานคร",
        "postalCode": "10110",
        "issueDate": "20/02/2566",
        "expireDate": "13/02/2574",
        "issuer": "เขตวัฒนา/กรุงเทพมหานคร"
    }
]

# สถานะเครื่องอ่าน
device_status = {
    "connected": False,
    "model": "GLINK GCSR-01",
    "port": "COM3",
    "firmware": "v2.1.5"
}

# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """หน้าแรก - ส่ง HTML ไฟล์"""
    return send_file('thai_id_scanner_web.html')

@app.route('/api/device/status', methods=['GET'])
def get_device_status():
    """ดูสถานะเครื่องอ่านบัตร"""
    return jsonify({
        "success": True,
        "device": device_status
    })

@app.route('/api/device/connect', methods=['POST'])
def connect_device():
    """เชื่อมต่อเครื่องอ่านบัตร"""
    # จำลองการเชื่อมต่อ (รอ 1 วินาที)
    time.sleep(1)
    device_status["connected"] = True
    return jsonify({
        "success": True,
        "message": "เชื่อมต่อเครื่องอ่านบัตรสำเร็จ",
        "device": device_status
    })

@app.route('/api/device/disconnect', methods=['POST'])
def disconnect_device():
    """ยกเลิกการเชื่อมต่อเครื่องอ่านบัตร"""
    device_status["connected"] = False
    return jsonify({
        "success": True,
        "message": "ยกเลิกการเชื่อมต่อแล้ว"
    })

@app.route('/api/scan', methods=['POST'])
def scan_card():
    """สแกนบัตรประชาชน - API หลัก"""
    
    # ตรวจสอบการเชื่อมต่อ
    if not device_status["connected"]:
        return jsonify({
            "success": False,
            "error": "DEVICE_NOT_CONNECTED",
            "message": "กรุณาเชื่อมต่อเครื่องอ่านบัตรก่อน"
        }), 400
    
    # จำลองการอ่านบัตร (รอ 2-3 วินาที)
    scan_time = random.uniform(1.5, 2.5)
    time.sleep(scan_time)
    
    # สุ่มเลือกข้อมูลตัวอย่าง
    citizen = random.choice(SAMPLE_CITIZENS)
    
    # สร้าง full address
    address_parts = [citizen["address"]]
    if citizen["moo"]:
        address_parts.append(f"หมู่ {citizen['moo']}")
    if citizen["trok"]:
        address_parts.append(f"ตรอก{citizen['trok']}")
    if citizen["soi"]:
        address_parts.append(f"ซอย{citizen['soi']}")
    if citizen["street"]:
        address_parts.append(f"ถนน{citizen['street']}")
    address_parts.append(f"แขวง{citizen['subDistrict']}")
    address_parts.append(f"เขต{citizen['district']}")
    address_parts.append(citizen["province"])
    address_parts.append(citizen["postalCode"])
    
    full_address = " ".join(address_parts)
    
    # Response ในรูปแบบ GLINK API
    response = {
        "success": True,
        "scanTime": round(scan_time, 2),
        "timestamp": datetime.now().isoformat(),
        "data": {
            "cid": citizen["cid"],
            "name": {
                "th": {
                    "title": citizen["titleTh"],
                    "firstName": citizen["firstNameTh"],
                    "middleName": citizen["middleNameTh"],
                    "lastName": citizen["lastNameTh"],
                    "fullName": f"{citizen['titleTh']}{citizen['firstNameTh']} {citizen['lastNameTh']}"
                },
                "en": {
                    "title": citizen["titleEn"],
                    "firstName": citizen["firstNameEn"],
                    "middleName": citizen["middleNameEn"],
                    "lastName": citizen["lastNameEn"],
                    "fullName": f"{citizen['titleEn']} {citizen['firstNameEn']} {citizen['lastNameEn']}"
                }
            },
            "birthDate": citizen["birthDate"],
            "gender": citizen["gender"],
            "religion": citizen["religion"],
            "address": {
                "full": full_address,
                "houseNo": citizen["address"],
                "moo": citizen["moo"],
                "trok": citizen["trok"],
                "soi": citizen["soi"],
                "street": citizen["street"],
                "subDistrict": citizen["subDistrict"],
                "district": citizen["district"],
                "province": citizen["province"],
                "postalCode": citizen["postalCode"]
            },
            "issueDate": citizen["issueDate"],
            "expireDate": citizen["expireDate"],
            "issuer": citizen["issuer"],
            "photo": None  # ในการใช้งานจริงจะเป็น base64 encoded image
        }
    }
    
    return jsonify(response)

@app.route('/api/validate/cid/<cid>', methods=['GET'])
def validate_cid(cid):
    """ตรวจสอบเลขบัตรประชาชน"""
    # ลบขีดออก
    cid_clean = cid.replace("-", "")
    
    # ตรวจสอบความยาว
    if len(cid_clean) != 13:
        return jsonify({
            "valid": False,
            "message": "เลขบัตรประชาชนต้องมี 13 หลัก"
        })
    
    # ตรวจสอบว่าเป็นตัวเลข
    if not cid_clean.isdigit():
        return jsonify({
            "valid": False,
            "message": "เลขบัตรประชาชนต้องเป็นตัวเลขเท่านั้น"
        })
    
    # ตรวจสอบ checksum (algorithm บัตรประชาชนไทย)
    total = 0
    for i in range(12):
        total += int(cid_clean[i]) * (13 - i)
    
    check_digit = (11 - (total % 11)) % 10
    
    if check_digit == int(cid_clean[12]):
        return jsonify({
            "valid": True,
            "message": "เลขบัตรประชาชนถูกต้อง",
            "formatted": f"{cid_clean[0]}-{cid_clean[1:5]}-{cid_clean[5:10]}-{cid_clean[10:12]}-{cid_clean[12]}"
        })
    else:
        return jsonify({
            "valid": False,
            "message": "เลขบัตรประชาชนไม่ถูกต้อง (checksum ไม่ตรง)"
        })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "GLINK Thai ID Scanner API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("🎴 GLINK Thai ID Card Scanner - Simulation Server")
    print("=" * 60)
    print(f"📍 Server URL: http://localhost:5050")
    print(f"📖 API Docs:")
    print(f"   - GET  /api/device/status  - ดูสถานะเครื่อง")
    print(f"   - POST /api/device/connect - เชื่อมต่อเครื่อง")
    print(f"   - POST /api/scan           - สแกนบัตร")
    print(f"   - GET  /api/validate/cid/<cid> - ตรวจสอบเลขบัตร")
    print("=" * 60)
    print("🚀 กำลังเริ่มต้น server...")
    print("")
    
    app.run(host='0.0.0.0', port=5050, debug=True)
