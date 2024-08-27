#!/bin/bash

# Script used for updating GitHub tokens. This script accepts an argument
# build/ops. It then pulls the appropriate configurations from the private
# configuration repo (configured in env.json) and deploys the pipeline stack,
# github bootstrap stack, and if in build account, the feature branch manager.

set -e  # Exit immediately if a command exits with a non-zero status

# Function to print messages
print_message() {
    echo "===> $1"
}

# Function to setup and activate virtual environment
setup_venv() {
    print_message "Setting up virtual environment..."
    python3.10 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install pip --upgrade
}

# Check if the correct number of arguments is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <build|ops>"
    exit 1
fi

# Check if the argument is valid
if [ "$1" != "build" ] && [ "$1" != "ops" ]; then
    echo "Error: Argument must be either 'build' or 'ops'"
    exit 1
fi

# Set the stage based on the input
if [ "$1" == "build" ]; then
    STAGE="dev"
else
    STAGE="prod"
fi

print_message "python3.10 version: $(python3.10 --version)"

# Run config command
print_message "Running ./config rrap $STAGE"
./config rrap $STAGE

# Change to infrastructure directory
print_message "Changing to infrastructure directory"
cd infrastructure

# Setup virtual environment and run app_run.py
setup_venv
print_message "Running app_run.py"
python3.10 app_run.py $STAGE pipeline "deploy --require-approval never"

# Move back to root directory
print_message "Moving back to root directory"
cd ..

# Change to github-creds directory
print_message "Changing to github-creds directory"
cd utilities/supporting-stacks/github-creds

# Setup virtual environment and run cdk deploy
setup_venv
print_message "Exporting CONFIG_ID=$1"
export CONFIG_ID=$1
print_message "Running cdk deploy"
cdk deploy

# Move back to root directory
print_message "Moving back to root directory"
cd ../../..

# If input was "ops", finish here
if [ "$1" == "ops" ]; then
    print_message "Skipping feature branch manager update (ops mode)"
    print_message "Script completed successfully"
    exit 0
fi

# For "build" input, continue with feature branch manager
print_message "Including feature branch manager update"
cd utilities/supporting-stacks/feature-branch-manager

# Setup virtual environment and run cdk deploy
setup_venv
print_message "Exporting CONFIG_ID=$1"
export CONFIG_ID=$1
print_message "Running cdk deploy"
cdk deploy

# Move back to root directory
cd ../../..

print_message "Script completed successfully"
