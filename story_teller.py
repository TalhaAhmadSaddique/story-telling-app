from openai import OpenAI
import requests, os, time
from moviepy.editor import *
import gradio as gr
from dotenv import load_dotenv

os.system("sudo apt install ffmpeg")


load_dotenv()
api_key=os.getenv("OPENAI_KEY")


client = OpenAI(api_key=api_key)

def generate_story(text: str):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a story writing assistant, skilled in writing a short story of 3 to 4 paragraphs and each paragraph have only 2 to 3 lines."},
        {"role": "user", "content": text}
      ]
    )
    response = completion.choices[0].message.content
    return response

def text2speech(text: str):
    audio_filename = "output.wav"
    if os.path.exists(audio_filename):
        os.remove(audio_filename)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    response.stream_to_file(audio_filename)
    while not os.path.exists(audio_filename):
        time.sleep(0.2)

def text2image(text: str):
    image_filename = "output.jpg"
    if os.path.exists(image_filename):
        os.remove(image_filename)
    response = client.images.generate(
      model="dall-e-3",
      prompt=f"Generate a background image for background image of story voice-over app. The story context is given below: \n{text}",
      size="1024x1024",
      quality="standard",
      n=1,
    )
    image_url = response.data[0].url
    response = requests.get(image_url)
    with open(image_filename, "wb") as f:
        f.write(response.content)
    while not os.path.exists(image_filename):
        time.sleep(0.2)

def video_generation(out: int):
    audio_path = "output.wav"
    image_path = "output.jpg"
    video_filename = f"{out}output.mp4"
    if os.path.exists(video_filename):
        os.remove(video_filename)
    audio = AudioFileClip(audio_path)
    image = ImageClip(image_path)
    image = image.set_duration(audio.duration)
    video = CompositeVideoClip([image.set_audio(audio)])
    video.write_videofile(video_filename, fps=24, codec='libx264')
    while not os.path.exists(video_filename):
        time.sleep(0.2)

def concatenate_clips(directory, output_file):
    files = os.listdir(directory)
    video_files = [file for file in files if file.endswith(".mp4")]
    clips = [VideoFileClip(os.path.join(directory, file)) for file in video_files]
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_file, codec='libx264', fps=24)
    for clip in clips:
        clip.close()

def main(context: str):
  story = generate_story(context)
  filtered_sentences = [sentence for sentence in story.split('\n') if sentence.strip()]
  for x, each in enumerate(filtered_sentences):
      text2speech(each)
      text2image(each)
      video_generation(x+1)
      os.system("rm -rf output.wav output.jpg")
  final_video_filename = 'output_video.mp4'
  if os.path.exists(final_video_filename):
      os.remove(final_video_filename)
  concatenate_clips('/content', final_video_filename)
  while not os.path.exists(final_video_filename):
      time.sleep(0.2)
  return final_video_filename


inputs = gr.Textbox(lines=5, label="Enter Text")
outputs = gr.Video(label="Generated Video")
title = "Story Teller App"
description = "Enter some text to generate a video on the given context."
gr.Interface(main, inputs, outputs, title=title, description=description).launch(debug=True)

