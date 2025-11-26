# 🎬 MP4 to MP3 Converter API

## 📋 สรุป

API สำหรับแปลง MP4 (วิดีโอ) เป็น MP3 (เสียง) ด้วย Python Flask

### ✨ ฟีเจอร์

- ✅ แปลง MP4 → MP3 (extract audio)
- ✅ ปรับแต่ง bitrate (128k, 192k, 256k, 320k)
- ✅ ปรับแต่ง sample rate (22050, 44100, 48000 Hz)
- ✅ Support ไฟล์ขนาดใหญ่ (up to 500MB)
- ✅ Response headers แสดง conversion time และ bitrate
- ✅ Automatic cleanup หลังจากแปลงเสร็จ

---

## 🚀 Installation

### 1. ติดตั้ง Dependencies

```bash
cd python-api
pip install -r requirements.txt
```

**Dependencies ที่เพิ่ม:**

```
moviepy==1.0.3
pydub==0.25.1
imageio==2.33.1
imageio-ffmpeg==0.4.10
```

### 2. ตรวจสอบ System Requirements

**Windows:**

- Python 3.7+
- FFmpeg (ติดตั้งอัตโนมัติผ่าน imageio-ffmpeg)

**macOS:**

```bash
brew install ffmpeg
```

**Linux:**

```bash
sudo apt-get install ffmpeg
```

---

## 📡 API Endpoints

### 1. POST `/api/convert/mp4-to-mp3` - Convert MP4 to MP3

**Method:** POST  
**Content-Type:** multipart/form-data

**Request Parameters:**

| Parameter     | Type    | Required | Default | Description                             |
| ------------- | ------- | -------- | ------- | --------------------------------------- |
| `file`        | File    | ✅       | -       | MP4 file to convert                     |
| `bitrate`     | string  | ❌       | `192k`  | Audio bitrate (128k, 192k, 256k, 320k)  |
| `sample_rate` | integer | ❌       | `44100` | Sample rate in Hz (22050, 44100, 48000) |

**Response (Success - 200):**

- Returns MP3 file as binary data
- Headers:
  - `X-Conversion-Time`: Time taken in seconds
  - `X-Output-Size`: Output file size in bytes
  - `X-Bitrate`: Bitrate used

**Response (Error):**

```json
{
  "success": false,
  "error": "Error message",
  "status": "error",
  "timestamp": "2025-11-26T..."
}
```

**Status Codes:**

- `200 OK` - Conversion successful
- `400 Bad Request` - Invalid input (no file, invalid format, etc.)
- `405 Method Not Allowed` - Wrong HTTP method
- `413 Payload Too Large` - File size exceeds 500MB
- `500 Internal Server Error` - Conversion failed

---

### 2. GET `/api/convert/info` - Get Converter Information

**Method:** GET

**Response:**

```json
{
  "success": true,
  "service": "Media Converter API",
  "version": "1.0.0",
  "endpoints": {...},
  "supported_formats": {...},
  "parameters": {...},
  "limits": {...},
  "examples": {...},
  "timestamp": "2025-11-26T..."
}
```

---

### 3. GET `/api/convert/mp4-to-mp3` - Get Help (GET Method)

**Method:** GET  
**Purpose:** Show help information

**Response:**

```json
{
  "success": false,
  "error": "This endpoint requires POST method with file upload",
  "method": "POST",
  "content_type": "multipart/form-data",
  "parameters": {...},
  "example_curl": "...",
  "help_url": "/api/convert/info"
}
```

---

## 💻 Usage Examples

### 1. Basic Conversion (Python)

```python
import requests

# Upload MP4 file
with open('input.mp4', 'rb') as f:
    files = {'file': ('input.mp4', f, 'video/mp4')}
    response = requests.post(
        'http://localhost:5000/api/convert/mp4-to-mp3',
        files=files
    )

# Save MP3
if response.status_code == 200:
    with open('output.mp3', 'wb') as f:
        f.write(response.content)

    # Check headers
    print(f"Conversion Time: {response.headers['X-Conversion-Time']}s")
    print(f"Output Size: {response.headers['X-Output-Size']} bytes")
    print(f"Bitrate: {response.headers['X-Bitrate']}")
else:
    print(f"Error: {response.json()}")
```

