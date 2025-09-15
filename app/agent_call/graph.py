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

from app.extensions import get_checkpointer
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
    if df_updates.shape[0]>0:
    # Merge with updates (outer join keeps everything)
        df = df.merge(df_updates, on=["commit_id", "filename"], how="outer", suffixes=("", "_new"))

        # If compiled_new exists, prefer it, else keep old compiled
        df["compiled"] = df["compiled_new"].combine_first(df["compiled"])

    # Drop the helper column
        df = df.drop(columns=[col for col in df.columns if "new" in col])
    left = df.to_dict(orient='records')
    return left
    

from datetime import datetime
def add_date(date,file):
    file.update({'date':date,'compiled':False})
    return file

class File(BaseModel):
    commit_id:str = Field(description='The id of the particular commit we are using.')
    repo : str = Field(description='The Name of the repository ')
    filename : str = Field(description='The name of the file that changes is being made to')
    Patch : Optional[str] = Field(default=None,description='A list of the key points of the changes made as shown in the patch')

class Repository(BaseModel):
    repository:List[File]


class AgentState(TypedDict):
    commits:str
    user_id:str
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
    "Your job is to extract a list of key summary point of what happened in each patch given for each file. Make it detailed yet concise, that mean it should contain keywords"
    "that can be used to generate a report about the changes that occured in this file. The below is the text string : "
                        ),
    ('human','{text_string}')])

#since formatted has a list of formatted commit with each commit id, we can
#chck if the lenth of data is equal to len of formatted for that repository in the checkpointer


def receiver_node(state:AgentState):
    payload = state['commits']
    formatted = get_all_commits(payload)
    print('It was at receiver node')
    # print(formatted)
    formatted = [item for sublist in formatted for item in sublist]
    return {'formatted_commits':formatted}

def extraction_node(state:AgentState):
    os.environ["GOOGLE_API_KEY"] = current_app.config['GOOGLE_API_KEY']# 
    llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
    extracted_commits = []
    print('could be here \n\n\n\n\n\n')
    # print(state['formatted_commits'])
    df = pd.DataFrame().from_records(state['formatted_commits'])
    # if df.shape[0]>
    df["commit_id"] = df["message"].str.split("Commit_id").str[1].str.split(",").str[0].str.strip().str[2:]
    extracted_commits_df = pd.DataFrame().from_records(state.get('extracted_commits',[]))
    if extracted_commits_df.shape[0] > 0:
        df = df[~df["commit_id"].isin(extracted_commits_df["commit_id"])]
    df['commit_date'] = pd.to_datetime(df['commit_date'])
    df.sort_values('commit_date',inplace=True)
    df['dayofyear'] = df['commit_date'].dt.dayofyear.astype(str)
    df['year'] = df['commit_date'].dt.year.astype(str)
    df['day'] = df['year']+'-'+df['dayofyear']
    df.drop(['dayofyear','year'],axis=1,inplace=True)
    unique_commit_date = df['day'].unique()
    for date in unique_commit_date:
        temp = df[df['day']==date]
        temp_message = temp['message']
        # temp_date = temp['commit_date'].dt.dayofyear
        commit_prompt = prompt_template.invoke({'text_string':temp_message.tolist()})#change from state to df slice
        print('Im here\n\n\n\n\n\n')
        print(commit_prompt)
        structured_llm = llm.with_structured_output(schema=Repository)
        extracted_commit = structured_llm.invoke(commit_prompt)
        extracted_commit = [add_date(date,file) for file in extracted_commit.model_dump()['repository']]
        extracted_commits.extend(extracted_commit)
    # extract all the date in formatted using pandas
    # slice through df for each date, using each date run the extract and extend the extracted_commit list
    # a looop start#
    #i'm thinking  a date should be added to make composing text for each day easier for bulk composing
    print('Im now here \n\n\n\n\n\n')
        # a looop end#
    print('It was at extraction node')
    print(extracted_commits)
    return {'extracted_commits':extracted_commits}

# it is in reverseeeeeeeeeeeeeeeeeeeeeeeeeeeeeee for the extracted commit, earliest come last

# ---- Graph Definition ----
builder = StateGraph(AgentState)
builder.add_node(receiver_node)
builder.add_node(extraction_node)
# builder.add_node("responder", responder)
builder.set_entry_point("receiver_node")
builder.add_edge("receiver_node", "extraction_node")
builder.add_edge("extraction_node",END)
checkpointer = get_checkpointer()
graph = builder.compile(checkpointer=checkpointer)
# ---- Graph Factory ----




# i'm going to add a node that accumulate the extracted commit to a particular stuff, then upload it to a postgres db
# then it will reset the extracted_commit state to an empty list
# before each runs, i need it to generate a thread id using the date, so how will it know when to generate a thread id
# it checks if the extracted_commit state is empty