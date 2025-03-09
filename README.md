# DVC tool
This is a guideline for using the DVC (Data Version Control) tool with AWS S3 buckets.

## Creating DVC files

https://dvc.org/doc/start

Creating DVC files on AWS S3 storage:

1. If dvc is not installed on your pc, install and initialize it:
- `pip install dvc[s3]`
- `dvc init`

2. On your local machine, clone the github repository first if you don't have it.
3. Add files to be tracked by dvc (for more than one file use wildcard notation in file_name e.g *.mp3):
- `export AWS_ACCESS_KEY_ID= ...`
- `export AWS_SECRET_ACCESS_KEY= ...`
- `dvc add file_name(s).originalformat` , 
- if the files are in multiple sub-folders, in the parent folder do something like this : `find . -type f -name "*.mp3" -exec dvc add {} \;`


4. Push changes into the github repository:
(for more than one file use wildcard notation in file_name e.g *.dvc)
- `git config --global user.email "user_email"`
- `git config --global user.name "user_name"`
- `git add file_name(s).originalformat.dvc`

Also, DVC automatically creates a .gitignore file to ignore original files. If it is not added with dvc files automatically, add it separately:
- `git add .gitignore`
- `git commit -m "committing message"`
- `git push`

5. Modify the .dvc/config file to specify the remote storage (AWS s3 bucket) by adding the following lines (you can modify this configuration):

"""

[core]
    
    remote = <your_storage_name>
    autostage = true
    
[cache]

    dir = /tmp

['remote "<your_storage_name>"']

    url = <your_bucket_name>

"""

6. Add the remote storage:
- `dvc remote add`  
- `dvc remote list` (this command should show `<your_bucket_name>` ; `<your_storage_name>` is an alias for your `<your_bucket_name>`)

7. Push changes to dvc:
- `dvc push` to  push original files to S3 AWS (they are automatically committed with dvc add): 

To download and test the created dvc files from github repository:

check that AWS access keys are already exported:
- `echo $AWS_ACCESS_KEY_ID`
- `echo $AWS_SECRET_ACCESS_KEY`
- `git clone github_url` 
- `dvc pull file_name.originalformat.dvc`

To remove dvc files from the remote storage and stop tracking them with dvc:
- `dvc remove <dvc_file>`
- `dvc push`
- `git add <dvc_file> <gitignore_file>`
- `git commit -m "message"`
- `git push`


## DVC on Google Colab

- %env AWS_ACCESS_KEY_ID = [AWS KEY]
- %env AWS_SECRET_ACCESS_KEY = [AWS SECRET KEY]
- !pip install dvc[s3]
- !pip install git (in case git is not there)

the other commands will be the same.

## Organizing DVC files using DVC

There are two python scripts to orgnize dvc files after creating them:
- `extract_dvc_files.py`: clones all the repositories from your github account and saves an excel files that contains the list of all dvc files for all repositories and branches.
- `delete_dvc_files.py`: gets the output excel from previous script, and removes desired dvc files from the remote storage (modify the code to chose the files to be deleted).

## Organizing DVC files directly on the bucket (Not suggested!!)

**Important:**

To organize (add, delete, whatever) the files that you have pushed to the bucket using dvc, you must do it using dvc tool in the git repositories of the projects and not touch the bucket directly.

**Note 1:**
The files are saved with hashes on the bucket so you can't easily see the original file names and types on the bucket. If you know which dvc files are from which git repositories, it'll be easier to track them on the bucket because you already have the dvc files locally and you don't need to scan the whole bucket to find your files. The hidden folder `.dvc` in your git repository is where you can find the hashed files on the bucket. But if you don't know, then check the whole bucket with the following steps in order to find the files:

**Note 2:** some hashed files might be inside sub-folders in the bucket for example `folder1/folder2/folder3/hash`. Consider the complete path to refer to a hashed file in the following commands. 

This is an example for checking the audio files pushed to the bucket using dvc:

- export your AWS keys
- Check the current occupied storage on AWS by the files in your bucket:
  - `aws s3 ls <your_bucket_name>/ --summarize --human-readable --recursive`
- `aws s3 ls <your_bucket_name>/` lists all hashed files using dvc stored in the bucket
- `aws s3 ls <your_bucket_name>/ --recursive > s3_files.txt`
- `awk '{print $4}' s3_files.txt > hash_list.txt`

- This command checks all the hashes in `hash_list.txt` to find the ones that correspond to an audio file and saves them in `audio_files.txt`. This takes some time. It does it in batches of 20 to speed up but you can use larger sizes:
    - `xargs -P 20 -I {} bash -c '
    echo "Checking {}..."
    if aws s3 cp "<your_bucket_name>/{}" temp_file --quiet; then
        if ffmpeg -i temp_file 2>&1 | grep -q "Audio"; then
            echo "{}" >> audio_files.txt
        fi
    fi
    rm -f temp_file
' < hash_list.txt`

- This command copies all the audio files from the bucket into s3audio folder:
  - `cat audio_files.txt | xargs -I {} aws s3 cp <your_bucket_name>/{} s3audios/`
  - for a single file: `aws s3 cp <your_bucket_name>/<hashed_file> s3audios/`

- Check the downloaded files to separate non-audio files if there are any, and move the audios in audio_files folder:  
  - `for file in s3audios/*; do
    if ffprobe -i "$file" -show_streams -select_streams a -loglevel error | grep -q "codec_type=audio"; then
        mv "$file" audio_files/
    fi
done`

- Clean up the hash list in `audio_files.txt` by removing the ones for non-audio files.
- To delete the audio files from the bucket:
  - `cat audio_files.txt | xargs -I {} aws s3 rm <your_bucket_name>/{}`
- To verify the deletion. If no output appears, all files have been deleted successfully:
  - `aws s3 ls <your_bucket_name>/ --recursive | grep -Ff audio_files.txt`
- Check the occupied storage on the bucket again after deletion:
  - `aws s3 ls <your_bucket_name>/ --summarize --human-readable --recursive`