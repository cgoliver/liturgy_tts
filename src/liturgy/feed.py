import boto3
from feedgen.feed import FeedGenerator
import os
import wave
from datetime import timedelta

# DigitalOcean Spaces credentials
SPACE_NAME = "liturgy"
REGION = "nyc3"
ENDPOINT_URL = f"https://{SPACE_NAME}.{REGION}.digitaloceanspaces.com"
ACCESS_KEY = open("SPACES_ACCESS.txt").readline().strip()
SECRET_KEY = open("SPACES_SECRET.txt").readline().strip()

# Podcast details
FEED_URL = "https://{SPACE_NAME}.{REGION}.digitaloceanspaces.com/liturgy.xml"
LOCAL_FEED_FILE = "liturgy.xml"
BUCKET_BASE_URL = f"https://{SPACE_NAME}.{REGION}.digitaloceanspaces.com"

# Initialize Spaces client
session = boto3.session.Session()
client = session.client(
    "s3",
    region_name=REGION,
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)


def get_wav_duration_hms(file_path):
    with wave.open(file_path, "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration_seconds = int(frames / float(rate))
        duration_hms = str(timedelta(seconds=duration_seconds))
        return duration_hms


def upload_episode(file_path):
    """Upload an episode to DigitalOcean Space."""
    file_name = os.path.basename(file_path)
    client.upload_file(file_path, SPACE_NAME, file_name, ExtraArgs={"ContentType": "audio/wav"})
    return f"{BUCKET_BASE_URL}/{file_name}"


def update_feed(title, description, episode_url, duration):
    """Update the podcast feed with a new episode."""
    # Load or create the podcast feed
    fg = FeedGenerator()
    if os.path.exists(LOCAL_FEED_FILE):
        fg.parse(LOCAL_FEED_FILE)
    else:
        # Initialize a new feed
        fg.id(FEED_URL)
        fg.title("Liturgy of the Hours")
        fg.author({"name": "Carlos Oliver", "email": "c.gqq9t@passmail.net"})
        fg.link(href=FEED_URL, rel="self")
        fg.description("Liturgy of the Hours.")
        fg.language("en")
        fg.load_extension("podcast")
        fg.podcast.itunes_author("Carlos Oliver")
        fg.podcast.itunes_image(f"{BUCKET_BASE_URL}/podcast_logo.jpg")

    # Add the new episode
    episode = fg.add_entry()
    episode.id(episode_url)
    episode.title(title)
    episode.description(description)
    episode.enclosure(episode_url, 12345678, "audio/mpeg")
    episode.podcast.itunes_duration(duration)

    # Save the feed locally and upload it
    fg.rss_file(LOCAL_FEED_FILE)
    client.upload_file(
        LOCAL_FEED_FILE, SPACE_NAME, os.path.basename(LOCAL_FEED_FILE), ExtraArgs={"ContentType": "application/rss+xml"}
    )


def main():
    # Upload new episode
    episode_path = "episodes/26.11.2024_vespers.wav"
    episode_url = upload_episode(episode_path)
    print(f"Uploaded episode to {episode_url}")

    # Update feed
    update_feed(
        title="26.11.24: Vespers",
        description="Vespers.",
        episode_url=episode_url,
        duration=get_wav_duration_hms(episode_path),
    )
    print("Podcast feed updated!")


if __name__ == "__main__":
    main()
