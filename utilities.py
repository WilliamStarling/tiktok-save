import os
import json
import time
from datetime import datetime

def videos_to_check(videos, location, check_failures):
    """Get a subset of all videos to actually check."""

    existing_ids = get_existing_ids(location)
    failed_ids = get_failed_ids(location)
    
    if check_failures:
        # Only attempt to download previously failed videos
        return [
            v for v in videos if video_url_to_id(v.get("Link", v.get("VideoLink"))) in failed_ids
        ]
    else:
        # Download new videos, skipping both existing and failed ones
        return [
            v for v in videos if video_url_to_id(v.get("Link", v.get("VideoLink"))) not in existing_ids
            and video_url_to_id(v.get("Link", v.get("VideoLink"))) not in failed_ids
        ]


def get_existing_ids(location):
    """Gets the video IDs already present in a directory."""

    files = os.listdir(location)
    return [f.split(".")[0].split("_")[1] for f in files if f.endswith(".mp4")]


def get_failed_ids(location):
    """Gets the video IDs of previously failed videos."""
    try:
        with open(os.path.join(location, "logs", "download_failures.json"), "r") as f:
            return list(json.load(f).keys())
    except FileNotFoundError:
        return []


def date_to_timestamp(time):
    """Converts a string datetime to a UTC timestamp."""

    dt = datetime.strptime(f"{time}Z", "%Y-%m-%d %H:%M:%S%z")
    return int(datetime.timestamp(dt))


def video_url_to_id(url):
    """Converts a TikTok URL to the relevant ID."""

    return url.split("/")[-2]


def save_files(location, tiktok_dict, tiktok_data, timestamp, tiktok_id):
    """Saves the two files to disk."""

    dt_string = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%dT%H-%M-%S")
    name = tiktok_id
    
    # Create main location directory if it doesn't exist
    os.makedirs(location, exist_ok=True)
    
    # Save video file in the main location
    with open(os.path.join(location, f"{name}.mp4"), "wb") as f:
        f.write(tiktok_data)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(location, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Save JSON file in the logs directory
    with open(os.path.join(logs_dir, f"{name}.json"), "w") as f:
        json.dump(tiktok_dict, f, indent=4)


def record_failure(tiktok_id, error_message, location):
    """Make a note that a certain video can't be downloaded."""

    file_location = os.path.join(location, "failures.json")
    if os.path.exists(file_location):
        with open(file_location) as f:
            failures = json.load(f)
    else:
        failures = {}
    failures[tiktok_id] = [time.time(), error_message]
    with open(file_location, "w") as f:
        json.dump(failures, f, indent=4)


def remove_failure(tiktok_id, location):
    """Remove a failure record."""

    file_location = os.path.join(location, "failures.json")
    with open(file_location) as f:
        failures = json.load(f)
        with open(file_location, "w") as f:
            json.dump({
                k: v for k, v in failures.items() if k != tiktok_id
            }, f, indent=4)