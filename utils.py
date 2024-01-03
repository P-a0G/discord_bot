import requests
from bs4 import BeautifulSoup
from pytube import YouTube
import urllib.parse
import logging
import os
from mutagen.id3 import APIC, error, TIT2, TPE1
from mutagen.mp3 import MP3
# import eyed3
# from eyed3.id3.frames import ImageFrame

logging.basicConfig(encoding='utf-8', level=logging.INFO)


def is_valid_url(url):
    print("url?", url)
    # Parse the URL using urllib.parse
    parsed_url = urllib.parse.urlparse(url)

    # Check if the scheme and netloc (domain name) are non-empty
    if all([parsed_url.scheme, parsed_url.netloc]):
        logging.info(" > valid url")
        return 1
    else:
        logging.info(" > url not valid")
        return 0


def extract_from_url(url, output_dir=r"musics/", add_tags=False):
    # Step 2: Send an HTTP request to the page
    response = requests.get(url)
    html_content = response.text

    # Step 3: Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Get the video title
    title = soup.find("title").text.strip()

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # getting title of the film and author name from YT video title
    author = None
    if "-" in title:
        author, title = title.split("-")[:2]
        title = title.strip()
        author = author.strip()
    print("author:", author)
    print("title:", title)

    if title.lower() == "youtube":
        title = author.split(" (")[0]

    chars_to_remove = "\\/:*?\"<>|\',"
    for c in chars_to_remove:
        title = title.replace(c, "")
    title = title.replace("- ", "")
    title = title.replace("  ", " ")
    # title = title.replace(" ", "_")
    title = title.strip()
    filename = title + ".mp3"

    yt = YouTube(url)

    # Step 2: Get the audio streams
    try:
        audio_streams = yt.streams.filter(only_audio=True, mime_type="audio/webm")
    except:
        logging.info(f' >> Error trying to get audio_streams')
        audio_streams = None

    if audio_streams:
        best_audio = audio_streams[-1]

        audio_file_path = os.path.join(output_dir, filename)
        best_audio.download(filename=audio_file_path)

        logging.info(f' >> File saved in {audio_file_path}')

        return audio_file_path

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

    yt.streams.filter(only_audio=True)[0].download(output_path=output_dir, filename=filename)

    audio_file_path = os.path.join(output_dir, filename)

    logging.info(f' >> File saved in {os.path.join(output_dir, filename)}')

    image_url = soup.find("meta", property="og:image")["content"]
    print("image url:", image_url)

    # add metadata
    if add_tags:
        add_metadata(audio_file_path, title, author, image_url)  # todo debug
        logging.info(f' >> File saved in {os.path.join(output_dir, filename)} with metadata')

    return audio_file_path


def add_metadata(audio_file_path, music_title, author, image_url):
    # add metadata
    try:
        audio = MP3(audio_file_path)
    except ValueError:
        logging.error("Couldn't add metadata")
        return audio_file_path

    print(audio)
    return

    audio["TIT2"] = TIT2(encoding=3, text=music_title.strip())

    if author is not None:
        # Add the author tag
        audio["TPE1"] = TPE1(encoding=3, text=author.strip())

    # Set the image metadata
    print("image_url:", image_url)
    if image_url is not None:
        response = requests.get(image_url)
        try:
            audio['APIC'] = APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc=u'Cover',
                data=response.content
            )
        except error:
            logging.info("      Didn't get image...")
            pass

    audio.save(v2_version=3)


def get_size(file_pth):
    return round(os.path.getsize(file_pth) / 1048576, 2)


if __name__ == '__main__':
    # music_url = r'https://www.youtube.com/watch?v=bvSVwW4Zomw&list=PL3osQJLUr9gKXtj5zF5g-15vcliM0im0Q&index=26'
    #
    # logging.info(f"Try to extract: {music_url}")
    # if is_valid_url(music_url):
    #     extract_from_url(music_url, add_tags=True)
    # else:
    #     print("invalid_url")

    filename = r"C:\Users\33783\Music\discord_bot_musics\Down_to_Love_ft._Jonathan_Mendelsohn_(Official_Lyric_Video).mp3"
    title = "Down_to_Love_ft._Jonathan_Mendelsohn_(Official_Lyric_Video)"
    author = "Alpha 9"
    image = "https://i.ytimg.com/vi/bvSVwW4Zomw/hqdefault.jpg"
    add_metadata(filename, title, author, image)

