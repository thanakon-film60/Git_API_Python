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

    def read_call_matrix(self, date=None, use_latest=True):
        """อ่านข้อมูล Call Matrix จาก Google Sheets

        Args:
            date: วันที่ในรูปแบบ YYYY-MM-DD (ถ้าไม่ระบุและ use_latest=False จะใช้วันนี้)
            use_latest: ถ้าเป็น True จะใช้วันที่ล่าสุดที่มีข้อมูล (default: True)

        Returns:
            dict: ข้อมูล call matrix
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
            
            # ถ้าไม่ระบุวันที่ ให้ดึงวันที่ล่าสุดจาก sheet metadata หรือใช้วันนี้
            if date is None:
                bangkok_tz = pytz.timezone('Asia/Bangkok')
                if use_latest:
                    # ลองดึงวันที่จาก sheet metadata (last updated)
                    try:
                        # ดึงข้อมูล metadata
                        sheet_metadata = worksheet.spreadsheet.fetch_sheet_metadata()
                        last_update = None
                        
                        # หา sheet ที่ตรงกัน
                        for sheet_info in sheet_metadata.get('sheets', []):
                            properties = sheet_info.get('properties', {})
                            if properties.get('title') == worksheet.title:
                                # ใช้วันที่ปัจจุบันเนื่องจาก Google Sheets ไม่มี last modified per sheet
                                last_update = datetime.now(bangkok_tz)
                                break
                        
                        if last_update:
                            date = last_update.strftime('%Y-%m-%d')
                        else:
                            date = datetime.now(bangkok_tz).strftime('%Y-%m-%d')
                    except:
                        date = datetime.now(bangkok_tz).strftime('%Y-%m-%d')
                else:
                    date = datetime.now(bangkok_tz).strftime('%Y-%m-%d')

            # อ่านข้อมูลทั้งหมด
            all_values = worksheet.get_all_values()

            if len(all_values) < 2:
                return {"error": "No data found"}

            # แปลงข้อมูลเป็น format ที่ใช้งานง่าย
            headers = all_values[0]  # ['Agent', '9-10', '10-11', ...]
            time_slots = headers[1:-1]  # เอาเฉพาะช่วงเวลา (ไม่เอา Agent และ รวม)

            matrix_data = {}
            totals_by_agent = {}
            totals_by_slot = {slot: 0 for slot in time_slots}

            for row in all_values[1:]:  # ข้ามแถวหัวตาราง
                if not row or len(row) < 2:
                    continue

                agent_id = row[0]
                if not agent_id or agent_id == 'รวม':
                    continue

                matrix_data[agent_id] = {}
                agent_total = 0

                for i, slot in enumerate(time_slots, start=1):
                    try:
                        value = int(row[i]) if row[i] else 0
                    except (ValueError, IndexError):
                        value = 0

                    matrix_data[agent_id][slot] = value
                    agent_total += value
                    totals_by_slot[slot] += value

                totals_by_agent[agent_id] = agent_total

            # ดึงวันที่อัปเดตล่าสุดของ sheet
            bangkok_tz = pytz.timezone('Asia/Bangkok')
            last_updated = datetime.now(bangkok_tz).strftime('%Y-%m-%d %H:%M:%S')

            return {
                "success": True,
                "date": date,
                "last_updated": last_updated,
                "time_slots": time_slots,
                "matrix_data": matrix_data,
                "totals_by_agent": totals_by_agent,
                "totals_by_slot": totals_by_slot,
                "grand_total": sum(totals_by_agent.values()),
                "sheet_name": worksheet.title
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