### 2. High Quality (320k) - cURL

```bash
curl -X POST \
  -F "file=@input.mp4" \
  "http://localhost:5000/api/convert/mp4-to-mp3?bitrate=320k" \
  -o output.mp3
```

### 3. Custom Sample Rate (48kHz) - cURL

```bash
curl -X POST \
  -F "file=@input.mp4" \
  "http://localhost:5000/api/convert/mp4-to-mp3?sample_rate=48000" \
  -o output.mp3
```

### 4. Get Converter Info - cURL

```bash
curl "http://localhost:5000/api/convert/info"
```

### 5. JavaScript/Fetch API

```javascript
const formData = new FormData();
formData.append("file", document.getElementById("fileInput").files[0]);

const response = await fetch(
  "http://localhost:5000/api/convert/mp4-to-mp3?bitrate=320k",
  {
    method: "POST",
    body: formData,
  }
);

if (response.ok) {
  const blob = await response.blob();

  // Check headers
  const conversionTime = response.headers.get("X-Conversion-Time");
  const outputSize = response.headers.get("X-Output-Size");
  const bitrate = response.headers.get("X-Bitrate");

  console.log(`Conversion took ${conversionTime}s`);
  console.log(`Output size: ${outputSize} bytes`);
  console.log(`Bitrate: ${bitrate}`);

  // Download file
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "output.mp3";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
} else {
  const error = await response.json();
  console.error("Conversion error:", error.error);
}
```

### 6. React Component Example

```jsx
import React, { useState } from "react";

function MP4ToMP3Converter() {
  const [file, setFile] = useState(null);
  const [bitrate, setBitrate] = useState("192k");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState("");

  const handleConvert = async () => {
    if (!file) {
      setError("Please select a file");
      return;
    }

    setLoading(true);
    setError(null);
    setProgress("Converting...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `http://localhost:5000/api/convert/mp4-to-mp3?bitrate=${bitrate}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error);
      }

      const conversionTime = response.headers.get("X-Conversion-Time");
      const outputSize = response.headers.get("X-Output-Size");

      setProgress(
        `✅ Done! Time: ${conversionTime}s, Size: ${(
          outputSize /
          (1024 * 1024)
        ).toFixed(2)}MB`
      );

      // Download
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name.replace(".mp4", ".mp3");
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
      setProgress("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px", maxWidth: "500px" }}>
      <h2>🎬 MP4 to MP3 Converter</h2>

      <input
        type="file"
        accept=".mp4"
        onChange={(e) => setFile(e.target.files[0])}
        disabled={loading}
      />

      <select
        value={bitrate}
        onChange={(e) => setBitrate(e.target.value)}
        disabled={loading}
      >
        <option value="128k">128k (Low)</option>
        <option value="192k">192k (Standard)</option>
        <option value="256k">256k (High)</option>
        <option value="320k">320k (Maximum)</option>
      </select>

      <button onClick={handleConvert} disabled={loading || !file}>
        {loading ? "Converting..." : "Convert"}
      </button>

      {progress && <p style={{ color: "green" }}>{progress}</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
    </div>
  );
}

export default MP4ToMP3Converter;
```

---

## 🧪 Testing

### 1. Run Test Script

```bash
# เริ่ม Flask server ก่อน
cd python-api
python app.py

# ใน terminal อื่น
cd python-api
python ../test_mp4_to_mp3_api.py
```

### 2. Manual Testing with cURL

```bash
# Get info
curl http://localhost:5000/api/convert/info

# Test without file (error)
curl -X POST http://localhost:5000/api/convert/mp4-to-mp3

