import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

class GoogleSheetsService:
    def __init__(self):
        # ตั้งค่า credentials
        self.credentials = self._get_credentials()
        self.client = gspread.authorize(self.credentials)
        self.spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')

    def _get_credentials(self):
        """สร้าง credentials จาก environment variables"""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        credentials_info = {
            "type": "service_account",
            "project_id": os.getenv('GOOGLE_PROJECT_ID'),
            "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL'),
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_CERT_URL')
        }

        return Credentials.from_service_account_info(credentials_info, scopes=scopes)

    def get_spreadsheet(self):
        """เปิด spreadsheet"""
        return self.client.open_by_key(self.spreadsheet_id)

    def get_worksheet(self, sheet_name):
        """เปิด worksheet ตามชื่อ"""
        spreadsheet = self.get_spreadsheet()
        return spreadsheet.worksheet(sheet_name)

    def get_worksheet_with_fallback(self, sheet_names):
        """เปิด worksheet โดยลองหลายชื่อ (fallback)
        
        Args:
            sheet_names: list ของชื่อ sheet ที่เป็นไปได้
            
        Returns:
            worksheet object หรือ None ถ้าไม่พบ
        """
        spreadsheet = self.get_spreadsheet()
        
        for sheet_name in sheet_names:
            try:
                return spreadsheet.worksheet(sheet_name)
            except Exception:
                continue
        
        # ถ้าไม่พบเลย ให้แสดง list ของ sheets ที่มี
        available_sheets = [ws.title for ws in spreadsheet.worksheets()]
        raise ValueError(f"ไม่พบ sheet ที่ต้องการ. ลอง: {sheet_names}. Sheets ที่มี: {available_sheets}")

    def _parse_google_sheets_datetime(self, datetime_str):
        """Parse Google Sheets datetime format (YYYY-MM-DD HH:MM:SS or YYYY-MM-DD H:MM:SS)"""
        try:
            if not datetime_str or datetime_str.strip() == '':
                return None
            
            # Format: "2025-11-18 9:14:57" หรือ "2025-11-18 09:14:57"
            parts = datetime_str.strip().split()
            if len(parts) != 2:
                return None
            
            date_part = parts[0].strip()  # YYYY-MM-DD
            time_part = parts[1].strip()  # H:MM:SS หรือ HH:MM:SS
            
            # Parse date (YYYY-MM-DD)
            date_components = date_part.split('-')
            if len(date_components) != 3:
                return None
            
            year = int(date_components[0])
            month = int(date_components[1])
            day = int(date_components[2])
            
            # Format date
            formatted_date = f"{year:04d}-{month:02d}-{day:02d}"
            
            # Parse time (รองรับทั้ง H:MM:SS และ HH:MM:SS)
            time_components = time_part.split(':')
            hour = int(time_components[0]) if time_components else 0
            
            return {
                'date': formatted_date,
                'time': time_part,
                'hour': hour,
                'datetime': datetime_str
            }
        except Exception as e:
            # Debug: แสดง error ถ้า parse ไม่ได้
            print(f"Failed to parse datetime: {datetime_str}, Error: {e}")
            return None

    def _parse_duration_to_seconds(self, duration_str):
        """Parse duration string (H:MM:SS or MM:SS) to seconds"""
        try:
            if not duration_str or duration_str.strip() == '':
                return 0
            
            parts = duration_str.strip().split(':')
            
            if len(parts) == 3:  # H:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            else:
                return 0
        except:
            return 0

    def read_call_matrix(self, date=None, use_latest=True):
        """อ่านข้อมูล Call Matrix จาก Google Sheets (สรุปจาก Call Log)

        Args:
            date: วันที่ในรูปแบบ YYYY-MM-DD (ถ้าไม่ระบุจะใช้วันนี้)
            use_latest: ถ้าเป็น True จะใช้วันที่ล่าสุดที่มีข้อมูล (default: True)

        Returns:
            dict: ข้อมูล call matrix ในรูปแบบตาราง Agent x Time Slots
        """
        try:
            # เปิด worksheet (Call Log)
            possible_names = [
                'สรุป call_AI',
                'สรุป call_AI_summary',
                'call_AI_summary'
            ]
            worksheet = self.get_worksheet_with_fallback(possible_names)
            
            # ตั้งค่าวันที่
            bangkok_tz = pytz.timezone('Asia/Bangkok')
            if date is None:
                date = datetime.now(bangkok_tz).strftime('%Y-%m-%d')

            # อ่านข้อมูลทั้งหมด
            all_values = worksheet.get_all_values()

            if len(all_values) < 2:
                return {"success": False, "error": "No data found"}

            # หา headers
            headers = all_values[0]
            
            # หาตำแหน่งคอลัมน์ที่ต้องการ
            try:
                start_col = headers.index('start')
                caller_col = headers.index('ผู้โทร')
                duration_col = headers.index('สรุปเวลา')
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Missing required columns: {str(e)}",
                    "available_columns": headers
                }

            # กำหนดช่วงเวลา 9:00-20:00
            time_slots = ['9-10', '10-11', '11-12', '12-13', '13-14', '14-15', 
                         '15-16', '16-17', '17-18', '18-19', '19-20']
            
            # เป้าหมาย: Agent 101-108
            target_agents = ['101', '102', '103', '104', '105', '106', '107', '108']
            
            # สร้างโครงสร้างข้อมูล
            matrix_data = {agent: {slot: 0 for slot in time_slots} for agent in target_agents}
            totals_by_agent = {agent: 0 for agent in target_agents}
            totals_by_slot = {slot: 0 for slot in time_slots}
            
            # ประมวลผลข้อมูล
            MIN_DURATION_SECONDS = 30
            processed_count = 0
            
            for row in all_values[1:]:  # ข้ามหัวตาราง
                if len(row) <= max(start_col, caller_col, duration_col):
                    continue
                
                # ดึงข้อมูล
                start_datetime = row[start_col].strip()
                caller = row[caller_col].strip()
                duration_str = row[duration_col].strip()
                
                # กรอง Agent
                if caller not in target_agents:
                    continue
                
                # Parse datetime (format: DD/MM/YYYY, HH:MM:SS)
                parsed_datetime = self._parse_google_sheets_datetime(start_datetime)
                if not parsed_datetime:
                    continue
                
                # กรองวันที่
                if parsed_datetime['date'] != date:
                    continue
                
                # กรอง duration
                duration_seconds = self._parse_duration_to_seconds(duration_str)
                if duration_seconds < MIN_DURATION_SECONDS:
                    continue
                
                # หาช่วงเวลา
                hour = parsed_datetime['hour']
                time_slot = None
                
                for slot in time_slots:
                    start_hour = int(slot.split('-')[0])
                    end_hour = int(slot.split('-')[1])
                    if start_hour <= hour < end_hour:
                        time_slot = slot
                        break
                
                if time_slot:
                    matrix_data[caller][time_slot] += 1
                    totals_by_agent[caller] += 1
                    totals_by_slot[time_slot] += 1
                    processed_count += 1
            
            # สร้าง response
            last_updated = datetime.now(bangkok_tz).strftime('%Y-%m-%d %H:%M:%S')
            grand_total = sum(totals_by_agent.values())
            
            return {
                "success": True,
                "date": date,
                "last_updated": last_updated,
                "time_slots": time_slots,
                "matrix_data": matrix_data,
                "grand_total": grand_total,
                "sheet_name": worksheet.title,
                "processed_calls": processed_count,
                "min_duration_seconds": MIN_DURATION_SECONDS,
                "target_agents": target_agents
            }

        except ValueError as e:
            # Error จากการไม่พบ sheet
            return {
                "success": False,
                "error": str(e),
                "error_type": "sheet_not_found"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "unknown"
            }

    def update_call_count(self, agent_id, time_slot, increment=1):
        """อัพเดทจำนวนการโทรในช่วงเวลาที่กำหนด

        Args:
            agent_id: รหัส agent (เช่น '101', '102')
            time_slot: ช่วงเวลา (เช่น '9-10', '10-11')
            increment: จำนวนที่จะเพิ่ม (default=1)

        Returns:
            dict: ผลลัพธ์การอัพเดท
        """
        try:
            # เปิด worksheet (ลองหลายชื่อที่เป็นไปได้)
            possible_names = [
                'สรุป call_AI',
                'สรุป call_AI_summary',
                'call_AI_summary',
                'Call Matrix'
            ]
            worksheet = self.get_worksheet_with_fallback(possible_names)

            # หาตำแหน่งของ agent และ time slot
            all_values = worksheet.get_all_values()
            headers = all_values[0]

            # หาคอลัมน์ของ time_slot
            try:
                col_index = headers.index(time_slot) + 1  # +1 เพราะ gspread นับเริ่ม 1
            except ValueError:
                return {
                    "success": False,
                    "error": f"Time slot '{time_slot}' not found"
                }

            # หาแถวของ agent
            row_index = None
            for i, row in enumerate(all_values[1:], start=2):  # เริ่มนับที่ 2 (ข้ามหัวตาราง)
                if row[0] == agent_id:
                    row_index = i
                    break

            if row_index is None:
                return {
                    "success": False,
                    "error": f"Agent '{agent_id}' not found"
                }

            # อ่านค่าปัจจุบัน
            current_value = worksheet.cell(row_index, col_index).value
            try:
                current_value = int(current_value) if current_value else 0
            except ValueError:
                current_value = 0

            # คำนวณค่าใหม่
            new_value = current_value + increment

            # อัพเดทค่าใหม่
            worksheet.update_cell(row_index, col_index, new_value)

            return {
                "success": True,
                "agent_id": agent_id,
                "time_slot": time_slot,
                "old_value": current_value,
                "new_value": new_value,
                "increment": increment
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def set_call_count(self, agent_id, time_slot, value):
        """ตั้งค่าจำนวนการโทรโดยตรง (ไม่ใช่การเพิ่ม)

        Args:
            agent_id: รหัส agent (เช่น '101', '102')
            time_slot: ช่วงเวลา (เช่น '9-10', '10-11')
            value: ค่าใหม่ที่ต้องการตั้ง

        Returns:
            dict: ผลลัพธ์การอัพเดท
        """
        try:
            # เปิด worksheet (ลองหลายชื่อที่เป็นไปได้)
            possible_names = [
                'สรุป call_AI',
                'สรุป call_AI_summary',
                'call_AI_summary',
                'Call Matrix'
            ]
            worksheet = self.get_worksheet_with_fallback(possible_names)

            # หาตำแหน่งของ agent และ time slot
            all_values = worksheet.get_all_values()
            headers = all_values[0]

            # หาคอลัมน์ของ time_slot
            try:
                col_index = headers.index(time_slot) + 1
            except ValueError:
                return {
                    "success": False,
                    "error": f"Time slot '{time_slot}' not found"
                }

            # หาแถวของ agent
            row_index = None
            for i, row in enumerate(all_values[1:], start=2):
                if row[0] == agent_id:
                    row_index = i
                    break

            if row_index is None:
                return {
                    "success": False,
                    "error": f"Agent '{agent_id}' not found"
                }

            # อ่านค่าปัจจุบัน
            current_value = worksheet.cell(row_index, col_index).value
            try:
                current_value = int(current_value) if current_value else 0
            except ValueError:
                current_value = 0

            # ตั้งค่าใหม่
            worksheet.update_cell(row_index, col_index, value)

            return {
                "success": True,
                "agent_id": agent_id,
                "time_slot": time_slot,
                "old_value": current_value,
                "new_value": value
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def batch_update_call_counts(self, updates):
        """อัพเดทหลายช่องพร้อมกัน

        Args:
            updates: list of dict [{"agent_id": "101", "time_slot": "9-10", "value": 5}, ...]

        Returns:
            dict: ผลลัพธ์การอัพเดท
        """
        try:
            # เปิด worksheet (ลองหลายชื่อที่เป็นไปได้)
            possible_names = [
                'สรุป call_AI',
                'สรุป call_AI_summary',
                'call_AI_summary',
                'Call Matrix'
            ]
            worksheet = self.get_worksheet_with_fallback(possible_names)
            all_values = worksheet.get_all_values()
            headers = all_values[0]

            # เตรียม batch update
            batch_data = []

            for update in updates:
                agent_id = update.get('agent_id')
                time_slot = update.get('time_slot')
                new_value = update.get('value', 0)

                # หาตำแหน่ง
                try:
                    col_index = headers.index(time_slot) + 1
                except ValueError:
                    continue

                row_index = None
                for i, row in enumerate(all_values[1:], start=2):
                    if row[0] == agent_id:
                        row_index = i
                        break

                if row_index is None:
                    continue

                # เพิ่มเข้า batch
                batch_data.append({
                    'range': worksheet.title + '!' + gspread.utils.rowcol_to_a1(row_index, col_index),
                    'values': [[new_value]]
                })

            # อัพเดททั้งหมดพร้อมกัน
            if batch_data:
                worksheet.spreadsheet.values_batch_update(batch_data)

            return {
                "success": True,
                "updated_count": len(batch_data)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
