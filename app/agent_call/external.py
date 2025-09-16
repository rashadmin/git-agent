import requests
from flask import jsonify,request,current_app
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
import pandas as pd
# from app.agent_call.graph import graph
import os
from app import db
from langchain.chat_models import init_chat_model
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import ChatPromptTemplate
import time
from app.models import Post,User
from app.agent_call.composer import run_compose
from datetime import datetime,timedelta

def doy_to_date(year: int, doy: int):
    # January 1 of that year
    start = datetime(year, 1, 1)
    # Add (doy - 1) days
    date = start + timedelta(days=doy - 1)
    return date

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
        commit_message = data['commit']['author']['date']
        commits = data['files']#[1]#['patch']
        changed_files = [commit_update(commit,commit_message,repo,commit_id) for commit in commits if (commit['filename'].find('/lib/') < 0 and commit['filename'].find('requirements.txt') < 0 and \
                        commit['filename'].find('/bin/') < 0 and commit['filename'].find('ipynb_checkpoints/') < 0 and commit['filename'].find('pycache') < 0 and commit['filename'].find('migrations') < 0)]
        changed_files = [f'No({index+1}) {commit}' for index,commit in enumerate(changed_files)]
        changed_files = [add_date(commit_date,commit) for commit in changed_files]
        return changed_files

    

def get_all_commits(payload):
    from app.extensions import graph_context
    repo = payload["repository"]["full_name"]   
    after_commit = payload["after"]            
    GITHUB_API_URL = "https://api.github.com"
    GITHUB_TOKEN = current_app.config['GITHUB_TOKEN']
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    page = 1
    data =[]
    while True:
        url = f"{GITHUB_API_URL}/repos/{repo}/commits?per_page=100&page={page}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url,headers=headers)

        if response.status_code!=200:
            break
        datum = response.json()
        if not datum:  # stop when no more commits
            break

        data.extend(datum)
        page += 1
    # url = f"{GITHUB_API_URL}/repos/{repo}/commits"

    thread_id = payload['repository']['full_name'].encode("utf-8").hex()
    config = {"configurable": {"thread_id": thread_id}}
    DB_URI = current_app.config['SQLALCHEMY_DATABASE_URI']
    with graph_context() as graph:
        state = graph.get_state(config=config).values
    df = pd.DataFrame().from_records(state.get('formatted_commits',[]))
    if df.shape[0] > 0:
        df["commit_id"] = df["message"].str.split("Commit_id").str[1].str.split(",").str[0].str.strip().str[2:]
        commit_idx = df['commit_id'].unique()
    else:
        commit_idx = []
    extracted_commit = {i.get('commit_id') for i in state.get('extracted_commits',[])}
    if len(data) == len(commit_idx):
        formatted=[]
    elif len(data)>len(commit_idx):
        formatted_commit = {commit for commit in commit_idx}
        commit_ids = {commit['sha'] for commit in data}
        commit_ids.difference_update(formatted_commit)
        print(commit_ids)
        formatted = [format_github_request(repo,commit) for commit in commit_ids]
    elif len(data)==len(extracted_commit):
        formatted=[]
    else:
        commit_ids = {commit['sha'] for commit in data}
        commit_ids.difference_update(extracted_commit)
        print(commit_ids)
        formatted = [format_github_request(repo,commit) for commit in commit_ids]
    #receiving a nested list of dictionary, flatten  to a list of dictionary
    #convert to data frame, and sort by date, convert to list of dictionary and return as formatted 
    return formatted

def text_composer(thread_id):
    from app.extensions import graph_context
    config = {"configurable": {"thread_id": thread_id}}
    DB_URI = current_app.config['SQLALCHEMY_DATABASE_URI']
    with graph_context() as graph:
        state = graph.get_state(config=config).values
    
    df = pd.DataFrame().from_records(state['extracted_commits'])
    df_unique_date= sorted(df['date'].unique())
    uncompiled_df = df[df['compiled']==False]
    unique_date = uncompiled_df['date'].unique()
    print(df['compiled'].value_counts())
    for date in sorted(unique_date):
        DB_URI = current_app.config['SQLALCHEMY_DATABASE_URI']
        with graph_context() as graph:
            state = graph.get_state(config=config).values
        
        index = df_unique_date.index(date)
        #GET THE SUMMARY OF THE PREVIOUS COMMIT DATE:
        if index !=0:
            compiled_df = pd.DataFrame().from_records(state['compiled_diary_list'])
            backlog_date = df_unique_date[index-1]
            backlog_summary = compiled_df[compiled_df['date']==backlog_date]['summary']
        else:
            backlog_summary = ''
        temp_df = uncompiled_df[uncompiled_df['date']==date]
        day = len(state.get('compiled_diary_list',[]))+1
        temp_df['file_patch'] = 'FileName : ' + temp_df['filename'] + 'Patch : ' + temp_df['Patch']
        patch = temp_df['file_patch'].tolist()
        result = run_compose(day=day,commit_logs=patch,previous_summary=backlog_summary)
        info = {'twitter_thread':result['twitter_thread'],'facebook_post':result['facebook_post'].content,
         'linkedin_post':result['linkedin_post'].content,'summary':result['summary'].content,'repo':bytes.fromhex(thread_id).decode("utf-8"),
         'date':date}
        df.loc[df['date']==date,'compiled'] = True
        extracted_commits = df.to_dict(orient='records')
        DB_URI = current_app.config['SQLALCHEMY_DATABASE_URI']
        with graph_context() as graph:
            graph.update_state(
            {"configurable": {"thread_id": thread_id}},
            {'extracted_commits':extracted_commits,'compiled_diary_list':[info]})  # marks it as if an agent updated the state
        
        username = state['user_id']
        user_id = User.query.filter_by(username=username).first().id
        id = (username+info['repo']+date).encode("utf-8").hex()
        year =int(date.split('-')[0])
        dayofyear = int(date.split('-')[1])
        date_committed = doy_to_date(year,dayofyear)
        info.update({'date_committed':date_committed,'user_id':user_id,'id':id})
        existing = db.session.get(Post, id)
        if existing is None:
            post = Post()
            post.from_dict(info)
            db.session.add(post)
        else:
            existing.from_dict(info)
        db.session.commit()
        print(info)
        print('\n\n\n\n\n\n\n\n\n\n\n')  
      


    #use githubname as username



    # config = {"configurable": {"thread_id": thread_id}}

    # extracted_commits = graph.get_state(config=config).values['extracted_commits']
    # composed_text = text_composer(extracted_commits)
    # Command(graph,update= {'composed_text':composed_text})

