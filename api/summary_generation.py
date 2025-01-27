import whisper
import os
import moviepy.editor as mp
import google.generativeai as genai


def extract_audio(video_path, audio_output="audio.mp3"):
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(audio_output)
    print(f"Audio extracted: {audio_output}")

def transcribe_audio_with_whisper(audio_path):
    model = whisper.load_model("medium")
    result = model.transcribe(audio_path, verbose=True)
    return result['segments']

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def save_transcription_with_timestamps(segments, file_path):
    with open(file_path, 'w') as f:
        for segment in segments:
            start = format_time(segment['start'])
            end = format_time(segment['end'])
            text = segment['text'].strip()
            f.write(f"[{start}-{end}]: {text}\n")

    print(f"Transcription with timestamps saved to {file_path}")

def create_transcription(video_path,transcription_file_path):
  audio_path = "extracted_audio.mp3"
  extract_audio(video_path, audio_path)
  segments = transcribe_audio_with_whisper(audio_path)
  save_transcription_with_timestamps(segments, transcription_file_path)
  if os.path.exists(audio_path): os.remove(audio_path)

def create_summary(transcription_file_path,summary_file_path):
    with open(transcription_file_path, 'r') as file:
        transcribed_text = file.read()
    genai.configure(api_key="AIzaSyDJn8iLuEjbgsbVMog32wdEkWLSELH6-Q4")
    generation_config = {"temperature": 1,"top_p": 0.95,"top_k": 40,"max_output_tokens": 8192,"response_mime_type": "text/plain"}
    model = genai.GenerativeModel(model_name="gemini-1.5-flash",generation_config=generation_config)
    chat_session = model.start_chat(history=[])
    prompt = f"""
    Summarize the following transcribed text of the code tutorial in a concise and clear manner:\n\n{transcribed_text}.
    Each core concept should be summarized accurately.\n\nSummary:""",
    response = chat_session.send_message(prompt)
    with open(summary_file_path, 'w') as summary_file:
        summary_file.write(response.text)
        print(f"Summary saved to {summary_file_path}")

def summarize(video_folder_path):
    video_count = len([f for f in os.listdir(video_folder_path) if os.path.isfile(os.path.join(video_folder_path, f))])
    if video_count > 0 : 
        os.makedirs("transcriptions", exist_ok=True)
        os.makedirs("summaries", exist_ok=True)
    for video in os.listdir(video_folder_path):
        video_path = os.path.join(video_folder_path, video)
        if os.path.isfile(video_path):
            print(f"Found file: {video_path}")
            transcription_file_path = f"transcriptions/{video.split('.')[0]}.txt"
            summary_file_path = f"summaries/{video.split('.')[0]}.txt"
            create_transcription(video_path,transcription_file_path)
            create_summary(transcription_file_path,summary_file_path)

def transcribe(video_folder_path):
    video_count = len([f for f in os.listdir(video_folder_path) if os.path.isfile(os.path.join(video_folder_path, f))])
    if video_count > 0 : 
        os.makedirs("transcriptions", exist_ok=True)
    for video in os.listdir(video_folder_path):
        video_path = os.path.join(video_folder_path, video)
        if os.path.isfile(video_path):
            print(f"Found file: {video_path}")
            transcription_file_path = f"transcriptions/{video.split('.')[0]}.txt"
            create_transcription(video_path,transcription_file_path)
