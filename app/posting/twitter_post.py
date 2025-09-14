import requests
from requests_oauthlib import OAuth1
from flask import jsonify,request,current_app
import time
# --- Step 1: Authenticate with your Twitter/X API credentials ---
# You need Elevated Access from the Twitter/X developer portal



# --- Step 2: Define your thread content ---
thread = [
    "🚀 Starting my Twitter thread on Data Engineering! 🧵",
    "1. Data Pipelines are the backbone of modern analytics.",
    "2. Data Modeling helps structure your warehouse for fast queries.",
    "3. Cloud platforms like AWS, GCP, and Azure make scaling easier.",
    "✨ Thanks for reading! Follow for more data content."
]

# --- Step 3: Post the thread ---
def post_thread(thread):
    X_API_KEY = current_app.config["X_API_KEY"]
    X_API_KEY_SECRET = current_app.config["X_API_KEY_SECRET"]
    X_ACCESS_TOKEN = current_app.config["X_ACCESS_TOKEN"]
    X_ACCESS_TOKEN_SECRET = current_app.config["X_ACCESS_TOKEN_SECRET"]
    auth = OAuth1(X_API_KEY, X_API_KEY_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
    url = "https://api.twitter.com/2/tweets"

    # Post the first tweet
    response = requests.post(url, auth=auth, json={"text": thread[0]})
    response.raise_for_status()
    tweet_id = response.json()["data"]["id"]

    # Post replies (thread)
    for tweet in thread[1:]:
        response = requests.post(url, auth=auth, json={
            "text": tweet,
            "reply": {"in_reply_to_tweet_id": tweet_id}
        })
        response.raise_for_status()
        tweet_id = response.json()["data"]["id"]
        time.sleep(15)

    print("✅ Thread posted successfully!")

# --- Run it ---
# post_thread(thread)
