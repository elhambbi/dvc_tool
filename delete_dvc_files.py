import os
import subprocess
import pandas as pd
from git import Repo

def check_audio_dvc_file(dvc_file, repo_path, extensions):
    with open(os.path.join(repo_path, dvc_file), "r") as f:
        content = f.read()
    return any(ext in content for ext in extensions)

def remove_dvc_files(dvc_files, repo_path, remote_name):
    # gitignore_root = os.path.join(repo_path, ".gitignore")   # gitignore file in repo root
    for dvc_f in dvc_files:
        files_to_add = []
        subprocess.run(["dvc", "remove", dvc_f], cwd= repo_path, check=True)
        subprocess.run(["dvc", "push"], cwd=repo_path, check=True) #not necessary
        files_to_add.append(dvc_f)
        dvc_file_dir = os.path.dirname(dvc_f)
        gitignore_file = os.path.join(dvc_file_dir, ".gitignore") # gitignore file is dvc file dir
        files_to_add.append(gitignore_file)
        print("files_to_add:")
        print(files_to_add)
        subprocess.run(["git", "add" ]+ files_to_add, cwd= repo_path)  # Add DVC file & .gitignore
    
    subprocess.run(["git", "commit", "-m", f"Removed {len(dvc_files)} DVC files to free up space"], cwd= repo_path, check=True)
    subprocess.run(["git", "push"], cwd= repo_path, check=True)

    # subprocess.run(["dvc", "pull"], cwd= repo_path, check=True) # removes the original files locally if exist


def main():
    remote_name = "ds_storage"
    data = pd.read_excel("dvc_files.xlsx")

    repo_dvc_map = {}  # Dictionary to group DVC files by (repo_path, branch)
    for _, row in data.iterrows():
        repo_path, branch, dvc_file = row["repo_path"], row["branch"], row["dvc_file"]
        key = (repo_path, branch)
        if key not in repo_dvc_map:
            repo_dvc_map[key] = []
        repo_dvc_map[key].append(dvc_file)

    # Process each repo and branch only once
    for (repo_path, branch), dvc_files in repo_dvc_map.items():
        print("*"*150)
        print(f"Checking out {repo_path} branch {branch}...")
        repo = Repo(repo_path)
        repo.git.checkout(branch)

        audio_dvc_files = [dvc_f for dvc_f in dvc_files if check_audio_dvc_file(dvc_f, repo_path, extensions=(".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".aiff"))]
        
        if audio_dvc_files:
            print(f"Removing {len(audio_dvc_files)} audio DVC files...")
            remove_dvc_files(audio_dvc_files, repo_path, remote_name)
            print(f"Completed removal for {repo_path} branch {branch}\n\n")
        else:
            print(f"No audio DVC files found in {repo_path} branch {branch}\n\n")


if __name__=="__main__":
    main()