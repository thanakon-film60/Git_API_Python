import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """
    สร้างการเชื่อมต่อกับ PostgreSQL database
    รองรับการเชื่อมต่อทั้ง domain name และ local IP
    """
    try:
        # ลองเชื่อมต่อด้วย domain name ก่อน
        db_host = os.getenv("DB_HOST", "n8n.bjhbangkok.com")
        
        connection = psycopg2.connect(
            host=db_host,
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "Bjh12345!!"),
            database=os.getenv("DB_NAME", "postgres")
        )
        print(f"เชื่อมต่อ PostgreSQL สำเร็จ (Host: {db_host})")
        return connection
    except Error as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ PostgreSQL: {e}")
        # ลองเชื่อมต่อด้วย Local IP
        try:
            print("กำลังลองเชื่อมต่อด้วย Local IP...")
            connection = psycopg2.connect(
                host="192.168.1.19",
                port="5432",
                user="postgres",
                password="Bjh12345!!",
                database="postgres"
            )
            print("เชื่อมต่อ PostgreSQL สำเร็จ (Host: 192.168.1.19)")
            return connection
        except Error as e2:
            print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ PostgreSQL (Local IP): {e2}")
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
