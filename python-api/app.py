"""
Flask API for accessing Google Sheets data (Film data)
This API serves as a backend for the Performance Surgery Schedule system.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import traceback
from datetime import datetime, timedelta
from functools import wraps
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for production
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# In-memory cache
cache = {
    'data': None,
    'timestamp': None,
    'expires_at': None
}
CACHE_DURATION = int(os.getenv('CACHE_DURATION', 30))  # seconds


def get_google_sheets_client():
    """Initialize Google Sheets client with service account credentials"""
    try:
        # Get credentials from environment variables
        project_id = os.getenv('GOOGLE_PROJECT_ID')
        private_key_id = os.getenv('GOOGLE_PRIVATE_KEY_ID')
        private_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY', '')
        client_email = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL')
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_cert_url = os.getenv('GOOGLE_CLIENT_CERT_URL')

        if not client_email or not private_key:
            raise ValueError("Missing required Google credentials in environment variables")

        # Replace escaped newlines in private key if needed
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')

        # Construct service account credentials
        credentials_dict = {
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": private_key_id,
            "private_key": private_key,
            "client_email": client_email,
            "client_id": client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": client_cert_url
        }

        # Define the required scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]

        # Create credentials
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )

        # Authorize and return client
        client = gspread.authorize(credentials)
        return client

    except Exception as e:
        print(f"Error initializing Google Sheets client: {e}")
        traceback.print_exc()
        raise


def fetch_film_data():
    """Fetch data from Google Sheets 'Film data' sheet"""
    try:
        # Get spreadsheet ID from environment
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID not set in environment variables")

        print(f"📊 Fetching data from Google Sheets: {spreadsheet_id}")

        # Get Google Sheets client
        client = get_google_sheets_client()

        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Get the 'Film data' sheet
        sheet = spreadsheet.worksheet('Film data')

        # Get all values from the sheet
        all_values = sheet.get_all_values()

        if not all_values:
            return []

        # First row is header
        headers = all_values[0]
        data_rows = all_values[1:]

        # Convert to list of dictionaries
        result = []
        for idx, row in enumerate(data_rows, start=2):  # Start from row 2 (1-indexed)
            # Create dictionary with headers as keys
            row_dict = {}
            for col_idx, header in enumerate(headers):
                value = row[col_idx] if col_idx < len(row) else ''
                row_dict[header] = value

            # Add row number as ID
            row_dict['id'] = f'film-{idx}'

            # Add normalized fields for easier access
            row_dict['contact_person'] = row_dict.get('ผู้ติดต่อ', '').strip()
            row_dict['date_surgery_scheduled'] = row_dict.get('วันที่ได้นัดผ่าตัด', '').strip()
            row_dict['date_consult_scheduled'] = row_dict.get('วันที่ได้นัด consult', '').strip()
            row_dict['surgery_date'] = row_dict.get('วันที่ผ่าตัด', '').strip()

            result.append(row_dict)

        print(f"✅ Successfully fetched {len(result)} records from Google Sheets")
        return result

    except gspread.exceptions.WorksheetNotFound:
        print("❌ Worksheet 'Film data' not found")
        raise ValueError("Worksheet 'Film data' not found in spreadsheet")
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Spreadsheet not found")
        raise ValueError("Spreadsheet not found. Check GOOGLE_SPREADSHEET_ID and service account permissions")
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        traceback.print_exc()
        raise


def fetch_call_ai_data():
    """Fetch data from Google Sheets 'สรุป call_AI' sheet"""
    try:
        # Get spreadsheet ID from environment
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID not set in environment variables")

        print(f"📊 Fetching data from สรุป call_AI sheet: {spreadsheet_id}")

        # Get Google Sheets client
        client = get_google_sheets_client()

        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Get the 'สรุป call_AI' sheet
        sheet = spreadsheet.worksheet('สรุป call_AI')

        # Get all values from the sheet
        all_values = sheet.get_all_values()

        if not all_values:
            return []

        # First row is header
        headers = all_values[0]
        data_rows = all_values[1:]

        # Convert to list of dictionaries
        result = []
        for idx, row in enumerate(data_rows, start=2):  # Start from row 2 (1-indexed)
            # Create dictionary with headers as keys
            row_dict = {}
            for col_idx, header in enumerate(headers):
                value = row[col_idx] if col_idx < len(row) else ''
                row_dict[header] = value

            result.append(row_dict)

        print(f"✅ Successfully fetched {len(result)} records from สรุป call_AI sheet")
        return result

    except gspread.exceptions.WorksheetNotFound:
        print("❌ Worksheet 'สรุป call_AI' not found")
        raise ValueError("Worksheet 'สรุป call_AI' not found in spreadsheet")
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Spreadsheet not found")
        raise ValueError("Spreadsheet not found. Check GOOGLE_SPREADSHEET_ID and service account permissions")
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        traceback.print_exc()
        raise


def parse_duration_to_seconds(duration_str):
    """Parse duration string (H:MM:SS or MM:SS) to total seconds"""
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
            
    except (ValueError, AttributeError):
        return 0


def cache_data(func):
    """Decorator to cache data for specified duration"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        global cache
        now = datetime.now()

        # Check if cache is valid
        if (cache['data'] is not None and 
            cache['expires_at'] is not None and 
            now < cache['expires_at']):
            print(f"✅ Returning cached data (expires in {(cache['expires_at'] - now).seconds}s)")
            return cache['data']

        # Fetch new data
        print("📡 Cache expired or empty, fetching fresh data...")
        data = func(*args, **kwargs)

        # Update cache
        cache['data'] = data
        cache['timestamp'] = now
        cache['expires_at'] = now + timedelta(seconds=CACHE_DURATION)

        return data

    return wrapper


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Python API for Performance Surgery Schedule',
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'endpoints': {
            '/health': 'Health check',
            '/film-data': 'Get all raw data from Film data sheet (all columns and rows)',
            '/api/film-data': 'Get surgery schedule data from Google Sheets',
            '/api/google-sheets/film-data': 'Get all raw data from Film data sheet (all columns and rows)',
            '/run-time': 'Get call statistics from สรุป call_AI sheet mapped by time slots (9:00-20:00) for callers 101-108',
            '/api/clear-cache': 'Clear data cache (POST)'
        }
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_status': {
            'has_data': cache['data'] is not None,
            'cached_at': cache['timestamp'].isoformat() if cache['timestamp'] else None,
            'expires_at': cache['expires_at'].isoformat() if cache['expires_at'] else None
        }
    })


