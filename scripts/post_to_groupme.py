"""
Uploads the rendered PNG to GroupMe's image service and posts it to the
group via a Bot.

Needs TWO different credentials (both provided by GroupMe, not the same
thing):
  GROUPME_ACCESS_TOKEN  - your personal GroupMe developer access token,
                           shown on the dev.groupme.com dashboard after you
                           log in. Required because image uploads must go
                           through a real account, bots can't upload images
                           themselves.
  GROUPME_BOT_ID         - the Bot ID for the bot you created for this
                           group at dev.groupme.com/bots.
"""
import os
import sys

import requests

IMAGE_SERVICE_URL = "https://image.groupme.com/pictures"
BOT_POST_URL = "https://api.groupme.com/v3/bots/post"


def upload_image(png_path, access_token):
    with open(png_path, "rb") as f:
        r = requests.post(
            IMAGE_SERVICE_URL,
            headers={
                "X-Access-Token": access_token,
                "Content-Type": "image/png",
            },
            data=f.read(),
            timeout=60,
        )
    if r.status_code != 200:
        print("IMAGE UPLOAD FAILED:", r.status_code, r.text, file=sys.stderr)
        r.raise_for_status()
    return r.json()["payload"]["picture_url"]


def post_to_bot(bot_id, text, picture_url=None):
    body = {"bot_id": bot_id, "text": text}
    if picture_url:
        body["attachments"] = [{"type": "image", "url": picture_url}]
    r = requests.post(BOT_POST_URL, json=body, timeout=30)
    if r.status_code not in (200, 202):
        print("BOT POST FAILED:", r.status_code, r.text, file=sys.stderr)
        r.raise_for_status()


def post_leaderboard_image(png_path, caption=""):
    access_token = os.environ["GROUPME_ACCESS_TOKEN"]
    bot_id = os.environ["GROUPME_BOT_ID"]
    picture_url = upload_image(png_path, access_token)
    post_to_bot(bot_id, caption, picture_url)


def post_text(text):
    bot_id = os.environ["GROUPME_BOT_ID"]
    post_to_bot(bot_id, text)