# Test with file
curl -X POST -F "file=@test.mp4" http://localhost:5000/api/convert/mp4-to-mp3 -o output.mp3
```

---

## 📊 Performance

### Typical Conversion Times

| Video Duration | Video Size | Conversion Time\* |
| -------------- | ---------- | ----------------- |
| 1 minute       | ~10MB      | 5-10s             |
| 5 minutes      | ~50MB      | 15-20s            |
| 10 minutes     | ~100MB     | 25-35s            |
| 1 hour         | ~600MB     | 2-3 min           |

\*Depends on CPU and file format

### File Size Comparison

| Bitrate | File Size (per minute) |
| ------- | ---------------------- |
| 128k    | ~1MB                   |
| 192k    | ~1.4MB                 |
| 256k    | ~1.9MB                 |
| 320k    | ~2.4MB                 |

---

## 🔧 Configuration

### Environment Variables

ไม่มี environment variables ที่ต้องตั้งค่า (uses defaults)

### Optional: Set Max File Size

แก้ไข `app.py` ที่ `max_size`:

```python
max_size = 500 * 1024 * 1024  # 500 MB (เปลี่ยนตัวเลขได้)
```

---

## ❌ Error Handling

### Common Errors

**1. No file provided**

```json
{
  "success": false,
  "error": "No file provided. Please upload MP4 file with \"file\" parameter.",
  "status": "error"
}
```

**2. Invalid file format**

```json
{
  "success": false,
  "error": "Invalid file format. Expected .mp4, got .avi",
  "status": "error"
}
```

**3. File too large**

```json
{
  "success": false,
  "error": "File too large. Maximum size is 500MB, got 650.50MB",
  "status": "error"
}
```

**4. Video has no audio**

```json
{
  "success": false,
  "error": "Video has no audio track",
  "status": "error"
}
```

**5. FFmpeg not installed**

```json
{
  "success": false,
  "error": "FFmpeg or imageio not installed. Please install them: pip install imageio[ffmpeg]",
  "status": "error"
}
```

---

## 🌐 Deployment

### Railway Deployment

1. **Push code to GitHub**

```bash
git add .
git commit -m "Add MP4 to MP3 converter API"
git push origin main
```

2. **On Railway Dashboard:**

   - API จะ auto-deploy
   - FFmpeg จะติดตั้งอัตโนมัติผ่าน `imageio-ffmpeg`

3. **ทดสอบ:**

```bash
curl -X POST -F "file=@test.mp4" https://your-app.up.railway.app/api/convert/mp4-to-mp3 -o output.mp3
```

### Docker Support

สำหรับ Docker ใช้ `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
```

---

## 📚 API Response Headers

| Header                | Description               | Example                             |
| --------------------- | ------------------------- | ----------------------------------- |
| `X-Conversion-Time`   | Time taken in seconds     | `15.32`                             |
| `X-Output-Size`       | Output file size in bytes | `2097152`                           |
| `X-Bitrate`           | Bitrate used              | `192k`                              |
| `Content-Type`        | MIME type                 | `audio/mpeg`                        |
| `Content-Disposition` | Download filename         | `attachment; filename="output.mp3"` |

---

## 🎯 Use Cases

1. **Audio Extraction**

   - Extract audio from video files
   - Convert videos to podcasts

2. **Format Conversion**

   - Convert MP4 to MP3
   - Extract audio with specific bitrate

3. **Batch Processing**

   - Convert multiple videos
   - Automate audio extraction workflow

4. **Content Management**
   - Extract audio for music libraries
   - Prepare audio for streaming services

---

## ⚠️ Limitations

- **File Size:** Max 500MB (ปรับได้)
- **Input Format:** MP4 (สามารถเพิ่มได้)
- **Output Format:** MP3 (สามารถเพิ่มได้ เช่น WAV, OGG, etc.)
- **Processing Time:** ขึ้นอยู่กับขนาดไฟล์ และ CPU

---

## 🔄 Future Improvements

- [ ] Support for more input formats (AVI, MOV, WebM, etc.)
- [ ] Support for more output formats (WAV, OGG, FLAC, etc.)
- [ ] Batch processing endpoint
- [ ] Progress tracking (WebSocket)
- [ ] Queue system for large files
- [ ] Audio editing (trim, normalize, etc.)

---

## 📞 Support

หากมีปัญหา:

1. ตรวจสอบ FFmpeg ติดตั้งแล้วหรือไม่
2. ดู logs ใน terminal
3. ตรวจสอบ `/api/convert/info` endpoint
4. เรียก `/health` เพื่อตรวจสอบ API status

---

**Version:** 1.0.0  
**Last Updated:** November 26, 2025
