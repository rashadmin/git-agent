import requests
from flask import jsonify,request,current_app

def commit_update(commit):
    commit.update({'message':commit_message,'repo_name':repo.split('/')[-1]})
    message = (f"Repository - {commit['repo_name']}, FileName - {commit['filename']}, Status - {commit['status']}, No of Addition - "
    f"{commit['additions']}, No of Deletion - {commit['deletions']}, Commit Message - {commit['message']}, Patch - {commit.get('patch',None)}")
    return message

def format_github_request(payload):
    
    GITHUB_TOKEN = current_app.config['GITHUB_TOKEN']
    GITHUB_API_URL = "https://api.github.com"
    repo = payload["repository"]["full_name"]   
    after_commit = payload["after"]            
    headers = {"Authorization": f"token {GITHUB_TOKEN}","Accept": "application/vnd.github.v3+json"}
    # Fetch the latest contents of each file
    url = f"{GITHUB_API_URL}/repos/{repo}/commits/{after_commit}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        commit_message = data['commit']['message']
        commits = data['files']#[1]#['patch']
        changed_files = [commit_update(commit) for commit in commits if (commit['filename'].find('/lib/') < 0 and  \
                        commit['filename'].find('/bin/') < 0 and commit['filename'].find('ipynb_checkpoints/') < 0)]
        changed_files = [f'No({index+1}) {commit}' for index,commit in enumerate(changed_files)]
        return changed_files
    else:
        return jsonify({"error": f"Failed to fetch commit: {r.status_code}"}), 500