from datetime import datetime
import pytz

class CallMatrixService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service

    def get_current_time_slot(self):
        """คำนวณช่วงเวลาปัจจุบัน

        Returns:
            str: ช่วงเวลา เช่น '9-10', '10-11'
        """
        bangkok_tz = pytz.timezone('Asia/Bangkok')
        now = datetime.now(bangkok_tz)
        hour = now.hour

        # ถ้าไม่ใช่เวลาทำงาน (9-20) return None
        if hour < 9 or hour >= 20:
            return None

        return f"{hour}-{hour + 1}"

    def log_call(self, agent_id, call_type='outgoing', time_slot=None):
        """บันทึกการโทร

        Args:
            agent_id: รหัส agent
            call_type: ประเภทการโทร ('outgoing', 'incoming', 'missed')
            time_slot: ช่วงเวลา (ถ้าไม่ระบุจะใช้ช่วงเวลาปัจจุบัน)

        Returns:
            dict: ผลลัพธ์การบันทึก
        """
        if time_slot is None:
            time_slot = self.get_current_time_slot()

        if time_slot is None:
            return {
                "success": False,
                "error": "Not in working hours (9:00-20:00)"
            }

        # บันทึกลง Google Sheets
        result = self.sheets.update_call_count(agent_id, time_slot, increment=1)

        return result

    def get_call_matrix(self, date=None, use_latest=True):
        """ดึงข้อมูล Call Matrix

        Args:
            date: วันที่ (YYYY-MM-DD) - ถ้าไม่ระบุจะใช้วันที่ล่าสุด
            use_latest: ใช้วันที่ล่าสุดหรือไม่ (default: True)

        Returns:
            dict: ข้อมูล call matrix
        """
        return self.sheets.read_call_matrix(date, use_latest)

    def get_agent_summary(self, agent_id, date=None):
        """ดึงสรุปการโทรของ agent คนหนึ่ง

        Args:
            agent_id: รหัส agent
            date: วันที่

        Returns:
            dict: สรุปการโทร
        """
        matrix = self.sheets.read_call_matrix(date)

        if not matrix.get('success'):
            return matrix

        agent_data = matrix.get('matrix_data', {}).get(agent_id)
        if not agent_data:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found"
            }

        return {
            "success": True,
            "agent_id": agent_id,
            "date": matrix.get('date'),
            "calls_by_slot": agent_data,
            "total_calls": matrix.get('totals_by_agent', {}).get(agent_id, 0)
        }

    def get_time_slot_summary(self, time_slot, date=None):
        """ดึงสรุปการโทรในช่วงเวลาหนึ่ง

        Args:
            time_slot: ช่วงเวลา (เช่น '9-10')
            date: วันที่

        Returns:
            dict: สรุปการโทร
        """
        matrix = self.sheets.read_call_matrix(date)

        if not matrix.get('success'):
            return matrix

        slot_data = {}
        for agent_id, calls in matrix.get('matrix_data', {}).items():
            slot_data[agent_id] = calls.get(time_slot, 0)

        return {
            "success": True,
            "time_slot": time_slot,
            "date": matrix.get('date'),
            "calls_by_agent": slot_data,
            "total_calls": matrix.get('totals_by_slot', {}).get(time_slot, 0)
        }
