from typing import Union
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from pytube import YouTube
from pydub import AudioSegment
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

app = FastAPI(title="YouTube Download API", description="API to download YouTube videos as MP3")

# Create downloads directory
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

class YouTubeRequest(BaseModel):
    url: HttpUrl
    title: str = None

class DownloadResponse(BaseModel):
    message: str
    filename: str
    download_id: str

def download_youtube_audio(url: str, output_dir: str, download_id: str) -> dict:
    """Download YouTube video as MP3 audio file using pytube"""
    try:
        # Create YouTube object with error handling
        print(f"Attempting to download: {url}")
        yt = YouTube(url)
        
        # Check if video is available
        print(f"Video found: {yt.title}")
        
        # Get video title and sanitize it for filename
        title = yt.title
        sanitized_title = re.sub(r'[<>:"/\\|?*]', '', title)
        
        # Get all available streams for debugging
        all_streams = yt.streams.filter(only_audio=True)
        print(f"Available audio streams: {len(all_streams)}")
        
        # Try to get the best audio stream
        audio_stream = all_streams.order_by('abr').desc().first()
        
        if not audio_stream:
            # Fallback to any audio stream
            audio_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_audio=True).first()
            
        if not audio_stream:
            # Last resort: get any stream and extract audio
            audio_stream = yt.streams.filter(file_extension='mp4').first()
            
        if not audio_stream:
            raise Exception("No suitable audio or video stream found")
        
        print(f"Selected stream: {audio_stream}")
        
        # Download the audio file
        temp_filename = f"{download_id}_temp"
        print(f"Downloading to: {output_dir}/{temp_filename}")
        downloaded_file = audio_stream.download(
            output_path=output_dir,
            filename=temp_filename
        )
        
        print(f"Downloaded file: {downloaded_file}")
        
        # Convert to MP3 using pydub
        mp3_filename = f"{download_id}_{sanitized_title}.mp3"
        mp3_filepath = os.path.join(output_dir, mp3_filename)
        
        # Load the downloaded file and convert to MP3
        print(f"Converting to MP3: {mp3_filepath}")
        audio = AudioSegment.from_file(downloaded_file)
        audio.export(mp3_filepath, format="mp3", bitrate="192k")
        
        # Remove the temporary file
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        
        print(f"Conversion completed: {mp3_filename}")
        
        return {
            'success': True,
            'filename': mp3_filename,
            'title': title,
            'filepath': mp3_filepath
        }
            
    except Exception as e:
        error_msg = str(e)
        print(f"Download error: {error_msg}")
        
        # Provide more specific error messages
        if "HTTP Error 400" in error_msg:
            error_msg = "YouTube video unavailable or restricted. Try a different video."
        elif "Video unavailable" in error_msg:
            error_msg = "This video is not available for download (private, deleted, or geo-restricted)."
        elif "regex" in error_msg.lower():
            error_msg = "YouTube has changed their format. Pytube may need an update."
        
        return {
            'success': False,
            'error': error_msg
        }

@app.get("/")
def read_root():
    return {
        "message": "YouTube Download API", 
        "version": "1.0.0",
        "endpoints": [
            "/download-mp3 - POST: Download YouTube video as MP3",
            "/health - GET: Health check"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "YouTube Download API"}

@app.post("/download-mp3", response_model=DownloadResponse)
async def download_mp3(request: YouTubeRequest):
    """Download a YouTube video as MP3 file"""
    try:
        # Generate unique download ID
        download_id = str(uuid.uuid4())[:8]
        
        # Convert URL to string
        url = str(request.url)
        
        # Validate YouTube URL
        if not any(domain in url for domain in ['youtube.com', 'youtu.be']):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Use thread pool for blocking download operation
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor, 
                download_youtube_audio, 
                url, 
                str(DOWNLOADS_DIR), 
                download_id
            )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=f"Download failed: {result['error']}")
        
        return DownloadResponse(
            message="Download completed successfully",
            filename=result['filename'],
            download_id=download_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/download/{filename}")
async def get_file(filename: str):
    """Retrieve downloaded MP3 file"""
    file_path = DOWNLOADS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type='audio/mpeg',
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.delete("/download/{filename}")
async def delete_file(filename: str):
    """Delete downloaded MP3 file"""
    file_path = DOWNLOADS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        os.remove(file_path)
        return {"message": f"File {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@app.get("/downloads")
async def list_downloads():
    """List all downloaded files"""
    try:
        files = []
        for file in DOWNLOADS_DIR.iterdir():
            if file.is_file() and file.suffix == '.mp3':
                stat = file.stat()
                files.append({
                    "filename": file.name,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": stat.st_ctime
                })
        
        return {"files": files, "total": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

