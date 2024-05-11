import googleapiclient.discovery
from googleapiclient.errors import HttpError
from modules.utils import read_json

# Set your API key
api_key = read_json("./files/tokens.json")["google_debug"]

# Set up the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)


def get_channel_id(channel_username):
    # Request channel information
    channel_info = youtube.channels().list(forUsername=channel_username, part="id").execute()

    if channel_info["pageInfo"]["totalResults"] > 0:
        channel_id = channel_info["items"][0]["id"]
    else:
        channel_info = youtube.channels().list(forUsername=channel_username.strip().replace(" ", ""), part="id").execute()

        if channel_info["pageInfo"]["totalResults"] > 0:
            channel_id = channel_info["items"][0]["id"]

        else:
            channel_id = None

    if channel_id is None:
        search_response = youtube.search().list(
            q=channel_username,
            part="id",
            maxResults=1
        ).execute()

        try:
            channel_id = search_response['items'][0]['id']['channelId']
        except:
            channel_id = None

    return channel_id


def video_id_to_url(video_id):
    return "https://www.youtube.com/watch?v=" + str(video_id)


def get_first_youtube_response_url(search_string):
    # Search for videos
    search_response = youtube.search().list(
        q=search_string,
        part="id",
        maxResults=1
    ).execute()

    # Extract video ID of the first result
    video_id = search_response['items'][0]['id']['videoId']

    # Return the video url
    return video_id_to_url(video_id)


def get_channel_videos(channel_id, first_page=False, filter_by_duration=True, n_max=5000):
    # Request the list of videos from the specified channel
    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=50  # Adjust this as needed, maximum is 50
    )

    response = request.execute()

    # Process the response to extract video details
    videos = []
    for item in response['items']:
        # print("item:", item)
        title = item.get("snippet", {}).get("title")
        video_id = item.get("id", {}).get("videoId")
        if title is not None and video_id is not None:
            video = {
                'title': title,
                'videoId': video_id
            }
            videos.append(video)

    if filter_by_duration:
        return [v for v in videos if is_duration_in_range(
            get_video_duration(
                v.get('videoId', -1)
            )
        )]

    return videos


def get_video_duration(video_id):
    if video_id == -1:
        return 0

    response = youtube.videos().list(
        part="contentDetails",
        id=video_id
    ).execute()

    if not response:
        return 0

    if "items" not in response.keys():
        return 0

    duration = response["items"][0]["contentDetails"]["duration"]

    return duration


def is_duration_in_range(duration_str, min_minutes=2, max_minutes=6):
    if isinstance(duration_str, int):
        duration_str = str(duration_str)

    # Remove "PT" prefix
    duration_str = duration_str[2:]

    # Initialize variables
    hours = 0
    minutes = 0
    seconds = 0

    # Extract hours, minutes, and seconds
    if 'H' in duration_str:
        hours_str, duration_str = duration_str.split('H')
        hours = int(hours_str)
    if 'M' in duration_str:
        minutes_str, duration_str = duration_str.split('M')
        minutes = int(minutes_str)
    if 'S' in duration_str:
        seconds_str = duration_str.split('S')[0]
        seconds = int(seconds_str)

    # Calculate total duration in minutes
    total_minutes = hours * 60 + minutes + seconds / 60

    # Check if duration is within the range
    return min_minutes <= total_minutes <= max_minutes


def get_all_musics_from_channel(channel_id):
    videos_urls = list()
    video_titles = list()

    # Get the list of videos from the channel
    videos = get_channel_videos(channel_id, n_max=50)

    if not videos:
        return [], []
    # Print video information
    for i, video in enumerate(videos):
        try:
            video_title = video['title']
            video_id = video['videoId']
        except:
            continue
        duration = get_video_duration(video_id)

        # getting files between 2 and 6 min
        if is_duration_in_range(duration):
            video_titles.append(video_title)
            videos_urls.append(video_id_to_url(video_id))

    return videos_urls, video_titles


if __name__ == '__main__':
    # # Example usage:
    # channel_id = get_channel_id("Martin Garrix")  # Martin Garrix's channel ID
    #
    # urls, titles = get_all_musics_from_channel(channel_id)
    # if channel_id:
    #     for i in range(len(titles)):
    #         print(i, titles[i], urls[i])

    # channel_id = "UC3ifTl5zKiCAhHIBQYcaTeg"  # proximity?
    #
    # videos = get_channel_videos(channel_id, first_page=True, filter_by_duration=True)
    #
    # for v in videos:
    #     print("video:", v)


    print(get_first_youtube_response_url("Proximity"))

