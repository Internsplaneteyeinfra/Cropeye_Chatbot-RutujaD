# app/domain/fertilizer/video_resource.py

import json
from pathlib import Path

VIDEO_PATH = Path(__file__).parent / "videos.json"

if not VIDEO_PATH.exists():
    raise FileNotFoundError("videos.json not found")


def get_fertilizer_videos():
    with open(VIDEO_PATH, encoding="utf-8") as f:
        data = json.load(f)

    return data.get("videos", [])
