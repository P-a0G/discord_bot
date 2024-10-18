import googleapiclient.discovery
from modules.utils import read_json
from pytube import YouTube

# Set your API key
api_key = read_json("./files/tokens.json")["google_debug"]

# Set up the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)


def get_view_nb(video_url):
    yt = YouTube(video_url)
    return yt.views


def get_channel_id(channel_username):
    # Request channel information
    channel_info = youtube.channels().list(forUsername=channel_username, part="id").execute()

    if channel_info["pageInfo"]["totalResults"] > 0:
        channel_id = channel_info["items"][0]["id"]
    else:
        channel_info = youtube.channels().list(forUsername=channel_username.strip().replace(" ", ""),
                                               part="id").execute()

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


def get_channel_videos(artist_name, filter_by_duration=True, n_max=50, last_update: "datetime"=None):
    print(f" >>> Get {artist_name} <<<")
    artist_id = get_channel_id(artist_name)

    if last_update is not None:
        # Request the list of videos from the specified channel
        request = youtube.search().list(
            channelId=artist_id,
            part='snippet',
            maxResults=n_max,  # Adjust this as needed, maximum is 50
            type='video',
            publishedAfter=last_update.isoformat() + 'Z',
        )
    else:
        request = youtube.search().list(
            channelId=artist_id,
            part='snippet',
            maxResults=n_max,  # Adjust this as needed, maximum is 50
            type='video',
        )
    response = request.execute()

    if last_update is None and len(response['items']) == 0:
        print(f" > Didn't get musics with channel id, using q mode {artist_name}")
        request = youtube.search().list(
            q=artist_name,  # for results based on regex
            part='snippet',
            maxResults=n_max,
            type='video'
        )

        response = request.execute()

    # Process the response to extract video details
    videos = []
    for item in response['items']:
        title = item.get("snippet", {}).get("title")
        published_at = item.get("snippet", {}).get("publishedAt")
        video_id = item.get("id", {}).get("videoId")
        view_count = get_view_nb(video_id_to_url(video_id))
        if title is not None and video_id is not None:
            video = {
                'title': title,
                'videoId': video_id,
                'publishedAt': published_at,
                'view_count': view_count
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

    try:
        duration = response["items"][0]["contentDetails"]["duration"]
    except ValueError as e:
        print(f"Error with: {video_id_to_url(video_id)}\n{e}")

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


def get_all_musics_from_channel(artist_name):
    # Get the list of videos from the channel
    videos = get_channel_videos(artist_name, n_max=50)

    if not videos:
        return []
    # Print video information
    for i, video in enumerate(videos):
        if "title" not in video.keys() or "videoId" not in video.keys():
            continue
        video["duration"] = get_video_duration(video['videoId'])

        # getting files between 2 and 6 min
        if is_duration_in_range(video["duration"]):
            video["url"] = video_id_to_url(video['videoId'])

    return videos


if __name__ == '__main__':
    # Example usage:
    channel_id = get_channel_id("davidguetta")  # Martin Garrix's channel ID
    print("channel id:", channel_id)

    videos = get_all_musics_from_channel("davidguetta")
    if channel_id:
        for i, v in enumerate(videos):
            print(i, v["title"], v["view_count"])

    # channel_id = "UC3ifTl5zKiCAhHIBQYcaTeg"  # proximity?
    #
    # videos = get_channel_videos(channel_id, filter_by_duration=True)
    #
    # for v in videos:
    #     print("video:", v)

    pass