@app.route('/api/film-data', methods=['GET'])
@cache_data
def get_film_data():
    """Get surgery schedule data from Google Sheets 'Film data' sheet"""
    try:
        # Fetch data from Google Sheets
        data = fetch_film_data()

        # Return response
        response = {
            'success': True,
            'data': data,
            'total': len(data),
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Sheets (Film data)',
            'cached': cache['data'] is not None,
            'cache_info': {
                'duration': CACHE_DURATION,
                'expires_at': cache['expires_at'].isoformat() if cache['expires_at'] else None
            }
        }

        return jsonify(response)

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 400

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/film-data: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/film-data', methods=['GET'])
@app.route('/api/google-sheets/film-data', methods=['GET'])
def get_google_sheets_all_data():
    """Get all raw data from Google Sheets 'Film data' sheet (all columns and rows)"""
    try:
        # Get spreadsheet ID from environment
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID not set in environment variables")

        print(f"📊 Fetching all raw data from Google Sheets: {spreadsheet_id}")

        # Get Google Sheets client
        client = get_google_sheets_client()

        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Get the 'Film data' sheet
        sheet = spreadsheet.worksheet('Film data')

        # Get all values from the sheet (including headers)
        all_values = sheet.get_all_values()

        if not all_values:
            return jsonify({
                'success': True,
                'data': {
                    'headers': [],
                    'rows': [],
                    'all_data': []
                },
                'total_rows': 0,
                'total_columns': 0,
                'timestamp': datetime.now().isoformat(),
                'source': 'Google Sheets (Film data)'
            })

        # Separate headers and data rows
        headers = all_values[0] if len(all_values) > 0 else []
        data_rows = all_values[1:] if len(all_values) > 1 else []

        # Get sheet metadata
        total_rows = len(all_values)
        total_columns = len(headers) if headers else 0

        print(f"✅ Successfully fetched all data: {total_rows} rows x {total_columns} columns")

        # Return response with all data formats
        response = {
            'success': True,
            'data': {
                'headers': headers,
                'rows': data_rows,
                'all_data': all_values  # Raw data including headers
            },
            'total_rows': total_rows,
            'total_columns': total_columns,
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Sheets (Film data)',
            'sheet_info': {
                'name': 'Film data',
                'spreadsheet_id': spreadsheet_id,
                'has_headers': len(headers) > 0,
                'data_rows_count': len(data_rows)
            }
        }

        return jsonify(response)

    except gspread.exceptions.WorksheetNotFound:
        print("❌ Worksheet 'Film data' not found")
        return jsonify({
            'success': False,
            'error': "Worksheet 'Film data' not found in spreadsheet",
            'data': None,
            'timestamp': datetime.now().isoformat()
        }), 404

    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Spreadsheet not found")
        return jsonify({
            'success': False,
            'error': "Spreadsheet not found. Check GOOGLE_SPREADSHEET_ID and service account permissions",
            'data': None,
            'timestamp': datetime.now().isoformat()
        }), 404

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': None,
            'timestamp': datetime.now().isoformat()
        }), 400

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/google-sheets/film-data: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'data': None,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/run-time', methods=['GET'])
def get_run_time():
    """Get call statistics from 'สรุป call_AI' sheet for callers 101-108 mapped with time slots"""
    try:
        # Get query parameters - ใช้วันที่ปัจจุบันเป็นค่าเริ่มต้น
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Fetch data from สรุป call_AI sheet
        data = fetch_call_ai_data()
        
        # Define target callers (101-108)
        target_callers = ['101', '102', '103', '104', '105', '106', '107', '108']
        
        # Define time slots mapping (ตรงกับ callTableTimeSlots ใน React)
        time_slots = [
            {"label": "9:00-10:00", "start": "9", "hour_start": 9, "hour_end": 10},
            {"label": "10:00-11:00", "start": "10", "hour_start": 10, "hour_end": 11},
            {"label": "11:00-12:00", "start": "11", "hour_start": 11, "hour_end": 12},
            {"label": "12:00-13:00", "start": "12", "hour_start": 12, "hour_end": 13},
            {"label": "13:00-14:00", "start": "13", "hour_start": 13, "hour_end": 14},
            {"label": "14:00-15:00", "start": "14", "hour_start": 14, "hour_end": 15},
            {"label": "15:00-16:00", "start": "15", "hour_start": 15, "hour_end": 16},
            {"label": "16:00-17:00", "start": "16", "hour_start": 16, "hour_end": 17},
            {"label": "17:00-18:00", "start": "17", "hour_start": 17, "hour_end": 18},
            {"label": "18:00-19:00", "start": "18", "hour_start": 18, "hour_end": 19},
            {"label": "19:00-20:00", "start": "19", "hour_start": 19, "hour_end": 20},
        ]
        
        # Initialize result structure: time_slot (start) -> agent -> count
        slot_counts = {}
        for slot in time_slots:
            slot_counts[slot['start']] = {}
            for caller in target_callers:
                slot_counts[slot['start']][caller] = 0
        
        # Initialize totals per agent
        agent_totals = {}
        for caller in target_callers:
            agent_totals[caller] = 0
        
        # Minimum duration threshold: 30 minutes = 1800 seconds
        MIN_DURATION_SECONDS = 1800  # 0:30:00
        
        # Process each row
        for row in data:
            caller = row.get('ผู้โทร', '').strip()
            start_datetime = row.get('start', '').strip()
            duration_str = row.get('สรุปเวลา', '').strip()
            
            # Check if caller is in target range
            if caller not in target_callers:
                continue
            
            # Parse duration
            duration_seconds = parse_duration_to_seconds(duration_str)
            
            # Only count if duration > 30 minutes
            if duration_seconds <= MIN_DURATION_SECONDS:
                continue
            
            # Filter by date if provided
            if date_param and ' ' in start_datetime:
                call_date = start_datetime.split(' ')[0]
                if call_date != date_param:
                    continue
            
            # Extract hour from start datetime
            if ' ' in start_datetime:
                time_part = start_datetime.split(' ')[1] if len(start_datetime.split(' ')) > 1 else ''
                if time_part:
                    try:
                        hour = int(time_part.split(':')[0])
                        
                        # Find matching time slot
                        for slot in time_slots:
                            if slot['hour_start'] <= hour < slot['hour_end']:
                                slot_counts[slot['start']][caller] += 1
                                agent_totals[caller] += 1
                                break
                    except (ValueError, IndexError):
                        continue  # Skip if time parsing fails
        
        # Build response in format expected by React
        # Format: { "9": { "101": 5, "102": 3, ... }, "10": { ... }, totals: { "101": 50, ... } }
        response_data = {
            'success': True,
            'timeSlots': [],
            'slotCounts': slot_counts,  # สำหรับใช้ใน getCallTableValue
            'totals': agent_totals,     # จำนวนรวมต่อ agent
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Sheets (สรุป call_AI)',
            'filter_criteria': {
                'callers': target_callers,
                'min_duration': '0:30:00',
                'min_duration_seconds': MIN_DURATION_SECONDS,
                'time_slots_count': len(time_slots),
                'date': date_param if date_param else 'all'
            }
        }
        
        # Add timeSlots array for detailed view
        for slot in time_slots:
            response_data['timeSlots'].append({
                'label': slot['label'],
                'hourStart': slot['start'],
                'key': slot['start'],
                'agentCounts': slot_counts[slot['start']]
            })
        
        return jsonify(response_data)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /run-time: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear the data cache"""
    global cache
    cache = {
        'data': None,
        'timestamp': None,
        'expires_at': None
    }

    return jsonify({
        'success': True,
        'message': 'Cache cleared successfully',
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/',
            '/health',
            '/film-data',
            '/api/film-data',
            '/api/google-sheets/film-data',
            '/run-time',
            '/api/clear-cache'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error)
    }), 500


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    print(f"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║        🚀 Python API for Performance Surgery Schedule           ║
    ║                                                                  ║
    ║        Running on: http://localhost:{port}                         ║
    ║        Environment: {'Development' if debug else 'Production'}                                    ║
    ║        Cache Duration: {CACHE_DURATION}s                                       ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)
