"""
Minimal MP4 to MP3 converter using Flask and FFmpeg
"""

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/api/convert/mp4-to-mp3', methods=['POST'])
def convert_mp4_to_mp3():
    """Convert MP4 video to MP3 audio"""
    try:
        # Check file
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename.lower().endswith('.mp4'):
            return jsonify({'success': False, 'error': 'Only MP4 files accepted'}), 400
        
        # Get parameters
        bitrate = request.args.get('bitrate', '192k')
        sample_rate = request.args.get('sample_rate', '44100')
        
        if bitrate not in ['128k', '192k', '256k', '320k']:
            return jsonify({'success': False, 'error': 'Invalid bitrate'}), 400
        
        # Create temp dir
        temp_dir = tempfile.mkdtemp(prefix='mp4_to_mp3_')
        
        try:
            # Save MP4
            mp4_path = os.path.join(temp_dir, 'input.mp4')
            file.save(mp4_path)
            
            # Check size
            file_size = os.path.getsize(mp4_path)
            if file_size > 500 * 1024 * 1024:  # 500MB
                return jsonify({'success': False, 'error': 'File too large'}), 413
            
            print(f"📹 Converting {file.filename} ({file_size / (1024*1024):.2f}MB)...")
            
            # MP3 output path
            mp3_path = os.path.join(temp_dir, 'output.mp3')
            output_filename = Path(file.filename).stem + '.mp3'
            
            # FFmpeg command
            start_time = datetime.now()
            
            cmd = [
                'ffmpeg',
                '-i', mp4_path,
                '-q:a', '0',
                '-b:a', bitrate,
                '-ar', sample_rate,
                '-y',
                mp3_path
            ]
            
            # Run conversion
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                raise Exception(f"Conversion failed")
            
            if not os.path.exists(mp3_path):
                raise Exception("MP3 file not created")
            
            conversion_time = (datetime.now() - start_time).total_seconds()
            output_size = os.path.getsize(mp3_path)
            
            print(f"✅ Done! ({conversion_time:.1f}s)")
            
            # Send file
            response = send_file(
                mp3_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype='audio/mpeg'
            )
            
            # Add headers
            response.headers['X-Conversion-Time'] = str(conversion_time)
            response.headers['X-Output-Size'] = str(output_size)
            response.headers['X-Bitrate'] = bitrate
            
            # Cleanup after response
            @response.call_on_close
            def cleanup():
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            
            return response
            
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/convert/info', methods=['GET'])
def converter_info():
    """Get converter information"""
    return jsonify({
        'success': True,
        'service': 'MP4 to MP3 Converter',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/convert/mp4-to-mp3': 'Convert MP4 to MP3',
            'GET /api/convert/info': 'Get info'
        },
        'parameters': {
            'bitrate': ['128k', '192k', '256k', '320k'],
            'sample_rate': [22050, 44100, 48000]
        },
        'examples': {
            'basic': 'curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3',
            'high_quality': 'curl -X POST -F "file=@input.mp4" http://localhost:5000/api/convert/mp4-to-mp3?bitrate=320k'
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
