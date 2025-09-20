from typing_extensions import TypedDict,List, Dict, Any, Annotated, Optional
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.runtime import Runtime
from app.agent_call.external import format_github_request,get_all_commits
from langgraph.checkpoint.memory import MemorySaver
# import request
from psycopg_pool import ConnectionPool
import numpy as np
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
import pandas as pd
import os
from langchain_core.prompts import ChatPromptTemplate
from flask import jsonify,current_app
from langchain.chat_models import init_chat_model
import os
from pydantic import BaseModel,Field
from typing import Optional,List,Set
from langgraph.checkpoint.postgres import PostgresSaver
from app.agent_call.composer import run_compose
from app.agent_call.external import doy_to_date
from app.models  import User,Post
from app import db
# ---- State Definition ----
def add(left, right):
    if right == "__RESET__":
        return []
    left.extend(right)
    return left

def adder(left,right):
    if len(left)==0:
        left.extend(right)
        return left
    df = pd.DataFrame().from_records(left)
    df_updates = pd.DataFrame().from_records(right)
    new_dates = df_updates["date"].unique()

    # Drop old rows that match new dates
    df = df[~df["date"].isin(new_dates)]

    # Append new rows
    df = pd.concat([df, df_updates], ignore_index=True)

    left = df.to_dict(orient='records')
    return left
    

from datetime import datetime
def add_date(day,file):
    file.update({'date':day,'compiled':False})
    return file

class File(BaseModel):
    commit_id:str = Field(description='The id of the particular commit we are using.')
    repo : str = Field(description='The Name of the repository ')
    filename : str = Field(description='The name of the file that changes is being made to')
    Patch : Optional[str] = Field(default=None,description='A list of the key points of the changes made as shown in the patch')

class Repository(BaseModel):
    repository:List[File]


class AgentState(TypedDict):
    repo:str
    user_id:str
    day:str
    formatted_commits:Annotated[List[dict],add]
    extracted_commits:Annotated[List[dict],adder]
    compiled_diary_list:Annotated[List[dict],add]
    # requests: Annotated[list[RequestEntry], add]
    # selected_request: Optional[int] = None



prompt_template = ChatPromptTemplate([('system',
    "You will be given a text string containing the name of a repository, a commit id , a filename on which the changes occurred, this changes could be"
    "addition of a file which is the filename or addition of some line of codes in the file, same for the removal and modification this is according"
    "to. Also we can also get the number of addition,deletion from the no of addition, deletion"
    "A commit message will be specified which describe what commit was made, a brief description about what the commit is about."
    "The patch - is the main information body we will be using to get this information, "
    "Your job is to extract a list of key summary (under 200 characters or less) point of what happened in each patch given for each file. Make it detailed yet concise, that mean it should contain keywords"
    "that can be used to generate a report about the changes that occured in this file. The below is the text string : "
                        ),
    ('human','{text_string}')])

#since formatted has a list of formatted commit with each commit id, we can
#chck if the lenth of data is equal to len of formatted for that repository in the checkpointer


# def receiver_node(state:AgentState):
#     payload = state['commits']
#     formatted = get_all_commits(payload)
#     print('It was at receiver node')
#     # print(formatted)
#     formatted = [item for sublist in formatted for item in sublist]
#     return {'formatted_commits':formatted}

def extraction_node(state:AgentState):
    os.environ["GOOGLE_API_KEY"] = current_app.config['GOOGLE_API_KEY']# 
    llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
    print('could be here \n\n\n\n\n\n')
    # print(state['formatted_commits'])
    df = pd.DataFrame().from_records(state['formatted_commits'])
    day = state['day']
    df_to_extract = df[df['day']==day]
    print(df.head())
    extracted_commits_df = pd.DataFrame().from_records(state.get('extracted_commits',[]))
    if extracted_commits_df.shape[0] > 0:
        df_to_extract = df_to_extract.copy()
        df_to_extract.loc[:,"commit_id"] = df_to_extract["message"].str.split("Commit_id").str[1].str.split(",").str[0].str.strip().str[2:]
        df_to_extract = df_to_extract[~df_to_extract["commit_id"].isin(extracted_commits_df["commit_id"])]
        df_to_extract.drop('commit_id',axis=1,inplace=True)
    temp_message = df_to_extract['message']
    commit_prompt = prompt_template.invoke({'text_string':temp_message.tolist()})#change from state to df slice
    print('Im here\n\n\n\n\n\n')
    structured_llm = llm.with_structured_output(schema=Repository)
    extracted_commit = structured_llm.invoke(commit_prompt)
    extracted_commit = [add_date(day,file) for file in extracted_commit.model_dump()['repository']]
    print('It was at extraction node')
    return {'extracted_commits':extracted_commit}

def compose_node(state:AgentState):
    df = pd.DataFrame().from_records(state['extracted_commits'])
    day = state['day']
    df_unique_date= sorted(df['date'].unique())
    temp_df = df[(df['compiled']==False) and (df['date']==day)]
    print(df['compiled'].value_counts())
    index = df_unique_date.index(day)
    #GET THE SUMMARY OF THE PREVIOUS COMMIT DATE:
    if index !=0:
        compiled_df = pd.DataFrame().from_records(state['compiled_diary_list'])
        backlog_date = df_unique_date[index-1]
        backlog_summary = compiled_df[compiled_df['date']==backlog_date]['summary']
    else:
        backlog_summary = ''
    day_x = len(state.get('compiled_diary_list',[]))+1
    temp_df['file_patch'] = 'FileName : ' + temp_df['filename'] + 'Patch : ' + temp_df['Patch']
    patch = temp_df['file_patch'].tolist()
    result = run_compose(day=day_x,commit_logs=patch,previous_summary=backlog_summary)
    info = {'twitter_thread':result['twitter_thread'],'facebook_post':result['facebook_post'].content,
        'linkedin_post':result['linkedin_post'].content,'summary':result['summary'].content,'repo':state['repo'],
        'date':day}
    username = state['repo'].split('/')[0]
    user_id = User.query.filter_by(username=username).first().id
    id = (info['repo']+day).encode("utf-8").hex()
    print(id)
    year =int(day.split('-')[0])
    dayofyear = int(day.split('-')[1])
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
    df.loc[df['date']==day,'compiled'] = True
    extracted_commits = df.to_dict(orient='records')
    return {'extracted_commits':extracted_commits,'compiled_diary_list':[info]}  # marks it as if an agent updated the state
    

# ---- Graph Definition ----
builder = StateGraph(AgentState)
builder.add_node(extraction_node)
builder.add_node(compose_node)
builder.set_entry_point("extraction_node")
builder.add_edge("extraction_node", "compose_node")
builder.add_edge("compose_node",END)




# i'm going to add a node that accumulate the extracted commit to a particular stuff, then upload it to a postgres db
# then it will reset the extracted_commit state to an empty list
# before each runs, i need it to generate a thread id using the date, so how will it know when to generate a thread id
# it checks if the extracted_commit state is empty


