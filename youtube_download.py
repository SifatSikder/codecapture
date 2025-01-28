import yt_dlp

def download_youtube_video(link, download_path="."):
    try:
        ydl_opts = {
            'outtmpl': f'{download_path}/%(title)s.%(ext)s',  # Save the video with its title
            'format': 'bestvideo+bestaudio/best',  # Download the best video and audio streams
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading from '{link}'...")
            ydl.download([link])
            print("Download completed!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    video_link = "https://www.youtube.com/watch?v=vFW_QfDOvDg"  # Replace with your desired video link
    download_folder = "videos"  # Replace with your desired folder path
    download_youtube_video(video_link, download_folder)
