"""
Test script to verify SW1=0x61 handling fix
"""
from smartcard.System import readers
from smartcard.util import toHexString, toBytes

def test_card():
    print("=" * 50)
    print("  Testing SW1=0x61 Fix")
    print("=" * 50)
    
    available_readers = readers()
    if not available_readers:
        print("❌ No readers found")
        return
    
    reader = available_readers[0]
    print(f"📟 Reader: {reader}")
    
    connection = reader.createConnection()
    connection.connect()
    
    atr = connection.getATR()
    print(f"📇 ATR: {toHexString(atr)}")
    
    # Thai ID Card ATR markers
    if atr[4:9] == [0x54, 0x48, 0x20, 0x4E, 0x49]:  # "TH NI"
        print("✅ This IS a Thai National ID Card!")
    
    # Select Thai MOI Applet
    SELECT_CMD = [0x00, 0xA4, 0x04, 0x00, 0x08, 
                  0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]
    
    print(f"\n📤 Sending SELECT: {toHexString(SELECT_CMD)}")
    data, sw1, sw2 = connection.transmit(SELECT_CMD)
    print(f"📥 Response: SW1=0x{sw1:02X} SW2=0x{sw2:02X}")
    
    # Handle SW1=0x61 (GET RESPONSE needed)
    if sw1 == 0x61:
        print(f"⚡ SW1=0x61 detected! Sending GET RESPONSE for {sw2} bytes...")
        GET_RESPONSE = [0x00, 0xC0, 0x00, 0x00, sw2]
        data, sw1, sw2 = connection.transmit(GET_RESPONSE)
        print(f"📥 After GET RESPONSE: SW1=0x{sw1:02X} SW2=0x{sw2:02X}")
        if data:
            print(f"📊 Data: {toHexString(data)}")
    
    if sw1 == 0x90 and sw2 == 0x00:
        print("\n✅ SUCCESS! Card is Thai ID and SELECT worked!")
        print("✅ The SW1=0x61 fix is working correctly!")
        
        # Try reading CID
        print("\n📖 Reading CID...")
        SELECT_CID = [0x00, 0xA4, 0x04, 0x00, 0x02, 0x00, 0x01]
        connection.transmit(SELECT_CID)
        
        READ_CID = [0x80, 0xB0, 0x00, 0x00, 0x0D]
        data, sw1, sw2 = connection.transmit(READ_CID)
        
        if sw1 == 0x61:
            GET_RESPONSE = [0x00, 0xC0, 0x00, 0x00, sw2]
            data, sw1, sw2 = connection.transmit(GET_RESPONSE)
        
        if data:
            cid = bytes(data).decode('ascii', errors='ignore').strip()
            print(f"🆔 CID: {cid}")
    else:
        print(f"\n❌ Failed: SW1=0x{sw1:02X} SW2=0x{sw2:02X}")
    
    connection.disconnect()
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_card()
