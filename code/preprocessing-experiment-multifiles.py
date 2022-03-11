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

# Read data locally
input_data_path = os.path.join("/opt/ml/processing/input", "dataset.csv")

base_dir = './sagemaker-dvc-sample/dataset'

def split_dataframe(df, num=5):
    chunk_size = int(df.shape[0] / num)
    chunks = [df.iloc[i:i+chunk_size] for i in range(0,df.shape[0], chunk_size)]
    return chunks

def clone_dvc_git_repo(dvc_repo_url):
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

def sync_data_with_dvc(branch):
    os.chdir(base_dir)
    print(f"Create branch {branch}")
    try:
        subprocess.check_call(['git', 'checkout', '-b', branch])
        print(f"Create a new branch: {branch}")
    except:
        subprocess.check_call(['git', 'checkout', branch])
        print(f"Checkout existing branch: {branch}")
    print("Add files to DVC")
    subprocess.check_call(['dvc', 'add', 'train/'])
    subprocess.check_call(['dvc', 'add', 'validation/'])
    subprocess.check_call(['dvc', 'add', 'test/'])
    subprocess.check_call(['git', 'add', '.'])
    subprocess.check_call(['git', 'commit', '-m', f"'add data for {branch}'"])
    print("Push data to DVC")
    subprocess.check_call(['dvc', 'push'])
    print("Push dvc metadata to git")
    subprocess.check_call(['git', 'push', '--set-upstream', 'origin', branch, '--force'])
    commit_hash = subprocess.check_output(['git', 'log', '--format=%H', '-n', '1']).decode("utf-8").replace('\n','')
    print(f"commit hash: {commit_hash}")
    with Tracker.load() as tracker:
        tracker.log_parameters({"data_commit_hash": commit_hash})

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-test-split-ratio", type=float, default=0.3)
    parser.add_argument("--dvc-repo-url", type=str, default="codecommit::eu-west-1://sagemaker-dvc-sample")
    parser.add_argument("--dvc-branch", type=str, default="my-experiment")
    args, _ = parser.parse_known_args()
    
    with Tracker.load() as tracker:
        tracker.log_parameters(
            {
                "data_repo_url": args.dvc_repo_url,
                "train_test_split_ratio": args.train_test_split_ratio,
                "data_branch": args.dvc_branch
            }
        )
    
    clone_dvc_git_repo(args.dvc_repo_url)
    generate_train_validation_files(args.train_test_split_ratio)
    sync_data_with_dvc(args.dvc_branch)