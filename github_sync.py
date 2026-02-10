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
        if e.status == 401 or e.status == 403:
            st.session_state["github_auth_error"] = True
            print(f"GitHub Auth Error: {e}")
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
    # Fail fast if we already know auth is bad
    if st.session_state.get("github_auth_error", False):
        return False

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
            elif e.status == 401 or e.status == 403:
                st.session_state["github_auth_error"] = True
                return False
            else:
                raise e
        return True
    except Exception as e:
        # Catch top level auth errors too (e.g. get_repo failing)
        if isinstance(e, GithubException) and (e.status == 401 or e.status == 403):
             st.session_state["github_auth_error"] = True
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
            # Try to read root directory instead of specific file
            contents = repo.get_contents("")
            file_count = len(contents) if isinstance(contents, list) else 1
            return True, f"Github 연결 성공! (계정: {login}, 저장소: {repo_name}, 파일 {file_count}개)"
        except Exception as e:
            # Diagnosis: List available repos to see if it's a permission issue or typo
            try:
                available_repos = [r.full_name for r in user.get_repos(sort="updated")[:5]]
                
                # Double check if we actually found the repo object but just couldn't read contents
                # If e is 404 on get_contents, it means repo exists but is empty
                if "404" in str(e) and repo_name in available_repos:
                     return True, f"Github 연결 성공! (계정: {login}, 저장소: {repo_name})\n⚠️ 주의: 저장소가 비어있거나 파일을 읽을 수 없습니다. (데이터가 아직 없을 수 있음)"
                
                return False, f"⚠️ 접근 실패! (내 계정: {login})\n\n목표 저장소: '{repo_name}' (읽기 실패: {e})\n\n✅ 내 토큰으로 보이는 저장소 목록 (최신순 5개):\n" + "\n".join([f"- {r}" for r in available_repos])
            except:
                return False, f"저장소 '{repo_name}' 접근/읽기 실패: {e} (권한 없음)"
        
    except Exception as e:
        return False, f"Github 초기화 오류: {e}"
