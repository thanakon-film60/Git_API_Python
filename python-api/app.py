"""
Flask API for accessing Google Sheets data (Film data)
This API serves as a backend for the Performance Surgery Schedule system.
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_compress import Compress
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
import shutil
import tempfile
from pathlib import Path
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None
import mimetypes

# Import Call Matrix services
from services.google_sheets import GoogleSheetsService
from services.call_matrix import CallMatrixService

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable response compression (gzip)
Compress(app)

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

# Facebook Ads cache (แยกออกมาต่างหาก)
fb_ads_cache = {
    'data': {},  # เก็บตาม cache_key
    'timestamps': {},
    'expires_at': {}
}
FB_ADS_CACHE_DURATION = int(os.getenv('FB_ADS_CACHE_DURATION', 300))  # 5 นาที (300 วินาที)

# Initialize Call Matrix services
sheets_service = GoogleSheetsService()
call_matrix_service = CallMatrixService(sheets_service)


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
            '/api/film-data-contacts': 'Get contact data from Film data sheet (ผู้ติดต่อ, วันที่ได้นัด consult, วันที่ได้นัดผ่าตัด) (GET)',
            '/api/google-sheets/film-data': 'Get all raw data from Film data sheet (all columns and rows)',
            '/run-time': 'Get call statistics from สรุป call_AI sheet mapped by time slots (9:00-20:00) for callers 101-108',
            '/N_SaleIncentive_data': 'Get sale incentive data from N_SaleIncentive sheet (supports month/year filtering) (GET)',
            '/api/clear-cache': 'Clear data cache (POST)',
            '/api/facebook-ads-campaigns': 'Get Facebook Ads campaigns data (supports level, date filtering, daily breakdown) (GET)',
            '/api/facebook-ads-manager': 'Alias for /api/facebook-ads-campaigns (GET)',
            '/api/facebook-ads-insights': 'Get Facebook Ads Insights via Graph API v24.0 - simple and flexible (GET)',
            '/api/facebook-graph-insights': 'Get Facebook Ad insights via Graph API with video thumbnails (GET)',
            '/api/facebook-videos-direct': 'Get Facebook videos with direct downloadable URLs (แนะนำ) (GET)',
            '/api/facebook-videos': 'Get Facebook videos from ads (supports ad_id, date filtering) (GET)',
            '/api/google-sheets-data': 'Get Google Sheets data from เคสได้ชื่อเบอร์ sheet (GET)',
            '/api/google-ads': 'Get Google Ads data (GET)',
            '/data_bjh': 'Get all leads data from BJH PostgreSQL database (GET)',
            '/api/call-matrix': 'Get call matrix data for all agents (GET)',
            '/api/call-matrix/agent/<agent_id>': 'Get call summary for specific agent (GET)',
            '/api/call-matrix/time-slot/<time_slot>': 'Get call summary for specific time slot (GET)',
            '/api/call-matrix/log': 'Log a call for an agent (POST)',
            '/api/call-matrix/update': 'Update call count manually (POST)',
            '/api/call-matrix/batch-update': 'Batch update call counts (POST)'
        }
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_status': {
            'google_sheets': {
                'has_data': cache['data'] is not None,
                'cached_at': cache['timestamp'].isoformat() if cache['timestamp'] else None,
                'expires_at': cache['expires_at'].isoformat() if cache['expires_at'] else None
            },
            'facebook_ads': {
                'cached_keys': len(fb_ads_cache['data']),
                'cache_duration': FB_ADS_CACHE_DURATION
            }
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


@app.route('/api/film-data-contacts', methods=['GET'])
def get_film_data_contacts():
    """
    Get specific columns from Google Sheets 'Film data' sheet
    Returns only: ผู้ติดต่อ, วันที่ได้นัด consult, วันที่ได้นัดผ่าตัด
    
    Query Parameters:
    - count: "true" to get count summary by date (optional)
    - date: "YYYY-MM-DD" to filter by specific date (optional)
    - today: "true" to filter by today's date (optional)
    
    Example:
        GET /api/film-data-contacts
        GET /api/film-data-contacts?count=true
        GET /api/film-data-contacts?count=true&today=true
        GET /api/film-data-contacts?count=true&date=2025-11-18
    """
    try:
        # Get query parameters
        show_count = request.args.get('count', '').lower() == 'true'
        filter_today = request.args.get('today', '').lower() == 'true'
        filter_date = request.args.get('date', '').strip()
        
        # Get spreadsheet ID from environment
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID not set in environment variables")

        print(f"📊 Fetching contact data from Google Sheets 'Film data': {spreadsheet_id}")

        # Get Google Sheets client
        client = get_google_sheets_client()

        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Get the 'Film data' sheet
        sheet = spreadsheet.worksheet('Film data')

        # Get all values from the sheet
        all_values = sheet.get_all_values()

        if not all_values or len(all_values) < 2:
            return jsonify({
                'success': True,
                'data': [],
                'total': 0,
                'timestamp': datetime.now().isoformat(),
                'source': 'Google Sheets (Film data)'
            })

        # Get headers
        headers = all_values[0]
        data_rows = all_values[1:]

        # Find column indexes for required fields
        try:
            contact_col = headers.index('ผู้ติดต่อ')
            consult_date_col = headers.index('วันที่ได้นัด consult')
            surgery_date_col = headers.index('วันที่ได้นัดผ่าตัด')
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Required column not found: {str(e)}',
                'available_columns': headers,
                'data': [],
                'timestamp': datetime.now().isoformat()
            }), 400

        # Helper function to parse and normalize date
        def normalize_date(date_str):
            """แปลงวันที่จาก DD/MM/YYYY หรือ YYYY-MM-DD เป็น YYYY-MM-DD"""
            if not date_str or not date_str.strip():
                return None
            
            date_str = date_str.strip()
            
            try:
                # ลอง DD/MM/YYYY (รูปแบบจาก Google Sheets)
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                        return f"{year:04d}-{month:02d}-{day:02d}"
                
                # ลอง YYYY-MM-DD
                elif '-' in date_str:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    return date_str
                
                return None
            except (ValueError, IndexError):
                return None
        
        # กำหนดวันที่สำหรับกรอง
        target_date = None
        if filter_today:
            target_date = datetime.now().strftime('%Y-%m-%d')
        elif filter_date:
            # Validate date format
            try:
                datetime.strptime(filter_date, '%Y-%m-%d')
                target_date = filter_date
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD',
                    'data': [],
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        # Extract data
        result = []
        consult_date_counts = {}  # นับจำนวน consult แต่ละวัน
        surgery_date_counts = {}  # นับจำนวนผ่าตัดแต่ละวัน
        
        for idx, row in enumerate(data_rows, start=2):  # Start from row 2 (1-indexed)
            if len(row) <= max(contact_col, consult_date_col, surgery_date_col):
                continue

            contact_person = row[contact_col].strip() if contact_col < len(row) else ''
            consult_date_raw = row[consult_date_col].strip() if consult_date_col < len(row) else ''
            surgery_date_raw = row[surgery_date_col].strip() if surgery_date_col < len(row) else ''

            # แปลงวันที่เป็นรูปแบบมาตรฐาน YYYY-MM-DD
            consult_date_normalized = normalize_date(consult_date_raw)
            surgery_date_normalized = normalize_date(surgery_date_raw)

            # Skip empty rows
            if not contact_person and not consult_date_raw and not surgery_date_raw:
                continue
            
            # กรองตามวันที่ถ้ามีการระบุ
            if target_date:
                # ตรวจสอบว่ามีวันที่ตรงกับที่กรองหรือไม่ (เทียบรูปแบบ normalized)
                if consult_date_normalized != target_date and surgery_date_normalized != target_date:
                    continue

            result.append({
                'id': f'film-{idx}',
                'ผู้ติดต่อ': contact_person,
                'วันที่ได้นัด consult': consult_date_raw,
                'วันที่ได้นัดผ่าตัด': surgery_date_raw,
                # English field names for easier access
                'contact_person': contact_person,
                'consult_date': consult_date_raw,
                'consult_date_normalized': consult_date_normalized,
                'surgery_appointment_date': surgery_date_raw,
                'surgery_appointment_date_normalized': surgery_date_normalized
            })
            
            # นับจำนวนตามวันที่ (ใช้รูปแบบ normalized)
            if consult_date_normalized:
                consult_date_counts[consult_date_normalized] = consult_date_counts.get(consult_date_normalized, 0) + 1
            
            if surgery_date_normalized:
                surgery_date_counts[surgery_date_normalized] = surgery_date_counts.get(surgery_date_normalized, 0) + 1

        print(f"✅ Successfully fetched {len(result)} records from 'Film data'")

        # Build response
        response = {
            'success': True,
            'data': result,
            'total': len(result),
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Sheets (Film data)',
            'columns': ['ผู้ติดต่อ', 'วันที่ได้นัด consult', 'วันที่ได้นัดผ่าตัด']
        }
        
        # เพิ่มข้อมูลการกรอง
        if target_date:
            response['filter'] = {
                'date': target_date,
                'type': 'today' if filter_today else 'custom'
            }
        
        # Add count summary if requested
        if show_count:
            # แปลงเป็น array และเรียงตามวันที่
            consult_counts_array = [
                {'date': date, 'count': count} 
                for date, count in sorted(consult_date_counts.items())
            ]
            
            surgery_counts_array = [
                {'date': date, 'count': count} 
                for date, count in sorted(surgery_date_counts.items())
            ]
            
            response['count_summary'] = {
                'consult_appointments': {
                    'total_dates': len(consult_date_counts),
                    'total_appointments': sum(consult_date_counts.values()),
                    'by_date': consult_counts_array
                },
                'surgery_appointments': {
                    'total_dates': len(surgery_date_counts),
                    'total_appointments': sum(surgery_date_counts.values()),
                    'by_date': surgery_counts_array
                }
            }

        return jsonify(response)

    except gspread.exceptions.WorksheetNotFound:
        print("❌ Worksheet 'Film data' not found")
        return jsonify({
            'success': False,
            'error': "Worksheet 'Film data' not found in spreadsheet",
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 404

    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Spreadsheet not found")
        return jsonify({
            'success': False,
            'error': "Spreadsheet not found. Check GOOGLE_SPREADSHEET_ID and service account permissions",
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
        print(f"❌ Error in /api/film-data-contacts: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
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
    global cache, fb_ads_cache
    cache = {
        'data': None,
        'timestamp': None,
        'expires_at': None
    }
    fb_ads_cache = {
        'data': {},
        'timestamps': {},
        'expires_at': {}
    }

    return jsonify({
        'success': True,
        'message': 'All caches cleared successfully (Google Sheets + Facebook Ads)',
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
    Get Facebook Ads campaigns data (Optimized with caching)
    
    Query Parameters:
    - level: "campaign" | "adset" | "ad" (default: "campaign")
    - date_preset: "today" | "yesterday" | "last_7d" | "last_30d" | "this_month" | "last_month"
    - time_range: JSON string {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
    - time_increment: "1" for daily breakdown, "monthly" for monthly (optional)
    - action_breakdowns: comma-separated (e.g., "action_type")
    - fields: Comma-separated list of additional fields (optional)
    - limit: Maximum number of records to return (optional, default: 1000)
    - no_cache: "true" to bypass cache (optional)
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
        action_breakdowns = request.args.get('action_breakdowns')
        custom_fields = request.args.get('fields')
        limit = request.args.get('limit', type=int, default=1000)
        no_cache = request.args.get('no_cache', '').lower() == 'true'
        
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
        
        # สร้าง cache key
        cache_key = f"{level}_{since}_{until}_{time_increment}_{action_breakdowns}_{custom_fields}_{limit}"
        
        # ตรวจสอบ cache
        global fb_ads_cache
        now = datetime.now()
        
        if not no_cache and cache_key in fb_ads_cache['data']:
            if (cache_key in fb_ads_cache['expires_at'] and 
                now < fb_ads_cache['expires_at'][cache_key]):
                cached_response = fb_ads_cache['data'][cache_key]
                cached_response['cached'] = True
                cached_response['cache_expires_in'] = (fb_ads_cache['expires_at'][cache_key] - now).seconds
                print(f"✅ Returning cached Facebook Ads data (expires in {cached_response['cache_expires_in']}s)")
                return jsonify(cached_response)
        
        print(f"📊 Fetching Facebook Ads data for {level} from {since} to {until}")
        
        # Initialize Facebook API
        FacebookAdsApi.init(access_token=access_token)
        
        # Get ad account
        account = AdAccount(ad_account_id)
        
        # Build params for insights
        params = {
            'level': level,
            'time_range': {'since': since, 'until': until},
            'limit': limit
        }
        
        # Add time_increment if specified (for daily breakdown)
        if time_increment:
            params['time_increment'] = time_increment
        
        # Add action_breakdowns if specified
        if action_breakdowns:
            params['action_breakdowns'] = [x.strip() for x in action_breakdowns.split(',')]
        
        # Fields to fetch - เฉพาะที่จำเป็น (ลดภาระ API)
        fields = [
            'campaign_id',
            'campaign_name',
            'spend',
            'impressions',
            'clicks',
            'ctr',
            'cpc',
            'cpm',
            'reach',
            'actions',
            'cost_per_action_type',
            'date_start',
            'date_stop'
        ]
        
        # เพิ่ม fields ตาม level
        if level in ['adset', 'ad']:
            fields.extend(['adset_id', 'adset_name'])
        if level == 'ad':
            fields.extend(['ad_id', 'ad_name'])
        
        # Add custom fields if provided
        if custom_fields:
            custom_fields_list = [f.strip() for f in custom_fields.split(',')]
            fields.extend(custom_fields_list)
            fields = list(set(fields))  # Remove duplicates
        
        # Get insights
        print(f"🔍 Requesting insights with {len(fields)} fields, limit: {limit}")
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
            
            # Get conversions (from actions)
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
            'timestamp': datetime.now().isoformat(),
            'cached': False,
            'cache_duration': FB_ADS_CACHE_DURATION
        }
        
        # บันทึกลง cache
        fb_ads_cache['data'][cache_key] = response.copy()
        fb_ads_cache['timestamps'][cache_key] = now
        fb_ads_cache['expires_at'][cache_key] = now + timedelta(seconds=FB_ADS_CACHE_DURATION)
        
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
# Facebook Ads Insights API - Simple Direct Call
# ========================================

@app.route('/api/facebook-ads-insights', methods=['GET'])
def get_facebook_ads_insights():
    """
    Get Facebook Ads Insights via Graph API v24.0
    ดึงข้อมูล insights ของ Facebook Ads โดยตรงจาก Graph API
    
    Query Parameters:
    - ad_account_id: Ad Account ID (optional, ถ้าไม่ระบุจะใช้จาก env)
    - level: "ad" | "adset" | "campaign" (default: "ad")
    - date_preset: "today" | "yesterday" | "last_7d" | "last_14d" | "last_30d" | "this_month" | "last_month" (default: "today")
    - since: วันที่เริ่มต้น format YYYY-MM-DD (optional, จะ override date_preset)
    - until: วันที่สิ้นสุด format YYYY-MM-DD (optional, ใช้คู่กับ since)
    - fields: comma-separated fields (optional, มี default fields)
    - action_breakdowns: "action_type" เพื่อดู breakdown ของ actions (optional)
    - limit: จำนวน records สูงสุด (default: 500)
    - no_cache: "true" เพื่อข้าม cache (optional)
    
    Default Fields:
    - ad_id, ad_name, adset_id, adset_name, campaign_id, campaign_name
    - spend, impressions, clicks, ctr, cpc, cpm, actions
    
    Example:
        GET /api/facebook-ads-insights
        GET /api/facebook-ads-insights?level=ad&date_preset=today
        GET /api/facebook-ads-insights?level=ad&date_preset=today&action_breakdowns=action_type
        GET /api/facebook-ads-insights?ad_account_id=act_454323590676166&date_preset=today
        GET /api/facebook-ads-insights?since=2025-11-01&until=2025-11-30
    """
    try:
        # Get environment variables
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        default_ad_account_id = os.getenv('FACEBOOK_AD_ACCOUNT_ID')
        
        if not access_token:
            return jsonify({
                'success': False,
                'error': 'Missing FACEBOOK_ACCESS_TOKEN environment variable',
                'data': [],
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Get query parameters
        ad_account_id = request.args.get('ad_account_id', default_ad_account_id)
        level = request.args.get('level', 'ad')
        date_preset = request.args.get('date_preset', 'today')
        since_param = request.args.get('since')
        until_param = request.args.get('until')
        custom_fields = request.args.get('fields')
        action_breakdowns = request.args.get('action_breakdowns')
        limit = request.args.get('limit', type=int, default=500)
        no_cache = request.args.get('no_cache', '').lower() == 'true'
        
        # Validate ad_account_id
        if not ad_account_id:
            return jsonify({
                'success': False,
                'error': 'Missing ad_account_id. Please provide via query param or set FACEBOOK_AD_ACCOUNT_ID env variable',
                'data': [],
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Ensure ad_account_id has "act_" prefix
        if not ad_account_id.startswith('act_'):
            ad_account_id = f'act_{ad_account_id}'
        
        # Validate level
        valid_levels = ['ad', 'adset', 'campaign']
        if level not in valid_levels:
            return jsonify({
                'success': False,
                'error': f'Invalid level. Must be one of: {valid_levels}',
                'data': [],
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Determine date range
        if since_param and until_param:
            since = since_param
            until = until_param
            date_type = 'custom'
            use_time_range = True
        else:
            since, until = get_date_range(date_preset)
            date_type = 'preset'
            use_time_range = False
        
        # Create cache key
        cache_key = f"insights_{ad_account_id}_{level}_{since}_{until}_{custom_fields}_{action_breakdowns}_{limit}"
        
        # Check cache
        global fb_ads_cache
        now = datetime.now()
        
        if not no_cache and cache_key in fb_ads_cache['data']:
            if (cache_key in fb_ads_cache['expires_at'] and 
                now < fb_ads_cache['expires_at'][cache_key]):
                cached_response = fb_ads_cache['data'][cache_key].copy()
                cached_response['cached'] = True
                cached_response['cache_expires_in'] = (fb_ads_cache['expires_at'][cache_key] - now).seconds
                print(f"✅ Returning cached Facebook Ads Insights (expires in {cached_response['cache_expires_in']}s)")
                return jsonify(cached_response)
        
        print(f"📊 Fetching Facebook Ads Insights: account={ad_account_id}, level={level}, date={date_preset}")
        
        # Build fields list
        if custom_fields:
            fields_list = [f.strip() for f in custom_fields.split(',')]
        else:
            # Default fields based on level
            fields_list = [
                'spend',
                'impressions',
                'clicks',
                'ctr',
                'cpc',
                'cpm',
                'actions'
            ]
            
            # Add level-specific fields
            if level == 'ad':
                fields_list = ['ad_id', 'ad_name', 'adset_id', 'adset_name', 'campaign_id', 'campaign_name'] + fields_list
            elif level == 'adset':
                fields_list = ['adset_id', 'adset_name', 'campaign_id', 'campaign_name'] + fields_list
            elif level == 'campaign':
                fields_list = ['campaign_id', 'campaign_name'] + fields_list
        
        # Build Graph API URL
        api_version = 'v24.0'
        base_url = f'https://graph.facebook.com/{api_version}/{ad_account_id}/insights'
        
        # Build params
        params = {
            'level': level,
            'fields': ','.join(fields_list),
            'access_token': access_token,
            'limit': limit
        }
        
        # Add date parameters
        if use_time_range:
            params['time_range'] = json.dumps({'since': since, 'until': until})
        else:
            params['date_preset'] = date_preset
        
        # Add action_breakdowns if specified
        if action_breakdowns:
            params['action_breakdowns'] = action_breakdowns
        
        print(f"📡 API Request: {base_url}")
        print(f"   Level: {level}, Date: {date_preset if not use_time_range else f'{since} to {until}'}")
        print(f"   Fields: {', '.join(fields_list)}")
        if action_breakdowns:
            print(f"   Action Breakdowns: {action_breakdowns}")
        
        # Make request to Graph API
        response = requests.get(base_url, params=params, timeout=60)
        
        # Check for errors
        if not response.ok:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
            error_code = error_data.get('error', {}).get('code', 0)
            error_type = error_data.get('error', {}).get('type', 'Unknown')
            
            print(f"❌ Facebook API Error: {error_msg}")
            
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': error_code,
                'error_type': error_type,
                'data': [],
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = response.json()
        data = result.get('data', [])
        
        # Process actions for easier access
        for item in data:
            if 'actions' in item and item['actions']:
                processed_actions = {}
                for action in item['actions']:
                    action_type = action.get('action_type', 'unknown')
                    action_value = action.get('value', '0')
                    processed_actions[action_type] = action_value
                item['actions_breakdown'] = processed_actions
        
        # Calculate summary
        total_spend = 0
        total_impressions = 0
        total_clicks = 0
        total_leads = 0
        total_messages = 0
        
        for item in data:
            total_spend += float(item.get('spend', 0))
            total_impressions += int(item.get('impressions', 0))
            total_clicks += int(item.get('clicks', 0))
            
            # Count leads and messages from actions
            if 'actions_breakdown' in item:
                total_leads += int(item['actions_breakdown'].get('lead', 0))
                total_messages += int(item['actions_breakdown'].get('onsite_conversion.messaging_conversation_started_7d', 0))
        
        # Build summary
        summary = {
            'total_spend': round(total_spend, 2),
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'total_leads': total_leads,
            'total_messages': total_messages,
            'average_ctr': round((total_clicks / total_impressions) * 100, 2) if total_impressions > 0 else 0,
            'average_cpc': round(total_spend / total_clicks, 2) if total_clicks > 0 else 0,
            'average_cpm': round((total_spend / total_impressions) * 1000, 2) if total_impressions > 0 else 0,
            'cost_per_lead': round(total_spend / total_leads, 2) if total_leads > 0 else 0
        }
        
        print(f"✅ Successfully fetched {len(data)} {level}(s) from Facebook Ads")
        print(f"   Summary: Spend={summary['total_spend']}, Impressions={summary['total_impressions']}, Clicks={summary['total_clicks']}")
        
        # Build response
        api_response = {
            'success': True,
            'api_version': api_version,
            'ad_account_id': ad_account_id,
            'level': level,
            'date_type': date_type,
            'date_preset': date_preset if date_type == 'preset' else None,
            'date_range': {
                'since': since,
                'until': until
            },
            'fields': fields_list,
            'action_breakdowns': action_breakdowns,
            'data': data,
            'summary': summary,
            'total_records': len(data),
            'paging': result.get('paging', {}),
            'timestamp': datetime.now().isoformat(),
            'cached': False,
            'cache_duration': FB_ADS_CACHE_DURATION
        }
        
        # Save to cache
        fb_ads_cache['data'][cache_key] = api_response.copy()
        fb_ads_cache['timestamps'][cache_key] = now
        fb_ads_cache['expires_at'][cache_key] = now + timedelta(seconds=FB_ADS_CACHE_DURATION)
        
        return jsonify(api_response)
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request timeout. Facebook API is slow.',
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500
        
    except requests.exceptions.RequestException as e:
        error_message = f"Facebook API request failed: {str(e)}"
        print(f"❌ {error_message}")
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/facebook-ads-insights: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500


# ========================================
# Facebook Graph API - Direct Insights
# ========================================

@app.route('/api/facebook-graph-insights', methods=['GET'])
def get_facebook_graph_insights():
    """
    Get Facebook Ad insights directly via Graph API v24.0
    
    Query Parameters:
    - level: "ad" | "adset" | "campaign" (default: "ad")
    - date_preset: "today" | "yesterday" | "last_7d" | "last_30d" (default: "today")
    - action_breakdowns: comma-separated (e.g., "action_type")
    - include_videos: "true" to include video thumbnails and URLs
    - limit: Maximum number of results (default: 100)
    
    Example:
        GET /api/facebook-graph-insights?level=ad&date_preset=today&include_videos=true
    """
    try:
        # Get environment variables
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        ad_account_id = os.getenv('FACEBOOK_AD_ACCOUNT_ID')
        
        if not access_token or not ad_account_id:
            return jsonify({
                'success': False,
                'error': 'Missing Facebook credentials',
                'data': []
            }), 400
        
        # Get query parameters
        level = request.args.get('level', 'ad')
        date_preset = request.args.get('date_preset', 'today')
        action_breakdowns = request.args.get('action_breakdowns', '')
        include_videos = request.args.get('include_videos', '').lower() == 'true'
        limit = request.args.get('limit', type=int, default=100)
        
        # Build Graph API URL
        base_url = f'https://graph.facebook.com/v24.0/{ad_account_id}/insights'
        
        # Build fields
        fields = [
            'ad_id',
            'ad_name',
            'adset_id',
            'adset_name',
            'campaign_id',
            'campaign_name',
            'spend',
            'impressions',
            'clicks',
            'ctr',
            'cpc',
            'cpm',
            'reach',
            'actions',
            'cost_per_action_type'
        ]
        
        # Build params
        params = {
            'level': level,
            'fields': ','.join(fields),
            'date_preset': date_preset,
            'access_token': access_token,
            'limit': limit
        }
        
        if action_breakdowns:
            params['action_breakdowns'] = action_breakdowns
        
        print(f"📊 Fetching Graph API insights: {base_url}")
        
        # Make request to Graph API
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        result = response.json()
        ads_data = result.get('data', [])
        
        # Process ads and optionally fetch videos
        processed_data = []
        
        for ad in ads_data:
            ad_id = ad.get('ad_id')
            
            ad_info = {
                **ad,
                'video_thumbnail': None,
                'video_url': None,
                'has_video': False
            }
            
            # Fetch video info if requested
            if include_videos and ad_id:
                try:
                    # Get ad creative
                    creative_url = f'https://graph.facebook.com/v24.0/{ad_id}'
                    creative_params = {
                        'fields': 'creative{thumbnail_url,video_id,object_story_spec}',
                        'access_token': access_token
                    }
                    
                    creative_response = requests.get(creative_url, params=creative_params)
                    if creative_response.ok:
                        creative_data = creative_response.json()
                        
                        if 'creative' in creative_data:
                            creative = creative_data['creative']
                            
                            # Get thumbnail
                            thumbnail = creative.get('thumbnail_url')
                            video_id = creative.get('video_id')
                            
                            if thumbnail:
                                ad_info['video_thumbnail'] = thumbnail
                                ad_info['has_video'] = True
                            
                            # Get video URL if available
                            if video_id:
                                video_url = f'https://graph.facebook.com/v24.0/{video_id}'
                                video_params = {
                                    'fields': 'source,permalink_url,picture',
                                    'access_token': access_token
                                }
                                
                                video_response = requests.get(video_url, params=video_params)
                                if video_response.ok:
                                    video_data = video_response.json()
                                    ad_info['video_url'] = video_data.get('source')
                                    ad_info['video_permalink'] = video_data.get('permalink_url')
                                    ad_info['video_thumbnail'] = video_data.get('picture', ad_info['video_thumbnail'])
                
                except Exception as e:
                    print(f"⚠️ Error fetching video for ad {ad_id}: {str(e)}")
            
            processed_data.append(ad_info)
        
        print(f"✅ Successfully fetched {len(processed_data)} ads from Graph API")
        
        # Build response
        response_data = {
            'success': True,
            'api_version': 'v24.0',
            'level': level,
            'date_preset': date_preset,
            'data': processed_data,
            'total_records': len(processed_data),
            'paging': result.get('paging', {}),
            'timestamp': datetime.now().isoformat(),
            'graph_api_url': base_url
        }
        
        return jsonify(response_data)
        
    except requests.exceptions.RequestException as e:
        error_message = f"Graph API request failed: {str(e)}"
        print(f"❌ {error_message}")
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/facebook-graph-insights: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'data': [],
            'timestamp': datetime.now().isoformat()
        }), 500


# ========================================
# Facebook Video API - Test Endpoint
# ========================================

@app.route('/api/test-facebook-videos', methods=['GET'])
def test_facebook_videos():
    """
    Test endpoint for Facebook video API
    ทดสอบการดึงวิดีโอจาก Facebook Ads
    
    Query Parameters:
    - limit: จำนวนวิดีโอที่ต้องการทดสอบ (default: 3)
    
    Example:
        GET /api/test-facebook-videos
        GET /api/test-facebook-videos?limit=5
    """
    try:
        # Get parameters
        limit = request.args.get('limit', type=int, default=3)
        
        # Get credentials
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        page_access_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
        ad_account_id = os.getenv('FACEBOOK_AD_ACCOUNT_ID')
        
        if not access_token or not ad_account_id:
            return jsonify({
                'success': False,
                'error': 'Missing credentials. Please check FACEBOOK_ACCESS_TOKEN and FACEBOOK_AD_ACCOUNT_ID',
                'test_status': 'failed',
                'videos': []
            }), 400
        
        # Use Page Access Token for video fetching if available
        video_token = page_access_token if page_access_token else access_token
        
        print(f"🧪 Testing Facebook Video API (limit: {limit})")
        
        # Build test request
        insights_url = f'https://graph.facebook.com/v24.0/{ad_account_id}/insights'
        params = {
            'level': 'ad',
            'fields': 'ad_id,ad_name,campaign_name,spend,impressions',
            'date_preset': 'today',
            'access_token': access_token,
            'limit': limit
        }
        
        # Fetch insights
        print("📡 Step 1: Fetching ad insights...")
        response = requests.get(insights_url, params=params, timeout=30)
        response.raise_for_status()
        
        insights_data = response.json().get('data', [])
        print(f"✅ Found {len(insights_data)} ads")
        
        if not insights_data:
            return jsonify({
                'success': True,
                'test_status': 'no_ads_found',
                'message': 'No ads found for today. Try changing date_preset.',
                'videos': [],
                'debug_info': {
                    'api_url': insights_url,
                    'date_preset': 'today'
                }
            })
        
        # Process videos
        test_results = []
        videos_found = 0
        
        for i, insight in enumerate(insights_data, 1):
            ad_id = insight.get('ad_id')
            print(f"\n📹 Step 2.{i}: Checking ad {ad_id}")
            
            result = {
                'step': i,
                'ad_id': ad_id,
                'ad_name': insight.get('ad_name'),
                'has_creative': False,
                'has_video': False,
                'video_data': None,
                'errors': []
            }
            
            try:
                # Get creative
                creative_url = f'https://graph.facebook.com/v24.0/{ad_id}'
                creative_params = {
                    'fields': 'creative{video_id,thumbnail_url}',
                    'access_token': access_token
                }
                
                creative_response = requests.get(creative_url, params=creative_params, timeout=10)
                if creative_response.ok:
                    creative_data = creative_response.json()
                    creative = creative_data.get('creative', {})
                    result['has_creative'] = True
                    
                    video_id = creative.get('video_id')
                    if video_id:
                        result['has_video'] = True
                        print(f"   ✅ Found video ID: {video_id}")
                        
                        # Get video details (use Page Access Token for video file access)
                        video_url = f'https://graph.facebook.com/v24.0/{video_id}'
                        video_params = {
                            'fields': 'source,title,length,picture,permalink_url',
                            'access_token': video_token  # Use Page Access Token instead of Ads Token
                        }
                        
                        video_response = requests.get(video_url, params=video_params, timeout=10)
                        if video_response.ok:
                            video_data = video_response.json()
                            result['video_data'] = {
                                'video_id': video_id,
                                'title': video_data.get('title', insight.get('ad_name')),
                                'length': video_data.get('length', 0),
                                'source_url': video_data.get('source', '')[:100] + '...' if video_data.get('source') else None,
                                'permalink': video_data.get('permalink_url'),
                                'thumbnail': video_data.get('picture', '')[:100] + '...' if video_data.get('picture') else None,
                                'has_download_url': bool(video_data.get('source'))
                            }
                            videos_found += 1
                            print(f"   ✅ Video details retrieved successfully")
                        else:
                            result['errors'].append(f"Failed to fetch video details: {video_response.status_code}")
                    else:
                        print(f"   ⚠️ No video in this ad")
                else:
                    result['errors'].append(f"Failed to fetch creative: {creative_response.status_code}")
                    
            except Exception as e:
                result['errors'].append(str(e))
                print(f"   ❌ Error: {str(e)}")
            
            test_results.append(result)
        
        # Summary
        summary = {
            'total_ads_checked': len(insights_data),
            'ads_with_creative': sum(1 for r in test_results if r.get('has_creative', False)),
            'ads_with_video': sum(1 for r in test_results if r.get('has_video', False)),
            'videos_with_download_url': sum(1 for r in test_results if r.get('video_data') and r['video_data'].get('has_download_url', False))
        }
        
        print(f"\n📊 Test Summary:")
        print(f"   - Total ads checked: {summary['total_ads_checked']}")
        print(f"   - Ads with video: {summary['ads_with_video']}")
        print(f"   - Videos with download URL: {summary['videos_with_download_url']}")
        
        # Response
        return jsonify({
            'success': True,
            'test_status': 'completed',
            'message': f'Test completed. Found {videos_found} videos with download URLs.',
            'summary': summary,
            'test_results': test_results,
            'timestamp': datetime.now().isoformat(),
            'api_info': {
                'endpoint': '/api/facebook-videos-direct',
                'description': 'Use this endpoint to get all videos with download URLs',
                'example': '/api/facebook-videos-direct?date_preset=today'
            }
        })
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'test_status': 'timeout',
            'error': 'Request timeout. Facebook API may be slow.',
            'videos': []
        }), 500
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'test_status': 'api_error',
            'error': f'Facebook API error: {str(e)}',
            'videos': []
        }), 500
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'test_status': 'error',
            'error': str(e),
            'videos': []
        }), 500


# ========================================
# Facebook Video API - Direct Video URLs
# ========================================

@app.route('/api/facebook-videos-direct', methods=['GET'])
def get_facebook_videos_direct():
    """
    Get Facebook videos with direct downloadable URLs
    
    Query Parameters:
    - date_preset: "today" | "yesterday" | "last_7d" | "last_30d" (default: "today")
    - limit: Maximum number of videos (default: 50)
    - ad_id: Specific ad ID (optional)
    
    Returns videos with:
    - Direct video source URL (downloadable)
    - Thumbnail URL
    - Public permalink
    - Ad performance data
    
    Example:
        GET /api/facebook-videos-direct?date_preset=today
        GET /api/facebook-videos-direct?ad_id=120232539320390180
    """
    try:
        # Get environment variables
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        page_access_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
        ad_account_id = os.getenv('FACEBOOK_AD_ACCOUNT_ID')
        
        if not access_token or not ad_account_id:
            return jsonify({
                'success': False,
                'error': 'Missing Facebook credentials',
                'videos': []
            }), 400
        
        # Use Page Access Token for video fetching if available, otherwise use regular token
        video_token = page_access_token if page_access_token else access_token
        
        # Get query parameters
        date_preset = request.args.get('date_preset', 'today')
        limit = request.args.get('limit', type=int, default=50)
        ad_id_filter = request.args.get('ad_id')
        
        print(f"🎥 Fetching videos from Facebook Ads (date_preset: {date_preset})")
        
        # Get date range
        since, until = get_date_range(date_preset)
        
        videos_data = []
        
        # Build Graph API URL for insights
        insights_url = f'https://graph.facebook.com/v24.0/{ad_account_id}/insights'
        insights_params = {
            'level': 'ad',
            'fields': 'ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,reach',
            'access_token': access_token,
            'limit': limit
        }
        
        # Add time range - use time_range for custom dates or date_preset for presets
        if since and until:
            insights_params['time_range'] = json.dumps({
                'since': since,
                'until': until
            })
        else:
            insights_params['date_preset'] = date_preset
        
        # Add ad_id filter if specified
        if ad_id_filter:
            insights_params['filtering'] = json.dumps([{
                'field': 'ad.id',
                'operator': 'EQUAL',
                'value': ad_id_filter
            }])
        
        print(f"📡 API Request: {insights_url}")
        print(f"   Parameters: level=ad, date_preset={date_preset}, limit={limit}")
        
        # Fetch insights
        insights_response = requests.get(insights_url, params=insights_params, timeout=30)
        insights_response.raise_for_status()
        insights_data = insights_response.json().get('data', [])
        
        if not insights_data:
            print(f"⚠️ No ads found with date_preset={date_preset}")
            print(f"   Try: today, yesterday, last_7d, last_30d, maximum")
        
        print(f"📊 Found {len(insights_data)} ads")
        
        # Process each ad to get video
        for insight in insights_data:
            ad_id = insight.get('ad_id')
            if not ad_id:
                continue
            
            try:
                # Get ad creative with video info
                creative_url = f'https://graph.facebook.com/v24.0/{ad_id}'
                creative_params = {
                    'fields': 'creative{video_id,thumbnail_url,object_story_spec}',
                    'access_token': access_token
                }
                
                creative_response = requests.get(creative_url, params=creative_params)
                if not creative_response.ok:
                    continue
                
                creative_data = creative_response.json()
                creative = creative_data.get('creative', {})
                video_id = creative.get('video_id')
                
                if not video_id:
                    continue
                
                # Get video details with source URL (use Page Access Token for video file access)
                video_url = f'https://graph.facebook.com/v24.0/{video_id}'
                video_params = {
                    'fields': 'source,title,description,length,picture,permalink_url,created_time,format,embed_html,status',
                    'access_token': video_token  # Use Page Access Token instead of Ads Token
                }
                
                video_response = requests.get(video_url, params=video_params, timeout=10)
                if not video_response.ok:
                    error_detail = video_response.json() if video_response.text else {}
                    error_msg = error_detail.get('error', {}).get('message', 'Unknown error')
                    print(f"   ⚠️ Failed to fetch video {video_id}: {video_response.status_code} - {error_msg}")
                    
                    # Still add video info with limited data (thumbnail and permalink only)
                    video_info = {
                        'ad_id': ad_id,
                        'ad_name': insight.get('ad_name'),
                        'adset_name': insight.get('adset_name'),
                        'campaign_name': insight.get('campaign_name'),
                        'video_id': video_id,
                        'video_title': insight.get('ad_name'),
                        'video_source_url': None,
                        'video_permalink': f'https://www.facebook.com/{video_id}',
                        'thumbnail_url': creative.get('thumbnail_url'),
                        'error': f'Cannot access video: {error_msg}',
                        'ad_performance': {
                            'spend': insight.get('spend', '0'),
                            'impressions': insight.get('impressions', '0'),
                            'clicks': insight.get('clicks', '0'),
                            'reach': insight.get('reach', '0')
                        },
                        'download_instructions': {
                            'note': 'Video details unavailable. This may be due to: 1) Missing permissions (needs pages_read_engagement), 2) Video is private/deleted, or 3) Video belongs to a page you don\'t have access to',
                            'alternative': 'Try viewing at: https://business.facebook.com/adsmanager'
                        }
                    }
                    videos_data.append(video_info)
                    continue
                
                video_data = video_response.json()
                
                # Get the best quality video format if available
                video_source = video_data.get('source')  # Direct video URL
                video_formats = video_data.get('format', [])
                
                # Try to get HD video if available
                hd_video_url = None
                sd_video_url = None
                if video_formats and isinstance(video_formats, list):
                    # Sort by height to get highest quality
                    sorted_formats = sorted(
                        video_formats,
                        key=lambda x: x.get('height', 0),
                        reverse=True
                    )
                    if sorted_formats:
                        hd_video_url = sorted_formats[0].get('embed_html') or sorted_formats[0].get('filter')
                        # Get SD version as fallback
                        if len(sorted_formats) > 1:
                            sd_video_url = sorted_formats[-1].get('embed_html') or sorted_formats[-1].get('filter')
                
                # If source is not available, try to construct download URL from video ID
                if not video_source:
                    print(f"   ⚠️ No 'source' field for video {video_id}, using alternative method")
                    # Try alternative: Use permalink or construct URL
                    video_source = None  # Will use permalink instead
                
                # Build video info
                video_info = {
                    'ad_id': ad_id,
                    'ad_name': insight.get('ad_name'),
                    'adset_name': insight.get('adset_name'),
                    'campaign_name': insight.get('campaign_name'),
                    'video_id': video_id,
                    'video_title': video_data.get('title', insight.get('ad_name')),
                    'video_description': video_data.get('description', ''),
                    'video_length': video_data.get('length', 0),
                    'video_source_url': video_source,  # Direct downloadable URL (may be None if no permission)
                    'video_hd_url': hd_video_url,  # HD version if available
                    'video_sd_url': sd_video_url,  # SD version as fallback
                    'video_permalink': video_data.get('permalink_url'),  # Public Facebook link
                    'thumbnail_url': video_data.get('picture', creative.get('thumbnail_url')),
                    'embed_html': video_data.get('embed_html', ''),
                    'created_time': video_data.get('created_time'),
                    'video_status': video_data.get('status', {}).get('video_status'),
                    'ad_performance': {
                        'spend': insight.get('spend', '0'),
                        'impressions': insight.get('impressions', '0'),
                        'clicks': insight.get('clicks', '0'),
                        'reach': insight.get('reach', '0')
                    },
                    'download_instructions': {
                        'method_1': f'Direct: curl -o video.mp4 "{video_source}"' if video_source else 'Source URL not available - requires additional permissions',
                        'method_2': f'With token: curl -o video.mp4 "{video_source}?access_token=YOUR_TOKEN"' if video_source else None,
                        'method_3': f'Public link: {video_data.get("permalink_url")}',
                        'note': 'If video_source_url is null, your access token needs pages_read_engagement permission or the video is not public'
                    }
                }
                
                videos_data.append(video_info)
                print(f"✅ Found video: {video_info['video_title']}")
                
            except Exception as e:
                print(f"⚠️ Error processing ad {ad_id}: {str(e)}")
                continue
        
        print(f"🎬 Total videos found: {len(videos_data)}")
        
        # Build response
        response = {
            'success': True,
            'date_preset': date_preset,
            'date_range': {'since': since, 'until': until},
            'videos': videos_data,
            'total_videos': len(videos_data),
            'timestamp': datetime.now().isoformat(),
            'usage_note': 'Use video_source_url for direct download. Some URLs may require access_token parameter.',
            'download_example': f'wget "{{video_source_url}}?access_token={access_token[:20]}..."'
        }
        
        return jsonify(response)
        
    except requests.exceptions.RequestException as e:
        error_message = f"Facebook API request failed: {str(e)}"
        print(f"❌ {error_message}")
        
        return jsonify({
            'success': False,
            'error': error_message,
            'videos': []
        }), 500
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/facebook-videos-direct: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'videos': []
        }), 500


# ========================================
# Facebook Video API
# ========================================

@app.route('/api/facebook-videos', methods=['GET'])
def get_facebook_videos():
    """
    Get Facebook videos from ads
    
    Query Parameters:
    - ad_id: Facebook Ad ID (optional, if not provided will get all ads with videos)
    - level: "ad" (default) | "adset" | "campaign"
    - date_preset: "today" | "yesterday" | "last_7d" | "last_30d" (default: "last_7d")
    - limit: Maximum number of videos to return (default: 50)
    
    Example:
        GET /api/facebook-videos
        GET /api/facebook-videos?ad_id=120232539320390180
        GET /api/facebook-videos?date_preset=last_30d&limit=100
    """
    try:
        # Get environment variables
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        ad_account_id = os.getenv('FACEBOOK_AD_ACCOUNT_ID')
        app_id = os.getenv('FACEBOOK_APP_ID', '1086145253509335')
        
        if not access_token or not ad_account_id:
            return jsonify({
                'success': False,
                'error': 'Missing Facebook credentials. Please set FACEBOOK_ACCESS_TOKEN and FACEBOOK_AD_ACCOUNT_ID',
                'videos': [],
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Get query parameters
        ad_id_param = request.args.get('ad_id')
        level = request.args.get('level', 'ad')
        date_preset = request.args.get('date_preset', 'last_7d')
        limit = request.args.get('limit', type=int, default=50)
        
        # Get date range
        since, until = get_date_range(date_preset)
        
        print(f"📹 Fetching Facebook videos from {since} to {until}")
        
        # Initialize Facebook API
        FacebookAdsApi.init(access_token=access_token)
        
        videos_data = []
        
        if ad_id_param:
            # Get video from specific ad
            try:
                from facebook_business.adobjects.ad import Ad
                
                ad = Ad(ad_id_param)
                
                # Get ad creative
                ad_data = ad.api_get(fields=[
                    'id',
                    'name',
                    'creative',
                    'status'
                ])
                
                if 'creative' in ad_data and ad_data['creative']:
                    creative_id = ad_data['creative']['id']
                    
                    # Get creative details including video
                    from facebook_business.adobjects.adcreative import AdCreative
                    creative = AdCreative(creative_id)
                    creative_data = creative.api_get(fields=[
                        'id',
                        'name',
                        'object_story_spec',
                        'video_id',
                        'thumbnail_url',
                        'title',
                        'body'
                    ])
                    
                    # Get video details if available
                    video_id = creative_data.get('video_id')
                    if video_id:
                        from facebook_business.adobjects.advideo import AdVideo
                        video = AdVideo(video_id)
                        video_data = video.api_get(fields=[
                            'id',
                            'title',
                            'description',
                            'length',
                            'source',
                            'picture',
                            'embed_html',
                            'created_time',
                            'updated_time',
                            'permalink_url'
                        ])
                        
                        videos_data.append({
                            'ad_id': ad_id_param,
                            'ad_name': ad_data.get('name'),
                            'video_id': video_id,
                            'video_title': video_data.get('title'),
                            'video_description': video_data.get('description'),
                            'video_length': video_data.get('length'),
                            'video_url': video_data.get('source'),
                            'video_permalink': video_data.get('permalink_url'),
                            'thumbnail_url': video_data.get('picture'),
                            'embed_html': video_data.get('embed_html'),
                            'created_time': video_data.get('created_time'),
                            'updated_time': video_data.get('updated_time')
                        })
                
            except Exception as e:
                print(f"⚠️ Error fetching video for ad {ad_id_param}: {str(e)}")
        
        else:
            # Get all ads with videos
            account = AdAccount(ad_account_id)
            
            # Get insights to find ads
            params = {
                'level': level,
                'time_range': {'since': since, 'until': until},
                'limit': limit,
                'filtering': [
                    {
                        'field': 'impressions',
                        'operator': 'GREATER_THAN',
                        'value': 0
                    }
                ]
            }
            
            fields = [
                'ad_id',
                'ad_name',
                'adset_id',
                'adset_name',
                'campaign_id',
                'campaign_name'
            ]
            
            insights = account.get_insights(fields=fields, params=params)
            
            # Process each ad to check for videos
            from facebook_business.adobjects.ad import Ad
            from facebook_business.adobjects.adcreative import AdCreative
            from facebook_business.adobjects.advideo import AdVideo
            
            for insight in insights:
                try:
                    ad_id = insight.get('ad_id')
                    if not ad_id:
                        continue
                    
                    ad = Ad(ad_id)
                    ad_data = ad.api_get(fields=['id', 'name', 'creative'])
                    
                    if 'creative' in ad_data and ad_data['creative']:
                        creative_id = ad_data['creative']['id']
                        
                        try:
                            creative = AdCreative(creative_id)
                            creative_data = creative.api_get(fields=[
                                'video_id',
                                'thumbnail_url',
                                'title',
                                'body'
                            ])
                            
                            video_id = creative_data.get('video_id')
                            if video_id:
                                try:
                                    video = AdVideo(video_id)
                                    video_data = video.api_get(fields=[
                                        'id',
                                        'title',
                                        'description',
                                        'length',
                                        'source',
                                        'picture',
                                        'embed_html',
                                        'created_time',
                                        'updated_time',
                                        'permalink_url'
                                    ])
                                    
                                    videos_data.append({
                                        'ad_id': ad_id,
                                        'ad_name': insight.get('ad_name'),
                                        'adset_name': insight.get('adset_name'),
                                        'campaign_name': insight.get('campaign_name'),
                                        'video_id': video_id,
                                        'video_title': video_data.get('title'),
                                        'video_description': video_data.get('description'),
                                        'video_length': video_data.get('length'),
                                        'video_url': video_data.get('source'),
                                        'video_permalink': video_data.get('permalink_url'),
                                        'thumbnail_url': video_data.get('picture'),
                                        'embed_html': video_data.get('embed_html'),
                                        'created_time': video_data.get('created_time'),
                                        'updated_time': video_data.get('updated_time')
                                    })
                                    
                                except Exception as e:
                                    print(f"⚠️ Error fetching video {video_id}: {str(e)}")
                                    
                        except Exception as e:
                            print(f"⚠️ Error fetching creative {creative_id}: {str(e)}")
                            
                except Exception as e:
                    print(f"⚠️ Error processing ad: {str(e)}")
                    continue
        
        print(f"✅ Successfully fetched {len(videos_data)} videos from Facebook Ads")
        
        # Build response
        response = {
            'success': True,
            'app_id': app_id,
            'date_range': {'since': since, 'until': until},
            'videos': videos_data,
            'total_videos': len(videos_data),
            'timestamp': datetime.now().isoformat(),
            'usage_notes': {
                'video_url': 'Direct video file URL (may require authentication)',
                'video_permalink': 'Public Facebook video link',
                'embed_html': 'HTML embed code for the video',
                'thumbnail_url': 'Video thumbnail image URL'
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/facebook-videos: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'videos': [],
            'timestamp': datetime.now().isoformat()
        }), 500


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
        
        # Initialize Google Ads client with v17 (compatible with google-ads 22.1.0)
        client = GoogleAdsClient.load_from_dict(credentials)
        ga_service = client.get_service('GoogleAdsService')
        
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


# ========================================
# Call Matrix API Endpoints
# ========================================

@app.route('/api/call-matrix', methods=['GET'])
def get_call_matrix():
    """ดึงข้อมูล Call Matrix ทั้งหมด

    Query Parameters:
        date (optional): วันที่ในรูปแบบ YYYY-MM-DD (ถ้าไม่ระบุจะใช้วันที่ล่าสุด)
        use_latest (optional): "true" หรือ "false" - ใช้วันที่ล่าสุดหรือไม่ (default: true เฉพาะตอนไม่ระบุ date)

    Example:
        GET /api/call-matrix
        GET /api/call-matrix?date=2025-11-18
        GET /api/call-matrix?use_latest=true
    """
    try:
        date = request.args.get('date')
        use_latest_param = request.args.get('use_latest')
        
        # ถ้าระบุ date แล้ว ให้ use_latest = false (ยกเว้นถ้ามีการระบุ use_latest ไว้)
        if date and use_latest_param is None:
            use_latest = False
        else:
            use_latest = use_latest_param is None or use_latest_param.lower() == 'true'
        
        result = call_matrix_service.get_call_matrix(date, use_latest)

        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/call-matrix: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/call-matrix/agent/<agent_id>', methods=['GET'])
def get_agent_summary(agent_id):
    """ดึงสรุปการโทรของ agent คนหนึ่ง

    Path Parameters:
        agent_id: รหัส agent (เช่น '101', '102')

    Query Parameters:
        date (optional): วันที่

    Example:
        GET /api/call-matrix/agent/101?date=2025-11-18
    """
    try:
        date = request.args.get('date')
        result = call_matrix_service.get_agent_summary(agent_id, date)

        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/call-matrix/agent: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/call-matrix/time-slot/<time_slot>', methods=['GET'])
def get_time_slot_summary(time_slot):
    """ดึงสรุปการโทรในช่วงเวลาหนึ่ง

    Path Parameters:
        time_slot: ช่วงเวลา (เช่น '9-10', '10-11')

    Query Parameters:
        date (optional): วันที่

    Example:
        GET /api/call-matrix/time-slot/9-10?date=2025-11-18
    """
    try:
        date = request.args.get('date')
        result = call_matrix_service.get_time_slot_summary(time_slot, date)

        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/call-matrix/time-slot: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/call-matrix/log', methods=['POST'])
def log_call():
    """บันทึกการโทร

    Request Body:
        {
            "agent_id": "101",
            "call_type": "outgoing",  # optional, default: "outgoing"
            "time_slot": "9-10"       # optional, default: current time slot
        }

    Example:
        POST /api/call-matrix/log
        {
            "agent_id": "101"
        }
    """
    try:
        data = request.get_json()

        if not data or 'agent_id' not in data:
            return jsonify({
                "success": False,
                "error": "agent_id is required"
            }), 400

        agent_id = data.get('agent_id')
        call_type = data.get('call_type', 'outgoing')
        time_slot = data.get('time_slot')

        result = call_matrix_service.log_call(agent_id, call_type, time_slot)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/call-matrix/log: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/call-matrix/update', methods=['POST'])
def update_call_count():
    """อัพเดทจำนวนการโทรด้วยตนเอง

    Request Body:
        {
            "agent_id": "101",
            "time_slot": "9-10",
            "value": 5
        }

    Example:
        POST /api/call-matrix/update
        {
            "agent_id": "101",
            "time_slot": "9-10",
            "value": 5
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400

        required_fields = ['agent_id', 'time_slot', 'value']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"{field} is required"
                }), 400

        agent_id = data.get('agent_id')
        time_slot = data.get('time_slot')
        value = data.get('value')

        # ใช้ set_call_count แทน update_call_count เพื่อตั้งค่าโดยตรง
        result = sheets_service.set_call_count(agent_id, time_slot, value)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/call-matrix/update: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/call-matrix/batch-update', methods=['POST'])
