import requests
from flask import jsonify,request,current_app
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
import pandas as pd
from app.extensions import checkpointer
# from app.agent_call.graph import graph
import os
from langchain.chat_models import init_chat_model


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
                        commit['filename'].find('/bin/') < 0 and commit['filename'].find('ipynb_checkpoints/') < 0 and commit['filename'].find('pycache') < 0)]
        changed_files = [f'No({index+1}) {commit}' for index,commit in enumerate(changed_files)]
        changed_files = [add_date(commit_date,commit) for commit in changed_files]
        return changed_files

    

def get_all_commits(payload):
    from app.agent_call.graph import graph
    repo = payload["repository"]["full_name"]   
    after_commit = payload["after"]            
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
    thread_id = payload['repository']['name'].encode("utf-8").hex()
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config=config).values
    extracted_commit = {i['commit_id'] for i in state['extracted_commits']}
    if len(data)-1==len(extracted_commit):
        formatted = format_github_request(repo,after_commit)
        print
    elif len(data)==len(extracted_commit):
        formatted=[]
    else:
        commit_ids = {commit['sha'] for commit in data}
        commit_ids.difference_update(extracted_commit)
        formatted = [format_github_request(repo,commit) for commit in commit_ids]
    #receiving a nested list of dictionary, flatten  to a list of dictionary
    #convert to data frame, and sort by date, convert to list of dictionary and return as formatted 
    return formatted

def text_composer(thread_id):
    from app.agent_call.graph import graph
    prompt_template = ChatPromptTemplate([('system',
    "You will be given a list of strings.Each string contain : `a patch which contains description of what happened in the updated code"
    "A filename which is the file the changed occured` "
    "I want you to create a diary post that will talk about the changes that occured throughout the series of the timeline represented as the timestamp in the serialized json string"
    "E.g A line of code might have been added in a previous index of the list, if the new patch in current timestamp indicates that the line was remove or changed, kindly indicate it, let it be shown as a story timeline"

                        ),
    ('human','{patch}')])
    os.environ["GOOGLE_API_KEY"] = current_app.config['GOOGLE_API_KEY']# 
    llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config=config).values
    df = pd.DataFrame().from_records(state['extracted_commits'])
    uncompiled_df = df[df['compiled']==False]
    unique_date = uncompiled_df['date'].unique()
    print(df['compiled'].value_counts())
    compiled_diary_list = []
    for date in unique_date:
        temp_df = uncompiled_df[uncompiled_df['date']==date]
        print(temp_df['compiled'].value_counts())
        print(temp_df.head())
        temp_df['file_patch'] = 'FileName : ' + temp_df['filename'] + 'Patch : ' + temp_df['Patch']
        patch = temp_df['file_patch'].tolist()
        patch_prompt = prompt_template.invoke({'patch':patch})#change from state to df slice
        compiled_diary = llm.invoke(patch_prompt)
        df.loc[df['date']==date,'compiled'] = True
        print(temp_df['compiled'].value_counts())
        info = {'compiled_diary':compiled_diary.content,'repo':bytes.fromhex(thread_id).decode("utf-8"),'date':date}
        extracted_commits = df.to_dict(orient='records')
        graph.update_state(
        {"configurable": {"thread_id": thread_id}},
        {'extracted_commits':extracted_commits,'compiled_diary_list':info})  # marks it as if an agent updated the state
        print(info)
        print('\n\n\n\n\n\n\n\n\n\n\n')
    
    # config = {"configurable": {"thread_id": thread_id}}

    # extracted_commits = graph.get_state(config=config).values['extracted_commits']
    # composed_text = text_composer(extracted_commits)
    # Command(graph,update= {'composed_text':composed_text})