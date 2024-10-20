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


def extract_from_url(url):
    video_id = url.split("v=")[-1].split("&")[0]  # Handles standard URL format

    response = youtube.videos().list(
        part='snippet',
        id=video_id
    ).execute()

    return response


if __name__ == '__main__':
    response = extract_from_url("https://www.youtube.com/watch?v=IYzSVlTNucs&ab_channel=CLAPTONE")
    print(response)
    print(response["items"][0]["id"])
