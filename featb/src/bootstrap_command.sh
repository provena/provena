#!/usr/bin/env bash -e

python_command="python3.10"

# get the current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# split branch on hyphens
IFS='-'
branch_split=($current_branch)
unset IFS

# check that the second number is okay
ticket_number=${branch_split[1]}

# move into the env bootstrapper location
echo "Moving to environment bootstrapper tool"
echo

cd admin-tooling/environment-bootstrapper

echo "Creating python venv"
echo

# create a virtual environment
${python_command} -m venv .venv

echo "Sourcing venv"
echo

# source and install requirements
source .venv/bin/activate

# install latest pip
pip install pip --upgrade

echo "Installing requirements"
echo

pip install -r requirements.txt

echo "Running bootstrap operation with feature branch number ${ticket_number}"
echo

# run the helper script to deploy feature branch
python environment_bootstrapper.py bootstrap-stage feature --suppress-warnings --param feature_number:${ticket_number}

echo "Bootstrapping complete."
