import yt_dlp

def download_youtube_video(link, download_path="."):
    try:
        ydl_opts = {
            'outtmpl': f'{download_path}/%(title)s.%(ext)s', 
            'format': 'bestvideo+bestaudio/best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading from '{link}'...")
            ydl.download([link])
            print("Download completed!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    video_link = "https://www.youtube.com/watch?v=vFW_QfDOvDg"
    download_folder = "videos"  
    download_youtube_video(video_link, download_folder)
