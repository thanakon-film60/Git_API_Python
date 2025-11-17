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
import requests
import json
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from db_connection import get_db_connection
from psycopg2 import Error

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

        # Debug: Print headers and sample data
        print(f"📋 Headers found in สรุป call_AI sheet: {headers}")
        if data_rows:
            print(f"📝 Sample row (first): {data_rows[0]}")

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


def parse_google_sheets_datetime(datetime_str):
    """
    Parse Google Sheets datetime format to standard format
    Input: '7/11/2025, 11:46:51' (DD/MM/YYYY, HH:MM:SS)
    Output: {'date': '2025-11-07', 'time': '11:46:51', 'hour': 11}
    """
    try:
        if not datetime_str or datetime_str.strip() == '':
            return None
        
        # Split by comma to separate date and time
        parts = datetime_str.strip().split(',')
        if len(parts) != 2:
            return None
        
        date_part = parts[0].strip()  # '7/11/2025'
        time_part = parts[1].strip()  # '11:46:51'
        
        # Parse date (DD/MM/YYYY)
        date_components = date_part.split('/')
        if len(date_components) != 3:
            return None
        
        day = int(date_components[0])
        month = int(date_components[1])
        year = int(date_components[2])
        
        # Convert to YYYY-MM-DD format
        formatted_date = f"{year:04d}-{month:02d}-{day:02d}"
        
        # Parse hour from time
        time_components = time_part.split(':')
        hour = int(time_components[0]) if time_components else 0
        
        return {
            'date': formatted_date,
            'time': time_part,
            'hour': hour,
            'datetime': datetime_str
        }
        
    except (ValueError, AttributeError, IndexError):
        return None


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
            '/N_SaleIncentive_data': 'Get sale incentive data from N_SaleIncentive sheet (supports month/year filtering) (GET)',
            '/api/clear-cache': 'Clear data cache (POST)',
            '/api/facebook-ads-campaigns': 'Get Facebook Ads campaigns data (supports level, date filtering, daily breakdown) (GET)',
            '/api/facebook-ads-manager': 'Alias for /api/facebook-ads-campaigns (GET)',
            '/api/google-sheets-data': 'Get Google Sheets data from เคสได้ชื่อเบอร์ sheet (GET)',
            '/api/google-ads': 'Get Google Ads data (GET)',
            '/data_bjh': 'Get all leads data from BJH PostgreSQL database (GET)'
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
        
        # Minimum duration threshold: 30 seconds
        MIN_DURATION_SECONDS = 30
        
        # Track total calls counted
        total_calls_counted = 0
        
        # Debug: Print sample data to verify column names
        if data:
            print(f"🔍 Sample row keys: {list(data[0].keys())}")
            print(f"🔍 Sample row data: {data[0]}")
        
        # Process each row
        processed_count = 0
        skipped_no_datetime = 0
        skipped_wrong_caller = 0
        skipped_duration = 0
        skipped_date = 0
        
        for row in data:
            caller = row.get('ผู้โทร', '').strip()
            start_datetime = row.get('start', '').strip()
            duration_str = row.get('สรุปเวลา', '').strip()
            
            # Parse Google Sheets datetime format (7/11/2025, 11:46:51)
            parsed_datetime = parse_google_sheets_datetime(start_datetime)
            if not parsed_datetime:
                skipped_no_datetime += 1
                continue
            
            # Check if caller is in target range (101-108 only)
            if caller not in target_callers:
                skipped_wrong_caller += 1
                continue
            
            # Parse duration
            duration_seconds = parse_duration_to_seconds(duration_str)
            
            # Only count if duration >= 30 seconds
            if duration_seconds < MIN_DURATION_SECONDS:
                skipped_duration += 1
                continue
            
            # Filter by date (compare YYYY-MM-DD format)
            if parsed_datetime['date'] != date_param:
                skipped_date += 1
                continue
            
            processed_count += 1
            
            # Get hour from parsed datetime
            hour = parsed_datetime['hour']
            
            # Find matching time slot (9:00-20:00)
            for slot in time_slots:
                if slot['hour_start'] <= hour < slot['hour_end']:
                    slot_counts[slot['start']][caller] += 1
                    agent_totals[caller] += 1
                    total_calls_counted += 1
                    break
        
        # Debug: Print filtering statistics
        print(f"📊 Filtering stats:")
        print(f"  - Total rows: {len(data)}")
        print(f"  - Processed successfully: {processed_count}")
        print(f"  - Skipped (no datetime): {skipped_no_datetime}")
        print(f"  - Skipped (wrong caller): {skipped_wrong_caller}")
        print(f"  - Skipped (duration < {MIN_DURATION_SECONDS}s): {skipped_duration}")
        print(f"  - Skipped (wrong date): {skipped_date}")
        print(f"  - Total calls counted: {total_calls_counted}")
        
        # Build response in format expected by React
        response_data = {
            'success': True,
            'date': date_param,
            'timeSlots': [],
            'slotCounts': slot_counts,  # สำหรับใช้ใน getCallTableValue
            'totals': agent_totals,     # จำนวนรวมต่อ agent
            'totalCalls': total_calls_counted,
            'message': f'Counted {total_calls_counted} calls for {date_param} with duration >= {MIN_DURATION_SECONDS} seconds',
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Sheets (สรุป call_AI)',
            'debug': {
                'total_rows': len(data),
                'processed': processed_count,
                'skipped_no_datetime': skipped_no_datetime,
                'skipped_wrong_caller': skipped_wrong_caller,
                'skipped_duration': skipped_duration,
                'skipped_date': skipped_date
            },
            'filter_criteria': {
                'callers': target_callers,
                'min_duration_seconds': MIN_DURATION_SECONDS,
                'time_slots_count': len(time_slots),
                'date': date_param
            }
        }
        
        # Add timeSlots array for detailed view (เฉพาะช่วงที่มีข้อมูล)
        for slot in time_slots:
            slot_data = slot_counts[slot['start']]
            # เพิ่มเฉพาะช่วงที่มีการโทรจริงๆ
            if any(count > 0 for count in slot_data.values()):
                # กรองเฉพาะ agent ที่มีการโทร
                agent_counts_filtered = {agent: count for agent, count in slot_data.items() if count > 0}
                response_data['timeSlots'].append({
                    'hourStart': slot['start'],
                    'hourEnd': str(slot['hour_end']),
                    'label': slot['label'],
                    'agentCounts': agent_counts_filtered
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


# ========================================
# Facebook Ads API
# ========================================

def get_date_range(date_preset=None, time_range=None):
    """Convert date_preset or time_range to since/until format"""
    if time_range:
        return time_range.get('since'), time_range.get('until')
    
    today = datetime.now()
    
    if date_preset == 'today':
        return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
    elif date_preset == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')
    elif date_preset == 'last_7d':
        since = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        return since, today.strftime('%Y-%m-%d')
    elif date_preset == 'last_30d':
        since = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        return since, today.strftime('%Y-%m-%d')
    elif date_preset == 'this_month':
        since = today.replace(day=1).strftime('%Y-%m-%d')
        return since, today.strftime('%Y-%m-%d')
    elif date_preset == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        return first_day_last_month.strftime('%Y-%m-%d'), last_day_last_month.strftime('%Y-%m-%d')
    else:
        return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')


@app.route('/api/facebook-ads-campaigns', methods=['GET'])
def get_facebook_ads_campaigns():
    """
    Get Facebook Ads campaigns data
    
    Query Parameters:
    - level: "campaign" | "adset" | "ad" (default: "campaign")
    - date_preset: "today" | "yesterday" | "last_7d" | "last_30d" | "this_month" | "last_month"
    - time_range: JSON string {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
    - time_increment: "1" for daily breakdown, "monthly" for monthly (optional)
    - fields: Comma-separated list of additional fields (optional)
    """
    try:
        # Get environment variables
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        ad_account_id = os.getenv('FACEBOOK_AD_ACCOUNT_ID')
        
        if not access_token or not ad_account_id:
            return jsonify({
                'success': False,
                'error': 'Missing Facebook credentials. Please set FACEBOOK_ACCESS_TOKEN and FACEBOOK_AD_ACCOUNT_ID',
                'data': [],
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Get query parameters
        level = request.args.get('level', 'campaign')
        date_preset = request.args.get('date_preset', 'today')
        time_range_param = request.args.get('time_range')
        time_increment = request.args.get('time_increment')
        custom_fields = request.args.get('fields')
        
        # Parse time_range if provided
        time_range = None
        if time_range_param:
            try:
                time_range = json.loads(time_range_param)
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid time_range format. Expected JSON string.',
                    'data': [],
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        # Get date range
        since, until = get_date_range(date_preset, time_range)
        
        print(f"📊 Fetching Facebook Ads data for {level} from {since} to {until}")
        
        # Initialize Facebook API
        FacebookAdsApi.init(access_token=access_token)
        
        # Get ad account
        account = AdAccount(ad_account_id)
        
        # Build params for insights
        params = {
            'level': level,
            'time_range': {'since': since, 'until': until},
        }
        
        # Add time_increment if specified (for daily breakdown)
        if time_increment:
            params['time_increment'] = time_increment
        
        # Fields to fetch - comprehensive list
        fields = [
            'campaign_id',
            'campaign_name',
            'adset_id',
            'adset_name',
            'ad_id',
            'ad_name',
            'spend',
            'impressions',
            'clicks',
            'ctr',
            'cpc',
            'cpm',
            'cpp',
            'reach',
            'frequency',
            'actions',
            'action_values',
            'conversions',
            'conversion_values',
            'cost_per_action_type',
            'cost_per_conversion',
            'date_start',
            'date_stop'
        ]
        
        # Add custom fields if provided
        if custom_fields:
            custom_fields_list = [f.strip() for f in custom_fields.split(',')]
            fields.extend(custom_fields_list)
            fields = list(set(fields))  # Remove duplicates
        
        # Get insights
        print(f"🔍 Requesting insights with fields: {fields}")
        insights = account.get_insights(
            fields=fields,
            params=params
        )
        
        # Process results
        data = []
        total_spend = 0
        total_impressions = 0
        total_reach = 0
        total_clicks = 0
        total_conversions = 0
        total_leads = 0
        total_purchase = 0
        
        for insight in insights:
            insight_dict = dict(insight)
            
            # Process actions for easier access
            processed_actions = {}
            if 'actions' in insight_dict and insight_dict['actions']:
                for action in insight_dict['actions']:
                    action_type = action.get('action_type', '')
                    action_value = int(action.get('value', 0))
                    processed_actions[action_type] = action_value
                    
                    # Count specific action types
                    if action_type == 'lead':
                        total_leads += action_value
                    elif action_type == 'purchase':
                        total_purchase += action_value
            
            # Add processed actions to insight
            insight_dict['processed_actions'] = processed_actions
            
            # Extract key metrics
            spend = float(insight_dict.get('spend', 0))
            impressions = int(insight_dict.get('impressions', 0))
            reach = int(insight_dict.get('reach', 0))
            clicks = int(insight_dict.get('clicks', 0))
            
            # Get conversions (from new conversion field or from actions)
            conversions = 0
            if 'conversions' in insight_dict and insight_dict['conversions']:
                for conv in insight_dict['conversions']:
                    conversions += float(conv.get('value', 0))
            else:
                # Fallback to counting from actions
                conversions = processed_actions.get('lead', 0) + processed_actions.get('purchase', 0)
            
            insight_dict['total_conversions'] = conversions
            
            # Add calculated metrics
            insight_dict['cost_per_result'] = round(spend / conversions, 2) if conversions > 0 else 0
            
            data.append(insight_dict)
            
            # Calculate totals
            total_spend += spend
            total_impressions += impressions
            total_reach += reach
            total_clicks += clicks
            total_conversions += conversions
        
        # Build summary
        summary = {
            'total_spend': round(total_spend, 2),
            'total_impressions': total_impressions,
            'total_reach': total_reach,
            'total_clicks': total_clicks,
            'total_conversions': round(total_conversions, 2),
            'total_leads': total_leads,
            'total_purchase': total_purchase,
            'average_cpc': round(total_spend / total_clicks, 2) if total_clicks > 0 else 0,
            'average_ctr': round((total_clicks / total_impressions) * 100, 2) if total_impressions > 0 else 0,
            'cost_per_result': round(total_spend / total_conversions, 2) if total_conversions > 0 else 0,
            'frequency': round(total_impressions / total_reach, 2) if total_reach > 0 else 0
        }
        
        print(f"✅ Successfully fetched {len(data)} {level}(s) from Facebook Ads")
        
        # Build response
        response = {
            'success': True,
            'level': level,
            'date_preset': date_preset if not time_range else None,
            'time_range': {'since': since, 'until': until},
            'time_increment': time_increment,
            'data': data,
            'summary': summary,
            'total_records': len(data),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/facebook-ads-campaigns: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500


# ========================================
# Facebook Ads Manager API (Alias)
# ========================================

@app.route('/api/facebook-ads-manager', methods=['GET'])
def get_facebook_ads_manager():
    """Alias for /api/facebook-ads-campaigns"""
    return get_facebook_ads_campaigns()


# ========================================
# Google Sheets Data API (เคสได้ชื่อเบอร์)
# ========================================

@app.route('/api/google-sheets-data', methods=['GET'])
def get_google_sheets_data():
    """
    Get data from Google Sheets 'เคสได้ชื่อเบอร์' sheet
    
    Query Parameters:
    - date_preset: "today" | "yesterday" | "last_7d" | "last_30d" | "this_month" | "last_month"
    - time_range: JSON string {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
    - daily: "true" to get daily breakdown
    """
    try:
        # Get query parameters
        date_preset = request.args.get('date_preset', 'today')
        time_range_param = request.args.get('time_range')
        daily = request.args.get('daily', '').lower() == 'true'
        
        # Parse time_range if provided
        time_range = None
        if time_range_param:
            try:
                time_range = json.loads(time_range_param)
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid time_range format. Expected JSON string.',
                    'data': []
                }), 400
        
        # Get date range
        since, until = get_date_range(date_preset, time_range)
        
        # Get spreadsheet ID from environment
        spreadsheet_id = os.getenv('GOOGLE_SHEET_ID') or os.getenv('GOOGLE_SPREADSHEET_ID')
        if not spreadsheet_id:
            return jsonify({
                'success': False,
                'error': 'GOOGLE_SHEET_ID not set in environment variables',
                'data': []
            }), 400
        
        print(f"📊 Fetching data from Google Sheets 'เคสได้ชื่อเบอร์': {spreadsheet_id}")
        
        # Get Google Sheets client
        client = get_google_sheets_client()
        
        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get the 'เคสได้ชื่อเบอร์' sheet
        sheet = spreadsheet.worksheet('เคสได้ชื่อเบอร์')
        
        # Get all values from the sheet
        all_values = sheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            return jsonify({
                'success': True,
                'total': 0,
                'dateRange': {'start': since, 'end': until},
                'hasDateColumn': False,
                'data': []
            })
        
        # Get headers and data rows
        headers = all_values[0]
        data_rows = all_values[1:]
        
        # Find date column (column A = index 0)
        date_col_index = 0
        has_date_column = len(headers) > 0
        
        print(f"📋 Headers: {headers}")
        print(f"📝 Sample row: {data_rows[0] if data_rows else 'No data'}")
        
        # Parse dates and filter
        filtered_data = []
        daily_counts = {}
        
        since_date = datetime.strptime(since, '%Y-%m-%d')
        until_date = datetime.strptime(until, '%Y-%m-%d')
        
        for row in data_rows:
            if len(row) <= date_col_index:
                continue
            
            date_str = row[date_col_index].strip()
            if not date_str:
                continue
            
            # Parse date (support DD/MM/YYYY or YYYY-MM-DD)
            try:
                if '/' in date_str:
                    # DD/MM/YYYY format
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                        row_date = datetime(year, month, day)
                    else:
                        continue
                else:
                    # YYYY-MM-DD format
                    row_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Filter by date range
                if since_date <= row_date <= until_date:
                    filtered_data.append({
                        'date': date_str,
                        'namePhone': row[1] if len(row) > 1 else ''
                    })
                    
                    # Count by date for daily breakdown
                    date_key = row_date.strftime('%Y-%m-%d')
                    daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
                    
            except (ValueError, IndexError):
                continue
        
        # Build response
        if daily:
            # Daily breakdown response
            daily_data = [{'date': date, 'count': count} 
                         for date, count in sorted(daily_counts.items(), reverse=True)]
            
            response = {
                'success': True,
                'dailyData': daily_data,
                'total': len(filtered_data),
                'dateRange': {'start': since, 'end': until},
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Standard response
            response = {
                'success': True,
                'total': len(filtered_data),
                'dateRange': {'start': since, 'end': until},
                'dateColIndex': date_col_index,
                'hasDateColumn': has_date_column,
                'totalRowsBeforeFilter': len(data_rows),
                'rowsAfterDateFilter': len(filtered_data),
                'data': filtered_data,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"✅ Successfully fetched {len(filtered_data)} records from 'เคสได้ชื่อเบอร์' sheet")
        
        return jsonify(response)
        
    except gspread.exceptions.WorksheetNotFound:
        print("❌ Worksheet 'เคสได้ชื่อเบอร์' not found")
        return jsonify({
            'success': False,
            'error': "Worksheet 'เคสได้ชื่อเบอร์' not found in spreadsheet",
            'data': []
        }), 404
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/google-sheets-data: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500


# ========================================
# Google Ads API
# ========================================

@app.route('/N_SaleIncentive_data', methods=['GET'])
def get_n_sale_incentive_data():
    """
    Get data from N_SaleIncentive sheet
    
    Query Parameters:
    - month: เดือน (1-12) - optional
    - year: ปี (เช่น 2025) - optional
    
    If month and year are provided, returns filtered data for that month.
    Otherwise, returns all data.
    """
    try:
        # Get query parameters
        month_param = request.args.get('month')
        year_param = request.args.get('year')
        
        # Get spreadsheet ID from environment
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID not set in environment variables")
        
        print(f"📊 Fetching data from N_SaleIncentive sheet: {spreadsheet_id}")
        
        # Get Google Sheets client
        client = get_google_sheets_client()
        
        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get the 'N_SaleIncentive' sheet
        worksheet = spreadsheet.worksheet('N_SaleIncentive')
        
        # Get all records
        records = worksheet.get_all_records()
        
        print(f"📋 Total records from N_SaleIncentive: {len(records)}")
        
        # Process data
        sale_data = []
        for record in records:
            try:
                # Get fields from record
                sale_date_str = record.get('SaleDate', '').strip()
                if not sale_date_str:
                    continue  # Skip records without date
                
                # Parse SaleDate (format: "2025-11-09 10:06:11")
                try:
                    sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d %H:%M:%S').date()
                except ValueError:
                    # Try alternative format without time
                    try:
                        sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"⚠️ Invalid date format: {sale_date_str}")
                        continue
                
                # Get Sale person and Income
                sale_person = record.get('Sale', '').strip()
                income_str = record.get('InCome', '0')
                
                # Convert income to float
                try:
                    income = float(income_str) if income_str else 0
                except ValueError:
                    income = 0
                
                # Filter by month and year if provided
                if month_param and year_param:
                    month = int(month_param)
                    year = int(year_param)
                    
                    if sale_date.month != month or sale_date.year != year:
                        continue  # Skip records that don't match the filter
                
                # Add to result
                sale_data.append({
                    'sale_person': sale_person,
                    'sale_date': sale_date.isoformat(),  # Format: "2025-11-09"
                    'income': income,
                    'day': sale_date.day,
                    'month': sale_date.month,
                    'year': sale_date.year
                })
                
            except Exception as e:
                print(f"⚠️ Error processing record: {e}")
                continue
        
        # Build response
        response = {
            'success': True,
            'data': sale_data,
            'total_records': len(sale_data),
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Sheets (N_SaleIncentive)'
        }
        
        # Add filter info if filtering was applied
        if month_param and year_param:
            response['filter'] = {
                'month': int(month_param),
                'year': int(year_param)
            }
        
        print(f"✅ Successfully processed {len(sale_data)} records from N_SaleIncentive")
        
        return jsonify(response)
        
    except gspread.exceptions.WorksheetNotFound:
        print("❌ Worksheet 'N_SaleIncentive' not found")
        return jsonify({
            'success': False,
            'error': "Worksheet 'N_SaleIncentive' not found in spreadsheet",
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 404
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /N_SaleIncentive_data: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/google-ads', methods=['GET'])
def get_google_ads():
    """
    Get Google Ads data
    
    Query Parameters:
    - startDate: Start date (YYYY-MM-DD) default: today
    - endDate: End date (YYYY-MM-DD) default: today
    - daily: "true" to get daily breakdown
    """
    try:
        # Get query parameters
        start_date = request.args.get('startDate', datetime.now().strftime('%Y-%m-%d'))
        end_date = request.args.get('endDate', datetime.now().strftime('%Y-%m-%d'))
        daily = request.args.get('daily', '').lower() == 'true'
        
        # Get environment variables
        client_id = os.getenv('GOOGLE_ADS_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET')
        developer_token = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')
        refresh_token = os.getenv('GOOGLE_ADS_REFRESH_TOKEN')
        customer_id = os.getenv('GOOGLE_ADS_CUSTOMER_ID')
        
        if not all([client_id, client_secret, developer_token, refresh_token, customer_id]):
            return jsonify({
                'success': False,
                'error': 'Missing Google Ads credentials. Please check environment variables.',
                'campaigns': []
            }), 400
        
        # Remove hyphens from customer_id if present
        customer_id = customer_id.replace('-', '')
        
        # Create Google Ads client configuration
        credentials = {
            'developer_token': developer_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'use_proto_plus': True,
            'use_cloud_org_for_api_access': False
        }
        
        # Initialize Google Ads client with v13 (compatible with google-ads 22.0.0)
        client = GoogleAdsClient.load_from_dict(credentials)
        ga_service = client.get_service('GoogleAdsService', version='v13')
        
        # Convert dates to YYYYMMDD format (required by Google Ads API)
        start_date_formatted = start_date.replace('-', '')
        end_date_formatted = end_date.replace('-', '')
        
        # Build query - simplified for v13
        if daily:
            # Daily breakdown query
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    segments.date,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.cost_micros
                FROM campaign
                WHERE segments.date >= '{start_date_formatted}'
                  AND segments.date <= '{end_date_formatted}'
                ORDER BY segments.date DESC
            """
        else:
            # Campaign-level query
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.cost_micros
                FROM campaign
                WHERE segments.date >= '{start_date_formatted}'
                  AND segments.date <= '{end_date_formatted}'
            """
        
        # Execute query
        response = ga_service.search(customer_id=customer_id, query=query)
        
        # Process results
        if daily:
            # Daily breakdown
            daily_data = {}
            
            for row in response:
                date = row.segments.date
                
                if date not in daily_data:
                    daily_data[date] = {
                        'date': date,
                        'clicks': 0,
                        'impressions': 0,
                        'cost': 0,
                        'conversions': 0
                    }
                
                daily_data[date]['clicks'] += row.metrics.clicks
                daily_data[date]['impressions'] += row.metrics.impressions
                daily_data[date]['cost'] += row.metrics.cost_micros / 1000000
                daily_data[date]['conversions'] += row.metrics.conversions
            
            daily_list = sorted(daily_data.values(), key=lambda x: x['date'], reverse=True)
            
            result = {
                'success': True,
                'dailyData': daily_list,
                'dateRange': {
                    'startDate': start_date,
                    'endDate': end_date
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Campaign-level
            campaigns = []
            total_clicks = 0
            total_impressions = 0
            total_cost = 0
            
            for row in response:
                campaign = row.campaign
                metrics = row.metrics
                
                clicks = metrics.clicks
                impressions = metrics.impressions
                cost = metrics.cost_micros / 1000000
                average_cpc = metrics.average_cpc / 1000000 if metrics.average_cpc else 0
                ctr = metrics.ctr * 100 if metrics.ctr else 0
                conversions = metrics.conversions
                
                campaigns.append({
                    'id': str(campaign.id),
                    'name': campaign.name,
                    'status': campaign.status.name,
                    'clicks': clicks,
                    'impressions': impressions,
                    'averageCpc': round(average_cpc, 2),
                    'cost': round(cost, 2),
                    'ctr': round(ctr, 2),
                    'conversions': conversions
                })
                
                total_clicks += clicks
                total_impressions += impressions
                total_cost += cost
            
            avg_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            
            result = {
                'campaigns': campaigns,
                'summary': {
                    'totalClicks': total_clicks,
                    'totalImpressions': total_impressions,
                    'averageCpc': round(avg_cpc, 2),
                    'totalCost': round(total_cost, 2),
                    'averageCtr': round(avg_ctr, 2)
                },
                'dateRange': {
                    'startDate': start_date,
                    'endDate': end_date
                },
                'timestamp': datetime.now().isoformat()
            }
        
        return jsonify(result)
        
    except GoogleAdsException as ex:
        error_message = f"Google Ads API error: {ex.error.message}"
        print(f"❌ {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'campaigns': [],
            'timestamp': datetime.now().isoformat()
        }), 500
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/google-ads: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'campaigns': [],
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/data_bjh', methods=['GET'])
def get_data_bjh():
    """
    Get all leads data from BJH PostgreSQL database
    
    Query Parameters:
    - limit: Maximum number of records to return (optional)
    - status: Filter by status (optional)
    - source: Filter by source (optional)
    - doctor: Filter by doctor (optional)
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', type=int)
        status_filter = request.args.get('status')
        source_filter = request.args.get('source')
        doctor_filter = request.args.get('doctor')
        
        # Get database connection
        connection = get_db_connection()
        
        if not connection:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to database',
                'data': [],
                'timestamp': datetime.now().isoformat()
            }), 500
        
        try:
            cursor = connection.cursor()
            
            # Build query with filters
            query = 'SELECT * FROM "BJH-Server"."bjh_all_leads"'
            conditions = []
            params = []
            
            if status_filter:
                conditions.append('status = %s')
                params.append(status_filter)
            
            if source_filter:
                conditions.append('source = %s')
                params.append(source_filter)
            
            if doctor_filter:
                conditions.append('doctor = %s')
                params.append(doctor_filter)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            if limit:
                query += f' LIMIT {limit}'
            
            # Execute query
            cursor.execute(query, params)
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Fetch all results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            import datetime as dt
            data = []
            for row in rows:
                row_dict = {}
                for i, col_name in enumerate(column_names):
                    value = row[i]
                    # Convert date/datetime objects to string
                    if isinstance(value, (dt.datetime, dt.date)):
                        value = value.isoformat()
                    row_dict[col_name] = value
                data.append(row_dict)
            
            cursor.close()
            
            # Build response
            response = {
                'success': True,
                'data': data,
                'total': len(data),
                'columns': column_names,
                'filters': {
                    'status': status_filter,
                    'source': source_filter,
                    'doctor': doctor_filter,
                    'limit': limit
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'PostgreSQL (BJH-Server.bjh_all_leads)'
            }
            
            print(f"✅ Successfully fetched {len(data)} records from bjh_all_leads")
            
            return jsonify(response)
            
        except Error as e:
            error_message = f"Database error: {str(e)}"
            print(f"❌ {error_message}")
            traceback.print_exc()
            
            return jsonify({
                'success': False,
                'error': error_message,
                'data': [],
                'timestamp': datetime.now().isoformat()
            }), 500
            
        finally:
            if connection:
                connection.close()
    
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /data_bjh: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500


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
            '/N_SaleIncentive_data',
            '/api/clear-cache',
            '/api/facebook-ads-campaigns',
            '/api/google-sheets-data',
            '/api/google-ads',
            '/data_bjh'
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
