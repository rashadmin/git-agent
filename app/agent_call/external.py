import requests
from flask import jsonify,request,current_app



def format_github_request(payload):
    GITHUB_TOKEN = current_app.config['GITHUB_TOKEN']
    GITHUB_API_URL = "https://api.github.com"
    event = request.headers.get("X-GitHub-Event")
    print(event)
    if event != "push":
        return jsonify({"msg": "Not a push event"}), 200

    repo = payload["repository"]["full_name"]   # e.g. "username/my-repo"
    after_commit = payload["after"]             # latest commit SHA

    changed_files = []
    for commit in payload.get("commits", []):
        changed_files.extend(commit.get("modified", []))
        changed_files.extend(commit.get("added", []))

    file_contents = {}
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    print('yesssssssssssssssss')
    # Fetch the latest contents of each file
    for file_path in changed_files:
        print('checking')
        url = f"{GITHUB_API_URL}/repos/{repo}/contents/{file_path}?ref={after_commit}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            # Content is base64 encoded by GitHub API
            import base64
            content = base64.b64decode(data["content"]).decode("utf-8")
            file_contents[file_path] = content
        else:
            file_contents[file_path] = f"Error fetching file: {r.status_code}"
    return file_contents
