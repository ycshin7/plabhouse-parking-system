# -*- coding: utf-8 -*-
import json
import os
import streamlit as st
from github import Github, GithubException

def get_github_repo():
    """
    Connects to GitHub using the token from secrets and returns the Repository object.
    It attempts to find the current running repository.
    """
    token = st.secrets.get("GITHUB_TOKEN")
    if not token:
        return None
    
    g = Github(token)
    
    # Try to identify the repo.
    # In a real scenario, we might want to hardcode the repo name or deduce it.
    # For now, let's assume the user puts REPO_NAME in secrets or we search for it.
    # However, since we don't know the repo name easily from inside the container without git,
    # let's ask the user to provide it in secrets, OR we can try to get the user and list repos.
    # A safer bet for this specific workspace is often finding the repo by name if known.
    # Let's try to get 'REPO_NAME' from secrets, otherwise fail gracefully to local storage.
    
    # Try to get 'GITHUB_REPO' from secrets
    repo_name = st.secrets.get("GITHUB_REPO")
    if not repo_name:
        # If GITHUB_REPO is missing, we can't connect.
        return None

    try:
        repo = g.get_repo(repo_name)
        return repo
    except:
        return None

def load_from_github(file_path, default_data):
    """
    Loads JSON data from GitHub. Returns default_data if failed/not found.
    """
    token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO") # Let's use GITHUB_REPO key
    
    if not token or not repo_name:
        return None # Return None to signal "Check local file instead"
        
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(file_path)
        decoded = contents.decoded_content.decode('utf-8')
        return json.loads(decoded)
    except Exception as e:
        print(f"GitHub Load Error: {e}")
        # Return None to signal error, but we need to distinguish between "Not Configured" and "Error"
        # Current logic returns None for both. 
        # Let's start raising invalid configuration as a distinct issue if needed, 
        # but for now, let's keep it simple: None means "Could not load".
        # The calling function should handle "None" as a potential error if configuration exists.
        return None

def save_to_github(file_path, data, commit_message):
    """
    Saves JSON data to GitHub.
    """
    token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO")
    
    if not token or not repo_name:
        return False
        
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # Prepare content
        json_content = json.dumps(data, ensure_ascii=False, indent=4)
        
        try:
            # Check if file exists to update it
            contents = repo.get_contents(file_path)
            repo.update_file(contents.path, commit_message, json_content, contents.sha)
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist, create it
                repo.create_file(file_path, commit_message, json_content)
            else:
                raise e
        return True
    except Exception as e:
        print(f"GitHub Save Error: {e}")
        return False
