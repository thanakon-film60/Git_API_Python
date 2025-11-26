"""
Test script for MP4 to MP3 Converter API
"""
import requests
import os
import json
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_converter_info():
    """Test converter info endpoint"""
    print("=" * 70)
    print("Test 1: Get Converter Info")
    print("=" * 70)
    
    url = f"{BASE_URL}/api/convert/info"
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Converter Info:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.text}")
    
    print()
    return response


def test_no_file():
    """Test MP4 to MP3 without file"""
    print("=" * 70)
    print("Test 2: Convert MP4 to MP3 (No File - Error Case)")
    print("=" * 70)
    
    url = f"{BASE_URL}/api/convert/mp4-to-mp3"
    response = requests.post(url)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        data = response.json()
        print(f"Expected Error: {data.get('error')}")
    else:
        print("Unexpected success")
    
    print()
    return response


def test_get_method():
    """Test GET method (should fail)"""
    print("=" * 70)
    print("Test 3: Convert MP4 to MP3 (GET Method - Should Show Help)")
    print("=" * 70)
    
    url = f"{BASE_URL}/api/convert/mp4-to-mp3"
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 405:
        data = response.json()
        print("\n📋 Help Info:")
        print(f"Method: {data.get('method')}")
        print(f"Content Type: {data.get('content_type')}")
        print(f"Example: {data.get('example_curl')}")
    else:
        print("Unexpected response")
    
    print()
    return response


def create_test_video():
    """Create a simple test MP4 file (1 minute, 30MB)"""
    print("📹 Creating test MP4 file...")
    
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.editor import ColorClip, concatenate_videoclips, AudioFileClip
        import numpy as np
        
        # สร้าง video clip 5 วินาที (สำหรับทดสอบ)
        duration = 5
        
        # Create a simple video (1920x1080, 24fps)
        make_frame = lambda t: np.array([
            [int(255 * np.sin(t)), int(255 * np.cos(t)), 128]
            for _ in range(1920*1080)
        ]).reshape(1080, 1920, 3).astype(np.uint8)
        
        clip = ColorClip(size=(1920, 1080), color=(100, 100, 200)).set_duration(duration)
        
        # Add audio (sine wave)
        import numpy as np
        sr = 44100
        duration_samples = int(sr * duration)
        t = np.linspace(0, duration, duration_samples)
        # 440 Hz sine wave
        audio_array = np.sin(2 * np.pi * 440 * t) * 0.3
        
        from pydub import AudioSegment
        import io
        
        # Create temporary MP4
        test_file = "test_video.mp4"
        clip.write_videofile(test_file, verbose=False, logger=None, fps=24)
        
        print(f"✅ Test video created: {test_file}")
        return test_file
        
    except Exception as e:
        print(f"❌ Error creating test video: {e}")
        print("   You need to create a test MP4 file manually")
        return None


def test_conversion_with_file(video_file):
    """Test MP4 to MP3 conversion with actual file"""
    print("=" * 70)
    print("Test 4: Convert MP4 to MP3 (With File)")
    print("=" * 70)
    
    if not os.path.exists(video_file):
        print(f"❌ Test video not found: {video_file}")
        print(f"   Please provide a valid MP4 file")
        print()
        return None
    
    file_size = os.path.getsize(video_file)
    print(f"📹 Input: {video_file} ({file_size / (1024*1024):.2f}MB)")
    
    url = f"{BASE_URL}/api/convert/mp4-to-mp3"
    
    try:
        with open(video_file, 'rb') as f:
            files = {'file': (video_file, f, 'video/mp4')}
            
            print("⏳ Converting...")
            response = requests.post(url, files=files, timeout=300)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Save MP3
            output_file = "output.mp3"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            output_size = os.path.getsize(output_file)
            
            print(f"\n✅ Conversion successful!")
            print(f"📁 Output: {output_file} ({output_size / (1024*1024):.2f}MB)")
            print(f"   Headers:")
            print(f"   - Conversion Time: {response.headers.get('X-Conversion-Time', 'N/A')}s")
            print(f"   - Bitrate: {response.headers.get('X-Bitrate', 'N/A')}")
        else:
            data = response.json()
            print(f"❌ Error: {data.get('error')}")
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout. Conversion took too long.")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()


def test_conversion_with_custom_bitrate(video_file):
    """Test MP4 to MP3 conversion with custom bitrate"""
    print("=" * 70)
    print("Test 5: Convert MP4 to MP3 (Custom Bitrate: 320k)")
    print("=" * 70)
    
    if not os.path.exists(video_file):
        print(f"❌ Test video not found: {video_file}")
        print()
        return None
    
    url = f"{BASE_URL}/api/convert/mp4-to-mp3"
    params = {
        'bitrate': '320k'
    }
    
    try:
        with open(video_file, 'rb') as f:
            files = {'file': (video_file, f, 'video/mp4')}
            
            print("⏳ Converting with 320k bitrate...")
            response = requests.post(url, files=files, params=params, timeout=300)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            output_file = "output_320k.mp3"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            output_size = os.path.getsize(output_file)
            
            print(f"✅ Conversion successful!")
            print(f"📁 Output: {output_file} ({output_size / (1024*1024):.2f}MB)")
            print(f"   Bitrate: {response.headers.get('X-Bitrate', 'N/A')}")
        else:
            data = response.json()
            print(f"❌ Error: {data.get('error')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()


if __name__ == "__main__":
    print("\n🎬 Testing MP4 to MP3 Converter API\n")
    
    try:
        # Test 1: Get info
        test_converter_info()
        
        # Test 2: No file
        test_no_file()
        
        # Test 3: GET method
        test_get_method()
        
        # Test 4 & 5: With file (if available)
        video_file = "test_video.mp4"
        
        if os.path.exists(video_file):
            test_conversion_with_file(video_file)
            test_conversion_with_custom_bitrate(video_file)
        else:
            print("=" * 70)
            print("⏭️  Skipping file conversion tests")
            print("=" * 70)
            print("To test file conversion, provide a test MP4 file named 'test_video.mp4'")
            print()
        
        print("=" * 70)
        print("✅ All available tests completed!")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server.")
        print("Please make sure the API server is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
