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


def get_channel_videos(channel_id, first_page=False):
    videos = []
    next_page_token = None

    while True:
        try:
            response = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=100,  # Maximum results per page (can be adjusted)
                order="date",  # Order by date published
                pageToken=next_page_token
            ).execute()

        except HttpError as e:
            error_reason = e._get_reason()
            if "quota" in error_reason.lower():
                print("API quota limit exceeded. Please try again later.")
            else:
                print("An error occurred:", error_reason)
            break

        videos.extend(response['items'])
        next_page_token = response.get('nextPageToken')

        if first_page or not next_page_token:
            break

    return videos


def get_video_duration(video_id):
    response = youtube.videos().list(
        part="contentDetails",
        id=video_id
    ).execute()

    duration = response["items"][0]["contentDetails"]["duration"]
    return duration


def is_duration_in_range(duration_str, min_minutes=2, max_minutes=6):
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
    videos = get_channel_videos(channel_id)

    # Print video information
    for i, video in enumerate(videos):
        try:
            video_title = video['snippet']['title']
            video_id = video['id']['videoId']
        except:
            continue
        duration = get_video_duration(video_id)

        # getting files between 2 and 6 min
        if is_duration_in_range(duration):
            video_titles.append(video_title)
            videos_urls.append(video_id_to_url(video_id))

    return videos_urls, video_titles


if __name__ == '__main__':
    # Example usage:
    channel_id = get_channel_id("Martin Garrix")  # Martin Garrix's channel ID

    urls, titles = get_all_musics_from_channel(channel_id)
    if channel_id:
        for i in range(len(titles)):
            print(i, titles[i], urls[i])


