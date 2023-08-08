import os, shutil
import speech_recognition as sr 
import moviepy.editor as mp
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pytube import YouTube
from pytube import Stream
from tqdm import tqdm

def writeToFile(text,path="recognized.txt",mode="a"):
  file = open(path,mode)
  file.write(text)
  file.close()

folders = ["./chunks","./converted","./video"]
for folder in folders:
  for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
      if os.path.isfile(file_path) or os.path.islink(file_path):
        os.unlink(file_path)
      elif os.path.isdir(file_path):
        shutil.rmtree(file_path)
    except Exception as e:
      print('Failed to delete %s. Reason: %s' % (file_path, e))

class TqdmForPyTube(tqdm):
  def on_progress(self, stream: Stream, chunk: bytes, bytes_remaining: int):
    self.total = stream.filesize
    bytes_downloaded = self.total - bytes_remaining
    return self.update(bytes_downloaded - self.n)

SAVE_PATH = "./video/"
CHUNK_SIZE = 30

link = input("Enter video link : ")
with TqdmForPyTube(unit='B', unit_scale=True, unit_divisor=1024, delay=2) as t:
  print("Downloading video ...")
  YouTube(link, on_progress_callback=t.on_progress).streams.filter(progressive = True,file_extension = "mp4").first().download(output_path = SAVE_PATH, filename = "test.mp4")
  print("Video downloaded!")

video = mp.VideoFileClip("./video/test.mp4")
num_seconds_video = int(video.duration)
print("The video is {} seconds long\nProcessing :\n".format(num_seconds_video))
l = list(range(0,num_seconds_video+1,CHUNK_SIZE))
l.append(num_seconds_video+1)

writeToFile(text = "Recognized Speech :\n\n", mode = "w")

for i in range(len(l)-1):
  print("Part {} of {} ->".format(i+1,len(l)))
  ffmpeg_extract_subclip("./video/test.mp4", l[i]-2*(l[i]!=0), l[i+1], targetname="chunks/cut{}.mp4".format(i+1))
  clip = mp.VideoFileClip(r"chunks/cut{}.mp4".format(i+1)) 
  clip.audio.write_audiofile(r"converted/converted{}.wav".format(i+1))
  r = sr.Recognizer()
  audio = sr.AudioFile("converted/converted{}.wav".format(i+1))
  try:
    with audio as source:
      r.adjust_for_ambient_noise(source)  
      audio_file = r.record(source)
      result = r.recognize_google(audio_file, language = 'en-US')
      text = str(result) + "\n"
      writeToFile(text)
  except sr.UnknownValueError:
    print("There might be some internal error! Sorry for the inconvinience 😔\n")
  except sr.RequestError as e:
    print("Server down! Sorry for the inconvinience 😔\n")

print("Task Completed!")