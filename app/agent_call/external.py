import requests
from flask import jsonify,request,current_app
from langchain_core.prompts import ChatPromptTemplate
# from app.agent_call.graph import graph
from langgraph.types import Command

def commit_update(commit,commit_message,repo,commit_id):
    commit.update({'message':commit_message,'repo_name':repo.split('/')[-1],'commit_id':commit_id})
    message = (f"Repository - {commit['repo_name']},Commit_id - {commit['commit_id']}, FileName - {commit['filename']}, Status - {commit['status']}, No of Addition - "
    f"{commit['additions']}, No of Deletion - {commit['deletions']}, Commit Message - {commit['message']}, Patch - {commit.get('patch',None)}")
    return message

def add_date(commit_date,commit):
    return  {'commit_date':commit_date,'message':commit }

def format_github_request(repo,after_commit):
    
    GITHUB_TOKEN = current_app.config['GITHUB_TOKEN']
    GITHUB_API_URL = "https://api.github.com"      
    headers = {"Authorization": f"token {GITHUB_TOKEN}","Accept": "application/vnd.github.v3+json"}
    # Fetch the latest contents of each file
    url = f"{GITHUB_API_URL}/repos/{repo}/commits/{after_commit}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        commit_id = data['sha']
        #COMMIT DATE CREATED
        commit_date=data['commit']['committer']['date']
        commit_message = data['commit']['message']
        commits = data['files']#[1]#['patch']
        changed_files = [commit_update(commit,commit_message,repo,commit_id) for commit in commits if (commit['filename'].find('/lib/') < 0 and  \
                        commit['filename'].find('/bin/') < 0 and commit['filename'].find('ipynb_checkpoints/') < 0)]
        changed_files = [f'No({index+1}) {commit}' for index,commit in enumerate(changed_files)]
        changed_files = [add_date(commit_date,commit) for commit in changed_files]
        return changed_files

    

def get_all_commits(payload):
    repo = payload["repository"]["full_name"]   
    # after_commit = 'c86c53676c1a2490681880f69fcfade90a9b87a3'#payload["after"]            
    GITHUB_API_URL = "https://api.github.com"
    GITHUB_TOKEN = current_app.config['GITHUB_TOKEN']
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    # Fetch the latest contents of each file
    url = f"{GITHUB_API_URL}/repos/{repo}/commits"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
    else:
        data = []
    formatted = [format_github_request(repo,commit['sha']) for commit in data]
    #receiving a nested list of dictionary, flatten  to a list of dictionary
    #convert to data frame, and sort by date, convert to list of dictionary and return as formatted 
    return formatted

def text_composer(thread_id):
    prompt_template = ChatPromptTemplate([('system',
    "You will be given a serialized json string containing a list of dictionary.Each dictionary contain : `a timestamp, a patch which contains description of what happened in the updated code"
    "A filename which is the file the changed occured, the repository the file is located. ` "
    "I want you to create a diary post that will talk about the changes that occured throughout the series of the timeline represented as the timestamp in the serialized json string"
    "E.g A line of code might have been added in a previous timestamp, if the new patch in current timestamp indicates that the line was remove or changed, kindly indicate it, let it be shown as a story timeline"

                        ),
    ('human','{extracted_commit}')])
    pass
    # config = {"configurable": {"thread_id": thread_id}}

    # extracted_commits = graph.get_state(config=config).values['extracted_commits']
    # composed_text = text_composer(extracted_commits)
    # Command(graph,update= {'composed_text':composed_text})