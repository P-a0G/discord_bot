import re

import googleapiclient.discovery
from googleapiclient.errors import HttpError

from modules.utils import read_json


class KeyManager:
    def __init__(self, key_names):
        self.keys = [read_json("./files/tokens.json")[k] for k in key_names]
        self.idx = 0
        self.youtube_clients = [googleapiclient.discovery.build("youtube", "v3", developerKey=key) for key in self.keys]

    def get_key(self):
        self.idx = (self.idx + 1) % len(self.keys)
        return self.youtube_clients[self.idx]


key_manager = KeyManager(["google_tn_net", "google_netcourrier", "google_drotek"])


def execute_request(request_params):
    try:
        youtube = key_manager.get_key()
        response = youtube.search().list(**request_params).execute()
        return response
    except HttpError as e:
        if e.resp.status == 403:
            print("Quota exceeded or permission denied.")
            return {}
        else:
            raise


def execute_request_video(request_params):
    try:
        youtube = key_manager.get_key()
        response = youtube.videos().list(**request_params).execute()
        return response
    except HttpError as e:
        if e.resp.status == 403:
            print("Quota exceeded or permission denied.")
            return {}
        else:
            raise


def get_video_id(url):
    # Regular expression to match video IDs in both URL formats
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def extract_from_url(url):
    video_id = get_video_id(url)

    try:
        youtube = key_manager.get_key()
        response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()
    except HttpError as e:
        if e.resp.status == 403:
            print("Quota exceeded or permission denied.")
            return {}
        else:
            raise
    return response


if __name__ == '__main__':
    response = extract_from_url("https://www.youtube.com/watch?v=IYzSVlTNucs&ab_channel=CLAPTONE")
    print(response)
    print(response["items"][0]["id"])  # id: IYzSVlTNucs
