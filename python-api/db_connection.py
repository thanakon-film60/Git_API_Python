import psycopg2
from psycopg2 import Error

def get_db_connection():
    """
    สร้างการเชื่อมต่อกับ PostgreSQL database
    """
    try:
        connection = psycopg2.connect(
            host="192.168.1.19",
            port="5432",
            user="postgres",
            password="Bjh12345!!",
            database="postgres"  # เปลี่ยนชื่อ database ตามที่ต้องการ
        )
        print("เชื่อมต่อ PostgreSQL สำเร็จ")
        return connection
    except Error as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ PostgreSQL: {e}")
        return None

def test_connection():
    """
    ทดสอบการเชื่อมต่อและดึงข้อมูลเวอร์ชัน PostgreSQL
    """
    connection = get_db_connection()
    
    if connection:
        try:
            cursor = connection.cursor()
            # ดึงเวอร์ชัน PostgreSQL
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            print(f"PostgreSQL version: {db_version[0]}")
            
            cursor.close()
        except Error as e:
            print(f"เกิดข้อผิดพลาด: {e}")
        finally:
            if connection:
                connection.close()
                print("ปิดการเชื่อมต่อ PostgreSQL")

if __name__ == "__main__":
    test_connection()
