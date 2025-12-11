"""ทดสอบอ่านบัตร"""
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException

r = readers()
print("=" * 50)
print("Reader:", r[0] if r else "No reader found")
print("=" * 50)

if not r:
    print("ERROR: No reader!")
    exit()

try:
    conn = r[0].createConnection()
    conn.connect()
    atr = conn.getATR()
    print("ATR:", toHexString(atr))
    print()
    
    # Thai MOI AID
    SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08, 0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]
    response, sw1, sw2 = conn.transmit(SELECT)
    print(f"SELECT MOI AID: SW1={hex(sw1)} SW2={hex(sw2)}")
    
    if sw1 == 0x90 and sw2 == 0x00:
        print("✅ SUCCESS! นี่คือบัตรประชาชนไทย")
        
        # ลองอ่าน CID
        GET_CID = [0x80, 0xB0, 0x00, 0x04, 0x02, 0x00, 0x0D]
        response, sw1, sw2 = conn.transmit(GET_CID)
        if sw1 == 0x90:
            cid = bytes(response).decode('ascii').strip()
            print(f"✅ CID: {cid}")
    elif sw1 == 0x6A:
        print("❌ FAILED: ไม่พบ Thai ID Applet")
        print("   บัตรนี้อาจไม่ใช่บัตรประชาชนไทย")
    else:
        print(f"❓ Unknown response: {hex(sw1)} {hex(sw2)}")
        
    conn.disconnect()
    
except NoCardException:
    print("❌ ERROR: ไม่พบบัตร! กรุณาใส่บัตรประชาชน")
except CardConnectionException as e:
    print(f"❌ ERROR: ไม่สามารถเชื่อมต่อบัตรได้: {e}")
except Exception as e:
    print(f"❌ ERROR: {e}")

input("\nกด Enter เพื่อปิด...")
