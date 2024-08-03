import os
import subprocess
import platform
import requests
from pathlib import Path
from getpass import getpass
import tkinter as tk
from tkinter import filedialog

def get_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    directory = filedialog.askdirectory(title="Select Directory")  # Open a directory selection dialog
    return directory

def detect_system():
    system = platform.system().lower()
    shell = os.environ.get('SHELL', 'unknown')
    print(f"System detected: {system}")
    print(f"Shell detected: {shell}")
    return system, shell

def check_git():
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Git is already installed.")
        return True
    except subprocess.CalledProcessError:
        print("Git is not installed.")
        return False

def install_git(system):
    if system == 'linux':
        distro = subprocess.run(['lsb_release', '-is'], capture_output=True, text=True).stdout.strip().lower()
        if 'ubuntu' in distro or 'debian' in distro:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'git'], check=True)
        elif 'centos' in distro or 'fedora' in distro or 'redhat' in distro:
            subprocess.run(['sudo', 'yum', 'install', '-y', 'git'], check=True)
    elif system == 'darwin':
        subprocess.run(['/bin/bash', '-c', '"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'], check=True)
        subprocess.run(['brew', 'install', 'git'], check=True)
    elif system == 'windows':
        print("Please install Git manually from https://git-scm.com/download/win")

def get_github_token():
    token = input("Enter your GitHub Personal Access Token: ")  # Changed getpass to input for visibility
    return token

def get_repositories(token):
    headers = {"Authorization": f"token {token}"}
    response = requests.get("https://api.github.com/user/repos", headers=headers)
    repos = response.json()
    return [(repo['name'], repo['clone_url'], repo['size']) for repo in repos]

def categorize_repositories(repositories):
    categorized = {
        "Tiny Repos": [],
        "Small Repos": [],
        "Medium Repos": [],
        "Large Repos": [],
        "Very Large Repos": []
    }
    
    for name, url, size in repositories:
        if size < 10:  # Size in KB
            categorized["Tiny Repos"].append((name, url))
        elif size < 100:
            categorized["Small Repos"].append((name, url))
        elif size < 1000:
            categorized["Medium Repos"].append((name, url))
        elif size < 10000:
            categorized["Large Repos"].append((name, url))
        else:
            categorized["Very Large Repos"].append((name, url))
    
    return categorized

def check_repo_status(repo_name):
    repo_path = Path(repo_name)
    if not repo_path.is_dir():
        return f"Repository {repo_name} is not cloned."
    try:
        result = subprocess.run(['git', '-C', repo_name, 'status'], capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return str(e)

def main():
    system, shell = detect_system()
    
    if not check_git():
        install_git(system)
    
    directory = get_directory()  # Get the directory from the user
    os.chdir(directory)  # Change to the selected directory

    token = get_github_token()
    repositories = get_repositories(token)
    categorized_repos = categorize_repositories(repositories)
    
    synced_repos = []
    edited_repos = []
    missing_repos = []

    for category, repos in categorized_repos.items():
        if repos:
            clone_choice = input(f"Do you want to clone {category} ({len(repos)} repos)? [y/n] ")
            if clone_choice.lower() == 'y':
                for repo_name, clone_url in repos:
                    try:
                        subprocess.run(['git', 'clone', clone_url], check=True)
                        print(f"Cloned {repo_name}.")
                    except subprocess.CalledProcessError as e:
                        print(f"Failed to clone {repo_name}: {e}")
            else:
                for repo_name, clone_url in repos:
                    missing_repos.append((repo_name, clone_url))

    for repo_name, clone_url in missing_repos:
        status = check_repo_status(repo_name)
        print(f"Status for {repo_name}:\n{status}")
        if "not cloned" in status:
            missing_repos.append((repo_name, clone_url))
        else:
            synced_repos.append(repo_name)  # Assuming synced if status is returned

    print("\nSummary:")
    print(f"Synced Repos: {', '.join(synced_repos) if synced_repos else 'None'}")
    print(f"Edited Repos: {', '.join(edited_repos) if edited_repos else 'None'}")
    print(f"Missing Repos: {', '.join(repo[0] for repo in missing_repos) if missing_repos else 'None'}")

if __name__ == "__main__":
    main()