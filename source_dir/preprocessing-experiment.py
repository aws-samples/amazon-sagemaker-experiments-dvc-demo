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

from git.repo.base import Repo

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

def clone_dvc_git_repo():
    print(f"Cloning repo: {dvc_repo_url}")
    repo = Repo.clone_from(dvc_repo_url, './sagemaker-dvc-sample')
    return repo
    
def generate_train_validation_files(ratio):
    for path in ['train', 'validation', 'test']:
        output_dir = Path(f"{base_dir}/{path}/")
        output_dir.mkdir(parents=True, exist_ok=True)

    print("Read dataset")
    dataset = pd.read_csv(input_data_path)
    train, other = train_test_split(dataset, test_size=ratio)
    validation, test = train_test_split(other, test_size=ratio)
    
    print("create train, validation, test")
    pd.DataFrame(train).to_csv(f"{base_dir}/train/california_train.csv", header=False, index=False)
    pd.DataFrame(validation).to_csv(f"{base_dir}/validation/california_validation.csv", header=False, index=False)
    pd.DataFrame(test).to_csv(f"{base_dir}/test/california_test.csv", header=False, index=False)
    print("data created")

def sync_data_with_dvc(repo):
    os.chdir(base_dir)
    print(f"Create branch {dvc_branch}")
    try:
        repo.git.checkout('-b', dvc_branch)
        print(f"Create a new branch: {dvc_branch}")
    except:
        repo.git.checkout(dvc_branch)
        print(f"Checkout existing branch: {dvc_branch}")
    print("Add files to DVC")
    
    for file_type in file_types:
        subprocess.check_call(['dvc', 'add', f"{file_type}/california_{file_type}.csv"])
    
    repo.git.add(all=True)
    repo.git.commit('-m', f"'add data for {dvc_branch}'")
    print("Push data to DVC")
    subprocess.check_call(['dvc', 'push'])
    print("Push dvc metadata to git")
    repo.remote(name='origin')
    repo.git.push('--set-upstream', repo.remote().name, dvc_branch, '--force')

    sha = repo.head.commit.hexsha
    print(f"commit hash: {sha}")

    with Tracker.load() as tracker:
        tracker.log_parameters({"data_commit_hash": sha})
        for file_type in file_types:
            path = dvc.api.get_url(
                f"{data_path}/{file_type}/california_{file_type}.csv",
                repo=dvc_repo_url,
                rev=dvc_branch
            )
            tracker.log_output(name=f"california_{file_type}",value=path)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-test-split-ratio", type=float, default=0.3)
    args, _ = parser.parse_known_args()
    
    train_test_split_ratio = args.train_test_split_ratio
    
    with Tracker.load() as tracker:
        tracker.log_parameters(
            {
                "train_test_split_ratio": train_test_split_ratio,
            }
        )
    
    configure_git()
    repo = clone_dvc_git_repo()
    generate_train_validation_files(train_test_split_ratio)
    sync_data_with_dvc(repo)
