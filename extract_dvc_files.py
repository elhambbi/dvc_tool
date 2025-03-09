import os
import time
import pandas as pd
from git import Repo
from github import Github

def get_repo_list(token= ""):
    g = Github(token)
    user = g.get_user()
    repo_names= []
    for repo in user.get_repos():
        repo_names.append(repo.name)
    return repo_names

def clone_repo(repo_url, repo_path):
    if not os.path.exists(repo_path):
        print(f"\n\nCloning {repo_url} into {repo_path}...")
        repo = Repo.clone_from(repo_url, repo_path)
    else:
        print(f"\n\nRepository already exists at {repo_path}. Pulling latest changes...")
        repo = Repo(repo_path)
        repo.remotes.origin.pull() 
    return repo

def get_all_branches(repo):
    repo.remotes.origin.fetch()
    remote_branches = [ref.name for ref in repo.remotes.origin.refs]
    return remote_branches

def find_dvc_files(repo_path):
    dvc_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".dvc"):
                item = os.path.join(root, file)
                item = item.split(f"{repo_path}/")[-1].strip()
                dvc_files.append(item)
    return dvc_files

def process_repo(repo_url, base_dir):
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(base_dir, repo_name)
    repo = clone_repo(repo_url, repo_path)
    time.sleep(1)
    branches = [b for b in get_all_branches(repo) if b != "origin/HEAD"]

    print(f"Repo path: {repo_path}")
    print(f"Branches found: {branches}")

    all_dvc_files = []
    for branch in branches:
        branch_name = branch.replace("origin/", "") 
        print(f"Switching to branch {branch_name} ...")
        repo.git.checkout(branch_name, "--")  # -- to force checkouting if branch name is ambiguous for git
        time.sleep(1)

        dvc_files = find_dvc_files(repo_path)
        all_dvc_files.extend([(repo_path, branch_name, file) for file in dvc_files])

    return all_dvc_files

def main():
    token = "<your_github_account_token>"
    repo_names = get_repo_list(token= token)
    repos = [f"git@github.com:<your_github_username>/{repo}.git" for repo in repo_names if repo != "dvc_tool"]
    print(f"{len(repos)} repos found.")
    print(repos)
    base_dir = "cloned_repos"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    data= []
    for repo_url in repos:
        all_dvc_files = process_repo(repo_url, base_dir)
        data.extend(all_dvc_files)

    df = pd.DataFrame(data, columns=["repo_path","branch", "dvc_file"])
    excel_filename = f"dvc_files.xlsx"
    df.to_excel(excel_filename, index=False)
    print(f"\nSaved {excel_filename}")


if __name__ == "__main__":
    main()
