# YouTube Download API

A FastAPI-based service to download YouTube videos as MP3 audio files.

## Features

- Download YouTube videos as high-quality MP3 files (192 kbps)
- Unique file naming to avoid conflicts
- File management endpoints (list, download, delete)
- Async processing for better performance
- Error handling and validation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg (required for audio conversion by pydub):
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Running the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### `POST /download-mp3`
Download a YouTube video as MP3.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "message": "Download completed successfully",
  "filename": "abc12345_Video Title.mp3",
  "download_id": "abc12345"
}
```

### `GET /download/{filename}`
Download the MP3 file.

### `GET /downloads`
List all downloaded files.

### `DELETE /download/{filename}`
Delete a downloaded file.

### `GET /health`
Health check endpoint.

## Example Usage

### Using curl:
```bash
# Download a video
curl -X POST "http://localhost:8000/download-mp3" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Download the file
curl -O "http://localhost:8000/download/abc12345_Rick Astley - Never Gonna Give You Up.mp3"

# List downloads
curl "http://localhost:8000/downloads"
```

### Using Python requests:
```python
import requests

# Download video
response = requests.post(
    "http://localhost:8000/download-mp3",
    json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
)
print(response.json())

# Get the filename from response
filename = response.json()["filename"]

# Download the file
file_response = requests.get(f"http://localhost:8000/download/{filename}")
with open(filename, "wb") as f:
    f.write(file_response.content)
```

## Notes

- Downloaded files are stored in the `downloads/` directory
- Files are named with a unique ID prefix to avoid conflicts
- Only YouTube URLs (youtube.com and youtu.be) are supported
- The API uses pytube for downloading and pydub for audio conversion
- Files are converted to MP3 format at 192 kbps quality

## Error Handling

The API includes comprehensive error handling for:
- Invalid YouTube URLs
- Download failures
- File not found errors
- Server errors

All errors return appropriate HTTP status codes and descriptive messages. 