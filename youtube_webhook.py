from flask import Flask, request
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Constants
HUB_URL = "https://pubsubhubbub.appspot.com/subscribe"
CHANNEL_ID = "UCSvSf_Jz1wz3g8LDJpPbsNg"  # Liquicity Channel ID
TOPIC_URL = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={CHANNEL_ID}"
CALLBACK_URL = "https://your-public-url.com/callback"  # Replace with your public URL


def subscribe_to_channel():
    """Send a subscription request to PubSubHubbub."""
    data = {
        "hub.callback": CALLBACK_URL,
        "hub.mode": "subscribe",
        "hub.topic": TOPIC_URL,
        "hub.verify": "async",
    }
    response = requests.post(HUB_URL, data=data)
    if response.status_code == 202:
        print("Subscription request sent successfully!")
    else:
        print(f"Failed to subscribe: {response.status_code} - {response.text}")


@app.route("/callback", methods=["GET", "POST"])
def callback():
    """Handle PubSubHubbub callbacks."""
    if request.method == "GET":
        # Respond to the verification challenge
        return request.args.get("hub.challenge", ""), 200

    if request.method == "POST":
        # Handle new video notification
        xml_data = request.data
        root = ET.fromstring(xml_data)
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
            video_url = f"https://youtu.be/{video_id}"
            print(f"New video uploaded: {video_url}")
        return "", 204


if __name__ == "__main__":
    # Subscribe to the Liquicity channel
    subscribe_to_channel()
    # Run the Flask app
    app.run(port=5000)