def batch_update_call_counts():
    """อัพเดทหลายช่องพร้อมกัน

    Request Body:
        {
            "updates": [
                {"agent_id": "101", "time_slot": "9-10", "value": 5},
                {"agent_id": "102", "time_slot": "10-11", "value": 8}
            ]
        }
    """
    try:
        data = request.get_json()

        if not data or 'updates' not in data:
            return jsonify({
                "success": False,
                "error": "updates array is required"
            }), 400

        updates = data.get('updates', [])
        result = sheets_service.batch_update_call_counts(updates)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/call-matrix/batch-update: {error_message}")
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }), 500


# ========================================
# MP4 to MP3 Converter API
# ========================================

@app.route('/api/convert/mp4-to-mp3', methods=['POST'])
def convert_mp4_to_mp3():
    """
    Convert MP4 video to MP3 audio file
    
    Methods:
    - POST: Upload file and convert
    
    Request:
    - Upload file: multipart/form-data with 'file' parameter
    
    Query Parameters:
    - bitrate: Audio bitrate (default: '192k'), e.g., '128k', '192k', '320k'
    - sample_rate: Sample rate (default: 44100), e.g., 22050, 44100, 48000
    
    Response:
    - Returns MP3 file for download
    
    Examples:
    ```bash
    # Basic conversion
    curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3
    
    # With custom bitrate
    curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3?bitrate=320k
    
    # With custom sample rate
    curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3?sample_rate=48000
    ```
    """
    try:
        # ตรวจสอบว่ามีไฟล์ upload
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided. Please upload MP4 file with "file" parameter.',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        file = request.files['file']
        
        # ตรวจสอบชื่อไฟล์
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected.',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # ตรวจสอบนามสกุลไฟล์
        filename = file.filename.lower()
        if not filename.endswith('.mp4'):
            return jsonify({
                'success': False,
                'error': f'Invalid file format. Expected .mp4, got .{filename.split(".")[-1]}',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Get parameters
        bitrate = request.args.get('bitrate', '192k')
        sample_rate = request.args.get('sample_rate', '44100', type=int)
        
        # ตรวจสอบ bitrate format
        valid_bitrates = ['128k', '192k', '256k', '320k']
        if bitrate not in valid_bitrates:
            return jsonify({
                'success': False,
                'error': f'Invalid bitrate. Choose from: {", ".join(valid_bitrates)}',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # ตรวจสอบ sample rate
        valid_sample_rates = [22050, 44100, 48000]
        if sample_rate not in valid_sample_rates:
            return jsonify({
                'success': False,
                'error': f'Invalid sample rate. Choose from: {", ".join(map(str, valid_sample_rates))}',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        start_time = datetime.now()
        
        # สร้าง temporary directory
        temp_dir = tempfile.mkdtemp(prefix='mp4_to_mp3_')
        
        try:
            # Save uploaded MP4 file
            mp4_path = os.path.join(temp_dir, 'input.mp4')
            file.save(mp4_path)
            
            # ตรวจสอบขนาดไฟล์
            file_size = os.path.getsize(mp4_path)
            max_size = 500 * 1024 * 1024  # 500 MB
            
            if file_size > max_size:
                return jsonify({
                    'success': False,
                    'error': f'File too large. Maximum size is 500MB, got {file_size / (1024*1024):.2f}MB',
                    'status': 'error',
                    'timestamp': datetime.now().isoformat()
                }), 413
            
        try:
            # Load video and extract audio
            if VideoFileClip is None:
                raise ImportError("moviepy not properly installed")
            
            video = VideoFileClip(mp4_path)
            
            # Get audio
            if video.audio is None:
                return jsonify({
                    'success': False,
                    'error': 'Video has no audio track',
                    'status': 'error',
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            # Output MP3 path
            output_filename = Path(filename).stem + '.mp3'
            mp3_path = os.path.join(temp_dir, 'output.mp3')
            
            # Extract audio
            audio = video.audio
            
            # Write audio to MP3
            audio.write_audiofile(
                mp3_path,
                verbose=False,
                logger=None,
                fps=sample_rate
            )
            
            # Close video
            video.close()
            
            # Check if MP3 was created
            if not os.path.exists(mp3_path):
                return jsonify({
                    'success': False,
                    'error': 'Failed to create MP3 file',
                    'status': 'error',
                    'timestamp': datetime.now().isoformat()
                }), 500
            
            # Get output file size
            output_size = os.path.getsize(mp3_path)
            conversion_time = (datetime.now() - start_time).total_seconds()
            
            print(f"✅ Conversion successful!")
            print(f"   Output: {output_filename} ({output_size / (1024*1024):.2f}MB)")
            print(f"   Time: {conversion_time:.2f}s")
            
            # Send file
            response = send_file(
                mp3_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype='audio/mpeg'
            )
            
            # Set headers
            response.headers['X-Conversion-Time'] = str(conversion_time)
            response.headers['X-Output-Size'] = str(output_size)
            response.headers['X-Bitrate'] = bitrate
            
            # Clean up in background (after response is sent)
            @response.call_on_close
            def cleanup():
                try:
                    shutil.rmtree(temp_dir)
                    print(f"🗑️  Cleaned up temporary files")
                except Exception as e:
                    print(f"⚠️  Error cleaning up: {e}")
            
            return response
            
        except ImportError as e:
            print(f"❌ ImportError: {e}")
            print("   Make sure imageio is installed: pip install imageio")
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return jsonify({
                'success': False,
                'error': 'FFmpeg or imageio not installed. Please install them: pip install imageio[ffmpeg]',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 500
            
        except Exception as e:
            print(f"❌ Conversion error: {e}")
            traceback.print_exc()
            
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return jsonify({
                'success': False,
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in /api/convert/mp4-to-mp3: {error_message}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_message,
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/convert/info', methods=['GET'])
def get_converter_info():
    """
    Get information about the converter API
    
    Returns:
    - Supported formats
    - API endpoints
    - Examples
    """
    return jsonify({
        'success': True,
        'service': 'Media Converter API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/convert/mp4-to-mp3': 'Convert MP4 to MP3 (upload file)',
            'GET /api/convert/info': 'Get converter information'
        },
        'supported_formats': {
            'input': ['mp4', 'avi', 'mov', 'mkv', 'flv', 'webm'],
            'output': ['mp3']
        },
        'parameters': {
            'bitrate': {
                'description': 'Audio bitrate',
                'default': '192k',
                'options': ['128k', '192k', '256k', '320k']
            },
            'sample_rate': {
                'description': 'Audio sample rate (Hz)',
                'default': 44100,
                'options': [22050, 44100, 48000]
            }
        },
        'limits': {
            'max_file_size': '500MB',
            'max_duration': 'unlimited'
        },
        'examples': {
            'basic': 'curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3',
            'high_quality': 'curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3?bitrate=320k',
            'custom_sample_rate': 'curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3?sample_rate=48000'
        },
        'response_headers': {
            'X-Conversion-Time': 'Conversion time in seconds',
            'X-Output-Size': 'Output file size in bytes',
            'X-Bitrate': 'Audio bitrate used'
        },
        'timestamp': datetime.now().isoformat()
    })


# ========================================
# Error Handlers
# ========================================

@app.route('/api/convert/mp4-to-mp3', methods=['GET'])
def convert_mp4_to_mp3_get_help():
    """GET endpoint for /api/convert/mp4-to-mp3 - show help"""
    return jsonify({
        'success': False,
        'error': 'This endpoint requires POST method with file upload',
        'method': 'POST',
        'content_type': 'multipart/form-data',
        'parameters': {
            'file': 'MP4 file to convert (required)',
            'bitrate': 'Audio bitrate (optional, default: 192k)',
            'sample_rate': 'Sample rate in Hz (optional, default: 44100)'
        },
        'example_curl': 'curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3',
        'help_url': '/api/convert/info'
    }), 405


# ========================================
# Error Handlers
# ========================================
# Error Handlers
# ========================================

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
            '/api/film-data-contacts',
            '/api/google-sheets/film-data',
            '/run-time',
            '/N_SaleIncentive_data',
            '/api/clear-cache',
            '/api/facebook-ads-campaigns',
            '/api/google-sheets-data',
            '/api/google-ads',
            '/data_bjh',
            '/api/call-matrix',
            '/api/call-matrix/agent/<agent_id>',
            '/api/call-matrix/time-slot/<time_slot>',
            '/api/call-matrix/log',
            '/api/call-matrix/update',
            '/api/call-matrix/batch-update'
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
