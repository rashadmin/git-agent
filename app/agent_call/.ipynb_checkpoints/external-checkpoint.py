import requests
from flask import jsonify,request,current_app



def format_github_request(payload):
    
    GITHUB_TOKEN = current_app.config['GITHUB_TOKEN']
    GITHUB_API_URL = "https://api.github.com"

    repo = payload["repository"]["full_name"]   # e.g. "username/my-repo"
    after_commit = payload["after"]             # latest commit SHA
    changed_files = {}
    for commit in payload.get("commits", []):
        changed_files['modified']=[i for i in commit.get("modified", []) if (i.find('/lib/') < 0 and (i.find('.ipynb_checkpoints')) and  i.find('/bin/') < 0)]
        changed_files['added'] = [i for i in commit.get("added", []) if (i.find('/lib/') < 0 and (i.find('.ipynb_checkpoints')) and  i.find('/bin/') < 0)]
        changed_files['removed'] = [i for i in commit.get("removed", []) if (i.find('/lib/') < 0 and (i.find('.ipynb_checkpoints')) and  i.find('/bin/') < 0)]
    
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    # print('yesssssssssssssssss')
    # Fetch the latest contents of each file
    all_file_contents = {} 
    for key in changed_files.keys():
        file_contents = {}
        for file_path in changed_files[key]:
            print('checking')
            url = f"{GITHUB_API_URL}/repos/{repo}/contents/{file_path}?ref={after_commit}"
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                # print(data)
                # Content is base64 encoded by GitHub API
                import base64
                content = base64.b64decode(data["content"]).decode("utf-8")
                file_contents[file_path] = content
            else:
                file_contents[file_path] = f"Error fetching file: {r.status_code}"
        all_file_contents[key] = file_contents 
    return all_file_contents