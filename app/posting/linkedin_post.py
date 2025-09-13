import requests
from flask import jsonify,request,current_app

ACCESS_TOKEN = "AQXPPXII5JJC2RwiVIsAxB72vgTe8CAbpa8A1LLO8CGfYd6TDdWJVSp4xoP0kUgZzXaglR4gXazMEG_lh0zwFqJHd11spmfCY5XaE_w1AH7dmpnfkvKJXFDObHOqlQGNjYL8odpaB8GAzJ5-j9QZ0NxO0EotVc6TpppRWeIAGpnmLoPolJLPIyydEEvJqL01ft1CIzZRHTx4n7jMOITPy4PhHmycIT_EiKz6RU35E3f1L-fe5_fzoGSp-ezKjg_RVI4p6agb8L_zRhNUkgf7bkLKKuJ7jjoW7fmg5_tcv_d4AmjYtODWwTR7TLB9RRZdZ0-u9HbKe1Oi7Kz5h7IHMY5lerm1zg"

# Your LinkedIn URN (unique ID for your profile)
# You can fetch it with: GET https://api.linkedin.com/v2/me
PERSON_URN = "urn:li:person:dYHx70fG9z"



def post_linkedin(status_text):
    ACCESS_TOKEN = current_app.config["ACCESS_TOKEN"]
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    payload = {
        "author": PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": status_text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 201:
        print("✅ Post published successfully!")
    else:
        print(f"❌ Error: {r.status_code} {r.text}")


# --- Run it ---
# post_linkedin("🚀 Just posted to LinkedIn via API using Python + requests! 🔥")
