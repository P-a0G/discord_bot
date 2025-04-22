import os

import eyed3
import requests
from bs4 import BeautifulSoup
from eyed3.id3.frames import ImageFrame
from moviepy.editor import AudioFileClip
from pytube.exceptions import VideoUnavailable
from pytubefix import YouTube
from pytubefix.cli import on_progress
from yt_dlp import YoutubeDL

from modules.google_utils import execute_request_video


class AudioFile:
    def __init__(self, item, artist: str, output_dir=r"musics/"):
        # todo add logger
        self.idx = item.get("id") if isinstance(item.get("id"), str) else item.get("id", {}).get("videoId")
        self.url = "https://www.youtube.com/watch?v=" + str(self.idx)
        self.title = self.convert_title(item.get("snippet", {}).get("title", "Unknown"))
        self.year = int((item.get("snippet", {}).get("publishedAt", "0000"))[:4])
        self.artist = artist if artist else item.get('snippet', {}).get('channelTitle', None)
        self.image_url = self.get_img_url() or item.get('snippet', {}).get('thumbnails', {}).get('default', {}).get(
            'url', None)
        self.output_dir = output_dir
        self._path = None
        self._size = 0
        self._album = None
        self._image = None
        self._duration = None
        self._view_count = None if "statistics" not in item else int(item.get("statistics", {}).get("viewCount", None))
        self.yt = YouTube(self.url, on_progress_callback=on_progress) if self.idx is not None else None

    def __repr__(self):
        return f"AudioFile(title='{self.title}', artist='{self.artist}', album='{self.album}', year={self.year})"

    @staticmethod
    def convert_title(title):
        if title is None:
            return None
        chars_to_remove = "\\/:*?\"<>|\',"
        for c in chars_to_remove:
            title = title.replace(c, "")
        title = title.replace("- ", "")
        title = title.replace("  ", " ")
        # title = title.replace(" ", "_")
        title = title.replace("&amp;", "&")
        title = title.strip()
        return title

    @property
    def view_count(self):
        if self._view_count is None:
            request_params = {
                'part': "statistics",
                'id': self.idx
            }
            try:
                response = execute_request_video(request_params)

                self._view_count = int(response['items'][0]['statistics']['viewCount'])
            except Exception:
                self._view_count = 0
                print("\t[Error] Couldn't get view count")
        return self._view_count

    @property
    def duration(self):
        if self._duration is None:
            request_params = {
                'part': "contentDetails",
                'id': self.idx
            }
            response = execute_request_video(request_params)

            self._duration = response.get('items', [{}])[0].get('contentDetails', {}).get('duration', 'PT0S')
            if self._duration == 'PT0S':
                print("\t[Error] Couldn't get duration", self.url)

        return self._duration

    @property
    def album(self):
        # todo try to get album from title
        if self._album is None:
            self._album = self.artist
        return self._album

    def get_img_url(self):
        if self.idx is None:
            return None
        response = requests.get(self.url)
        if response.status_code != 200:
            print("\t\tDidn't get high quality image")
            return None
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")
        image_url = soup.find("meta", property="og:image")["content"]

        return image_url

    @property
    def image(self):
        if self._image is None:
            response = requests.get(self.image_url)
            if response.status_code != 200:
                print("Failed to download image")
            else:
                self._image = response.content
        return self._image

    @property
    def size(self):
        if self._size == 0:
            if not os.path.exists(self.path):
                return 0
            self._size = round(os.path.getsize(self.path) / 1048576, 2)
        return self._size

    @property
    def path(self):
        if self._path is None and self.idx is not None:
            self.download(output_dir=self.output_dir)
        return self._path

    def download_audio(self, output_dir=r"musics/"):
        try:
            options = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_dir, self.title),
            }

            with YoutubeDL(options) as ydl:
                ydl.download([self.url])
        except VideoUnavailable:
            print(f"Video {self.url} is unavailable.")
            return 0
        except Exception as e:
            print(f' >> Error trying to get audio_streams: {e} url: {self.url}')
            return 0

        if os.path.exists(os.path.join(output_dir, self.title)):
            print(' > ?Had no extension, renaming to .webm')
            os.rename(
                os.path.join(output_dir, self.title),
                os.path.join(output_dir, self.title + ".webm")
            )

        if os.path.exists(os.path.join(output_dir, self.title + ".mp3")):
            self._path = os.path.join(output_dir, self.title + ".mp3")
        elif os.path.exists(os.path.join(output_dir, self.title + ".webm")):
            self._path = os.path.join(output_dir, self.title + ".webm")
        elif os.path.exists(os.path.join(output_dir, self.title + ".m4a")):
            self._path = os.path.join(output_dir, self.title + ".m4a")
        else:
            print(f' >> Error getting file extension: url: {self.url} title: {self.title}')
            self._path = None
            return 0

        print(f' >> File saved in {self._path}')

        return 1

    def convert_audio_to_mp3(self, extension=".webm"):
        output_path = self.path.replace(extension, ".mp3")
        audio = AudioFileClip(self.path)
        audio.write_audiofile(output_path)
        self._path = output_path

    def add_metadata(self):
        audiofile = eyed3.load(self.path)
        if audiofile is None:
            # If the automatic format detection fails, try specifying the format
            print("\tTrying to specify format")
            audiofile = eyed3.load(self.path, tag_version=eyed3.id3.ID3_V2_3)

        if audiofile is None:
            print("\t[Error] Failed to load audio file.")
            return

        if audiofile.tag is None:
            audiofile.initTag()

        audiofile.tag.title = self.title
        audiofile.tag.artist = self.artist
        audiofile.tag.album = self.album
        audiofile.tag.year = self.year
        audiofile.tag.images.set(ImageFrame.FRONT_COVER, self.image, "image/jpeg")
        audiofile.tag.save()

    def add_to_history(self, history_pth="files/history.csv"):
        if os.path.exists(history_pth):
            with open(history_pth, "a", encoding="utf-8") as f:
                f.write(";".join([str(e) for e in [self.title, self.artist, self.album, self.year, self.image is None, self.url]]) + "\n")

    def download(self, output_dir=r"musics/", add_tags=True):
        got_music = self.download_audio()

        if not got_music:
            print("[Error] couldn't get the music")
            return None

        if not self._path.endswith(".mp3"):
            try:
                self.convert_audio_to_mp3(extension="." + self._path.split(".")[-1])
            except Exception as e:
                print(e)
                print("\t[Error] Couldn't convert webm to mp3")
                print("Didn't add tags")
                add_tags = False  # need file to be mp3 to add metadata

        if add_tags:
            self.add_metadata()
            print(f' >> File saved in {os.path.join(output_dir, self.path)} with metadata')
        else:
            print("Didn't add tags")

        self.add_to_history()

        return self.path

    def delete(self):
        if os.path.exists(self.path):
            os.remove(self.path)

        webm_path = self.path.replace(".mp3", ".webm")
        if os.path.exists(webm_path):
            os.remove(webm_path)

        m4a_path = self.path.replace(".mp3", ".m4a")
        if os.path.exists(m4a_path):
            os.remove(m4a_path)

        self._path = None


if __name__ == '__main__':
    idx = "IYzSVlTNucs"
    request_params = {
        'part': "snippet, statistics",
        'id': idx
    }
    response = execute_request_video(request_params)

    print(response)
