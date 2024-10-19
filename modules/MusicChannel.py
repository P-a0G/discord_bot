from modules.google_utils import execute_request, extract_from_url as extract_from_url_request
from modules.AudioFile import AudioFile
from modules.utils import is_duration_in_range


class MusicChannel:
    def __init__(self, name: str):
        self.name: str = name
        self.idx: str = self.request_id()
        self.n_max_get: int = 50
        self.n_max_update: int = 10

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
            'maxResults': self.n_max_get,
            'type': "video"
        }

        response = execute_request(request_params)

        return self.get_videos_from_request(response, order_by_views=True)

    def get_last_update(self, last_update: "datetime"):
        request_params = {
            'channelId': self.idx,
            'part': 'snippet',
            'maxResults': self.n_max_update,
            'type': 'video',
            'publishedAfter': last_update.isoformat() + 'Z',
            'videoDuration': 'short'
        }

        response = execute_request(request_params)

        files = [f for f in self.get_videos_from_request(response) if is_duration_in_range(f.duration)]

        request_params['videoDuration'] = 'medium'

        response = execute_request(request_params)

        files += [f for f in self.get_videos_from_request(response) if is_duration_in_range(f.duration)]

        return files


def extract_from_url(url):
    audio_file = AudioFile(extract_from_url_request(url)["items"][0], "")
    return audio_file

