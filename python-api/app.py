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
            '/api/film-data': 'Get surgery schedule data from Google Sheets',
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
            '/api/film-data',
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
