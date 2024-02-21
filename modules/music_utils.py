import os
import requests
import logging
import urllib.parse
from bs4 import BeautifulSoup
from pytube import YouTube
from moviepy.editor import AudioFileClip
import eyed3
from eyed3.id3.frames import ImageFrame


def extract_with_bs(url):
    # Step 2: Send an HTTP request to the page
    response = requests.get(url)
    html_content = response.text

    # Step 3: Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Get the video title
    title = soup.find("title").text.strip()

    return title, soup


def get_metadata(title):
    # getting title of the film and author name from YT video title
    author = None
    if "-" in title:
        author, title = title.split("-")[:2]
        title = title.strip()
        author = author.strip()
    print("\tauthor:", author)
    print("\ttitle:", title)

    if title.lower() == "youtube":
        title = author.split(" (")[0]

    chars_to_remove = "\\/:*?\"<>|\',"
    for c in chars_to_remove:
        title = title.replace(c, "")
    title = title.replace("- ", "")
    title = title.replace("  ", " ")
    # title = title.replace(" ", "_")
    title = title.strip()
    filename = title + ".webm"

    return title, author, filename


def get_music_with_pytube(url, audio_file_path):
    yt = YouTube(url)

    # Step 2: Get the audio streams
    try:
        audio_streams = yt.streams.filter(only_audio=True, mime_type="audio/webm")
    except:
        logging.info(f' >> Error trying to get audio_streams')
        return 0

    if audio_streams:
        best_audio = audio_streams[-1]

        best_audio.download(filename=audio_file_path)

        logging.info(f' >> File saved in {audio_file_path}')

    return 1


def get_music_with_bs(soup, audio_file_path):
    # Get the download URL for the MP3 file
    download_url = None

    for script in soup.find_all("script"):
        script_text = str(urllib.parse.unquote(script.text)).replace("\\u0026", "&")
        if "audioQualityLabels" in script_text:
            download_url = script_text.split("url\":\"")[1].split("\",\"")[0].replace("\\u0026", "&")
            break

        if "audioquality" in script_text.lower():

            if "flashUrl" not in script_text:
                continue

            download_url = script.text.split("flashUrl\":\"")[1].split("\",\"")[0]
            break

    if download_url is None:
        logging.error("[Error] Didn't find download url")
        return None

    logging.info(f" > download url: {download_url}")

    yt = YouTube(download_url)

    yt.streams.filter(only_audio=True)[0].download(filename=audio_file_path)

    logging.info(f' >> File saved in {audio_file_path}')

    image_url = soup.find("meta", property="og:image")["content"]
    print("image url:", image_url)

    return audio_file_path


def extract_from_url(url, output_dir=r"musics/", add_tags=True):
    title, soup = extract_with_bs(url)

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    title, author, filename = get_metadata(title)

    audio_file_path = os.path.join(output_dir, filename)

    got_music = get_music_with_pytube(url, audio_file_path)

    if not got_music:
        got_music = get_music_with_bs(soup, audio_file_path)

    if not got_music:
        print("[Error] couldn't get the music")
        return None

    try:
        output_path = audio_file_path.replace(".webm", ".mp3")
        convert_webm_to_mp3(audio_file_path, output_path)
        audio_file_path = output_path
    except:
        print("\t[Error] Couldn't convert webm to mp3")
        add_tags = False  # need file to be mp3 to add metadata

    # add metadata
    if add_tags:
        add_metadata(
            file_path=audio_file_path,
            title=title,
            artist=author,
            album=None,  # todo
            year=None,  # todo
            img=None  # image_url  # todo debug
        )
        logging.info(f' >> File saved in {os.path.join(output_dir, filename)} with metadata')
    else:
        print("Didn't add tags")

    return audio_file_path


def convert_webm_to_mp3(input_file, output_file):
    audio = AudioFileClip(input_file)
    audio.write_audiofile(output_file)


def add_metadata(file_path, title, artist, album, year, img=None):
    audiofile = eyed3.load(file_path)

    if audiofile is None:
        # If the automatic format detection fails, try specifying the format
        print("\ttrying to specify format")
        audiofile = eyed3.load(file_path, tag_version=eyed3.id3.ID3_V2_3)

    if audiofile is None:
        print("\tFailed to load audio file.")
        return None

    if audiofile.tag is None:
        audiofile.initTag()

    audiofile.tag.title = title
    audiofile.tag.artist = artist

    if album is not None:
        audiofile.tag.album = album
    if year is not None:
        audiofile.tag.year = year

    audiofile.tag.save()

    print("\t> set tags done")

    if img is not None:
        audiofile.tag.images.set(ImageFrame.FRONT_COVER, img, 'image/jpeg')

        audiofile.tag.save()

        print("\t> set img done")
