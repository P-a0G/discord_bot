from modules.AudioFile import AudioFile
import eyed3


def get_music_returns_correct_data():
    audio_file = AudioFile("test_item", "test_artist")
    result = audio_file.download_audio()
    assert result == 1


def get_metadata_returns_correct_metadata():
    audio_file = AudioFile("test_item", "test_artist")
    audio_file.download_audio()
    audio_file.convert_webm_to_mp3()
    audio_file.add_metadata()
    assert audio_file.title == "test_item"
    assert audio_file.artist == "test_artist"


def get_img_for_music_returns_image():
    audio_file = AudioFile("test_item", "test_artist")
    image_url = audio_file.get_img_url()
    assert image_url is not None


def convert_mp3_converts_successfully():
    audio_file = AudioFile("test_item", "test_artist")
    audio_file.download_audio()
    audio_file.convert_webm_to_mp3()
    assert audio_file.path.endswith(".mp3")


def set_metadata_updates_metadata():
    audio_file = AudioFile("test_item", "test_artist")
    audio_file.download_audio()
    audio_file.convert_webm_to_mp3()
    audio_file.add_metadata()
    audiofile = eyed3.load(audio_file.path)
    assert audiofile.tag.title == "test_item"
    assert audiofile.tag.artist == "test_artist"


def set_img_updates_image():
    audio_file = AudioFile("test_item", "test_artist")
    audio_file.download_audio()
    audio_file.convert_webm_to_mp3()
    audio_file.add_metadata()
    audiofile = eyed3.load(audio_file.path)
    assert audiofile.tag.images[0].image_data is not None

