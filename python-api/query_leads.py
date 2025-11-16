from db_connection import get_db_connection
from psycopg2 import Error
import json

def get_all_leads():
    """
    ดึงข้อมูลทั้งหมดจากตาราง bjh_all_leads
    """
    connection = get_db_connection()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            # Query ข้อมูลจากตาราง
            query = 'SELECT * FROM "BJH-Server"."bjh_all_leads"'
            cursor.execute(query)
            
            # ดึงชื่อ columns
            column_names = [desc[0] for desc in cursor.description]
            
            # ดึงข้อมูลทั้งหมด
            rows = cursor.fetchall()
            
            print(f"พบข้อมูล {len(rows)} แถว")
            print(f"Columns: {column_names}\n")
            
            # แสดงข้อมูล 5 แถวแรก
            results = []
            for i, row in enumerate(rows[:5]):
                row_dict = dict(zip(column_names, row))
                results.append(row_dict)
                print(f"Row {i+1}:")
                print(json.dumps(row_dict, indent=2, default=str))
                print("-" * 50)
            
            cursor.close()
            return rows, column_names
            
        except Error as e:
            print(f"เกิดข้อผิดพลาดในการ query ข้อมูล: {e}")
            return None, None
        finally:
            if connection:
                connection.close()
                print("\nปิดการเชื่อมต่อ PostgreSQL")
    
    return None, None

def get_leads_with_limit(limit=10):
    """
    ดึงข้อมูลจำนวนจำกัดจากตาราง bjh_all_leads
    """
    connection = get_db_connection()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            query = f'SELECT * FROM "BJH-Server"."bjh_all_leads" LIMIT {limit}'
            cursor.execute(query)
            
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            print(f"ดึงข้อมูล {len(rows)} แถว")
            
            results = []
            for row in rows:
                row_dict = dict(zip(column_names, row))
                results.append(row_dict)
            
            cursor.close()
            return results
            
        except Error as e:
            print(f"เกิดข้อผิดพลาด: {e}")
            return None
        finally:
            if connection:
                connection.close()

if __name__ == "__main__":
    print("=== ดึงข้อมูลจาก bjh_all_leads ===\n")
    get_all_leads()
