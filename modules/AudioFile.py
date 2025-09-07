import os
import re

import requests
from bs4 import BeautifulSoup
from moviepy import AudioFileClip
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC
from mutagen.mp3 import MP3
from pytube.exceptions import VideoUnavailable
from pytubefix import YouTube
from pytubefix.cli import on_progress
from yt_dlp import YoutubeDL

from modules.google_utils import execute_request_video
from modules.spotify_utils import SpotifyManager


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
        self.spotify_manager = SpotifyManager()

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

    def get_duration_in_seconds(self) -> float:
        duration = self.duration  # format ISO 8601, e.g. 'PT1H2M3S'
        match = re.match(r'PT((?P<h>\d+)H)?((?P<m>\d+)M)?((?P<s>\d+)S)?', duration)
        hours = int(match.group('h')) if match and match.group('h') else 0
        minutes = int(match.group('m')) if match and match.group('m') else 0
        seconds = int(match.group('s')) if match and match.group('s') else 0
        return hours * 3600 + minutes * 60 + seconds - 1

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
        output_path = os.path.join(os.path.dirname(self.path), self.title + ".mp3")
        audio = AudioFileClip(self.path)
        try:
            audio.write_audiofile(output_path)
        except Exception as e:
            print(f"\t[Error] In convertion to mp3: {e}")
        self._path = output_path

    def add_metadata(self):
        metadata = self.spotify_manager.get_music_metadata(self.title, self.artist)

        audio = MP3(self.path, ID3=ID3)
        audio["TIT2"] = TIT2(encoding=3, text=metadata["title"])
        audio["TPE1"] = TPE1(encoding=3, text=metadata["artists"])
        audio["TALB"] = TALB(encoding=3, text=metadata["album"])

        year = metadata["release_date"].split("-")[0]
        audio["TDRC"] = TDRC(encoding=3, text=year)

        genre_str = "; ".join(metadata["genres"]) if metadata.get("genres") else ""
        audio["TCON"] = TCON(encoding=3, text=genre_str)

        if metadata.get("album_art_url"):
            resp = requests.get(metadata["album_art_url"])
            if resp.status_code == 200:
                audio["APIC"] = APIC(
                    encoding=3,
                    mime=resp.headers.get('Content-Type', 'image/jpeg'),
                    type=3,
                    desc="Cover",
                    data=resp.content
                )

        audio.save()


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
