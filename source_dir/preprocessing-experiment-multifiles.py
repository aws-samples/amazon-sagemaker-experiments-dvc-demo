# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
import argparse
import sys
import subprocess

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split

from smexperiments.tracker import Tracker

import dvc.api

# Prepare paths
input_data_path = os.path.join("/opt/ml/processing/input", "dataset.csv")
data_path = 'dataset'
base_dir = f"./sagemaker-dvc-sample/{data_path}"
file_types = ['test','train','validation']

dvc_repo_url = os.environ.get('DVC_REPO_URL')
dvc_branch = os.environ.get('DVC_BRANCH')
user = os.environ.get('USER', "sagemaker")

def configure_git():
    subprocess.check_call(['git', 'config', '--global', 'user.email', '"sagemaker-processing@example.com"'])
    subprocess.check_call(['git', 'config', '--global', 'user.name', user])
    
def split_dataframe(df, num=5):
    chunk_size = int(df.shape[0] / num)
    chunks = [df.iloc[i:i+chunk_size] for i in range(0,df.shape[0], chunk_size)]
    return chunks

def clone_dvc_git_repo():
    print(f"Cloning repo: {dvc_repo_url}")
    subprocess.check_call(["git", "clone", dvc_repo_url])

def generate_train_validation_files(ratio):
    for path in ['train', 'validation', 'test']:
        output_dir = Path(f"{base_dir}/{path}/")
        output_dir.mkdir(parents=True, exist_ok=True)

    print("Read dataset")
    dataset = pd.read_csv(input_data_path)
    train, other = train_test_split(dataset, test_size=ratio)
    validation, test = train_test_split(other, test_size=ratio)
    
    print("create train, validation, test")
    for index, chunk in enumerate(split_dataframe(pd.DataFrame(train))):
        chunk.to_csv(f"{base_dir}/train/california_train_{index + 1}.csv", header=False, index=False)

    for index, chunk in enumerate(split_dataframe(pd.DataFrame(validation), 3)):
        chunk.to_csv(f"{base_dir}/validation/california_validation_{index + 1}.csv", header=False, index=False)
    
    pd.DataFrame(test).to_csv(f"{base_dir}/test/california_test.csv", header=False, index=False)
    print("data created")

def sync_data_with_dvc():
    os.chdir(base_dir)
    print(f"Create branch {dvc_branch}")
    try:
        subprocess.check_call(['git', 'checkout', '-b', dvc_branch])
        print(f"Create a new branch: {dvc_branch}")
    except:
        subprocess.check_call(['git', 'checkout', dvc_branch])
        print(f"Checkout existing branch: {dvc_branch}")
    print("Add files to DVC")
    
    for file_type in file_types:
        subprocess.check_call(['dvc', 'add', f"{file_type}/"])

    subprocess.check_call(['git', 'add', '.'])
    subprocess.check_call(['git', 'commit', '-m', f"'add data for {dvc_branch}'"])
    print("Push data to DVC")
    subprocess.check_call(['dvc', 'push'])
    print("Push dvc metadata to git")
    subprocess.check_call(['git', 'push', '--set-upstream', 'origin', dvc_branch, '--force'])
    commit_hash = subprocess.check_output(['git', 'log', '--format=%H', '-n', '1']).decode("utf-8").replace('\n','')
    print(f"commit hash: {commit_hash}")

    with Tracker.load() as tracker:
        tracker.log_parameters({"data_commit_hash": commit_hash})
        for file_type in file_types:
            path = dvc.api.get_url(
                f"{data_path}/{file_type}",
                repo=dvc_repo_url,
                rev=dvc_branch
            )
            tracker.log_output(name=f"{file_type}",value=path)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-test-split-ratio", type=float, default=0.3)
    args, _ = parser.parse_known_args()
    
    train_test_split_ratio = args.train_test_split_ratio
    
    with Tracker.load() as tracker:
        tracker.log_parameters(
            {
                "train_test_split_ratio": train_test_split_ratio
            }
        )
    
    configure_git()
    clone_dvc_git_repo()
    generate_train_validation_files(train_test_split_ratio)
    sync_data_with_dvc()
