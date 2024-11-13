import re

import googleapiclient.discovery
from googleapiclient.errors import HttpError

from modules.utils import read_json

api_key = read_json("./files/tokens.json")["google_debug"]
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)


def execute_request(request_params):
    try:
        response = youtube.search().list(**request_params).execute()
        return response
    except HttpError as e:
        if e.resp.status == 403:
            print(e)
            raise PermissionError("Quota exceeded or permission denied.")
        else:
            raise


def execute_request_video(request_params):
    try:
        response = youtube.videos().list(**request_params).execute()
        return response
    except HttpError as e:
        if e.resp.status == 403:
            print(e)
            raise PermissionError("Quota exceeded or permission denied.")
        else:
            raise


def get_video_id(url):
    # Regular expression to match video IDs in both URL formats
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def extract_from_url(url):
    video_id = get_video_id(url)

    response = youtube.videos().list(
        part='snippet',
        id=video_id
    ).execute()

    return response


if __name__ == '__main__':
    response = extract_from_url("https://www.youtube.com/watch?v=IYzSVlTNucs&ab_channel=CLAPTONE")
    print(response)
    print(response["items"][0]["id"])  # id: IYzSVlTNucs
