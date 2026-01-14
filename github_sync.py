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
    except GithubException as e:
        if e.status == 404:
            # File not found
            return None
        print(f"GitHub API Error: {e}")
        return None
    except Exception as e:
        print(f"GitHub Load Error: {e}")
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

def diagnose_github_issue():
    """
    Returns (success: bool, message: str)
    Diagnostic function to find the exact cause of connection failure.
    """
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo_name = st.secrets.get("GITHUB_REPO")
    except:
        return False, "Secrets를 읽을 수 없습니다."

    if not token:
        return False, "GITHUB_TOKEN이 Secrets에 설정되지 않았습니다."
    if not repo_name:
        return False, "GITHUB_REPO가 Secrets에 설정되지 않았습니다."
    
    try:
        g = Github(token)
        # 1. Auth Check (API Call)
        try:
            user = g.get_user()
            login = user.login
        except Exception as e:
            return False, f"Github 로그인 실패 (Token 확인 필요): {e}"
            
        # 2. Repo Check (API Call)
        try:
            repo = g.get_repo(repo_name)
            # Make sure we can actually read something
            repo.get_contents("README.md") # Try to read a standard file or root
        except Exception as e:
            return False, f"저장소 '{repo_name}' 접근/읽기 실패: {e}"
            
        return True, f"Github 연결 성공! (계정: {login}, 저장소: {repo_name})"
        
    except Exception as e:
        return False, f"Github 초기화 오류: {e}"
