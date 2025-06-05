from pytube import YouTube

try:
    url = 'https://www.youtube.com/watch?v=JP45BsWTqBQ'
    print(f"Testing URL: {url}")
    
    yt = YouTube(url)
    print(f'Title: {yt.title}')
    print(f'Length: {yt.length} seconds')
    
    streams = yt.streams.filter(only_audio=True)
    print(f'Audio streams available: {len(streams)}')
    
    if streams:
        best_stream = streams.order_by('abr').desc().first()
        print(f'Best audio stream: {best_stream}')
    else:
        print('No audio streams found')
        
    # Try alternative streams
    all_streams = yt.streams.filter(file_extension='mp4')
    print(f'All MP4 streams: {len(all_streams)}')
    
except Exception as e:
    print(f'Error: {e}')
    print(f'Error type: {type(e).__name__}') 