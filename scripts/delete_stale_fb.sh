#!/bin/bash

# check python and aws cli 
python --version
aws --version

# move to feature manager folder  (assumes from base dir)
cd feature-branch-manager

# install venv 
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run the command 
python manager.py delete-stale --force
