# -*- coding: utf-8 -*-
import json
import os
import streamlit as st
from github import Github, GithubException
def get_github_repo():
    token = st.secrets.get("GITHUB_TOKEN")
    if not token: return None
    g = Github(token)
    repo_name = st.secrets.get("GITHUB_REPO")
    if not repo_name: return None
    try:
        return g.get_repo(repo_name)
    except:
        return None
def load_from_github(file_path, default_data):
    repo = get_github_repo()
    if not repo: return None
    try:
        contents = repo.get_contents(file_path)
        decoded = contents.decoded_content.decode('utf-8')
        return json.loads(decoded)
    except:
        return None
def save_to_github(file_path, data, commit_message):
    repo = get_github_repo()
    if not repo: return False
    try:
        json_content = json.dumps(data, ensure_ascii=False, indent=4)
        try:
            contents = repo.get_contents(file_path)
            repo.update_file(contents.path, commit_message, json_content, contents.sha)
        except GithubException as e:
            if e.status == 404:
                repo.create_file(file_path, commit_message, json_content)
            else:
                raise e
        return True
    except:
        return False
