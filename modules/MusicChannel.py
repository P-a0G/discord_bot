from modules.AudioFile import AudioFile
from modules.google_utils import execute_request, extract_from_url as extract_from_url_request
from modules.utils import is_duration_in_range


class MusicChannel:
    def __init__(self, name: str, idx: str = None):
        self.name: str = name
        self.idx: str = idx if idx is not None else self.request_id()
        self.n_max_get: int = 25
        self.n_max_update: int = 2

    def request_id(self):
        # Request channel information
        request_params = {
            'q': self.name,
            'part': "id",
            'maxResults': 1,
            'type': "channel"
        }

        search_response = execute_request(request_params)

        channel_id = search_response.get('items', [{}])[0].get('id', {}).get('channelId', None)

        if channel_id is None:
            print(f"Didn't get id for '{self.name}'")

        return channel_id

    def get_videos_from_request(self, response, order_by_views=False):
        # Process the response to extract video details
        files = [AudioFile(item, self.name) for item in response['items']]

        if order_by_views:
            files = sorted(files, key=lambda f: f.view_count, reverse=True)
        return files

    def get_all(self):
        request_params = {
            'channelId': self.idx,
            'part': "snippet",
            'maxResults': self.n_max_get // 2,
            'type': "video",
            'order': "viewCount",
            'videoDuration': 'medium'
        }

        response = execute_request(request_params)

        if response == {}:
            return []

        request_params['videoDuration'] = 'short'

        response['items'] += execute_request(request_params).get('items', [])

        return self.get_videos_from_request(response, order_by_views=True)

    def get_last_update(self, last_update):  # last_update: datetime.datetime
        request_params = {
            'channelId': self.idx,
            'part': 'snippet',
            'maxResults': self.n_max_update,
            'type': 'video',
            'publishedAfter': last_update.isoformat() + 'Z',
            'videoDuration': 'medium'
        }

        response = execute_request(request_params)

        if response == {}:
            return []

        request_params['videoDuration'] = 'short'

        response['items'] += execute_request(request_params).get('items', [])

        return [f for f in self.get_videos_from_request(response) if is_duration_in_range(f.duration)]


def extract_from_url(url):
    response = extract_from_url_request(url)
    if len(response.get("items", [])) == 0:
        print(f"Error couldn't get {url}")
        return AudioFile({}, "")
    audio_file = AudioFile(response["items"][0], "")
    audio_file.download()
    return audio_file


def get_url_from_name(music_name):
    request_params = {
        'q': music_name,
        'part': "snippet",
        'maxResults': 1,
        'type': "video"
    }

    response = execute_request(request_params)

    if len(response.get("items", [])) == 0:
        print(f"Error couldn't get {music_name}")
        return ""
    return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"


if __name__ == '__main__':
    url = ""
    extract_from_url(url)

    MusicChannel("Avicii").get_all()
