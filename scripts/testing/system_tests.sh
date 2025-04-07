#!/bin/bash -e

# Run from top level dir
echo "Working directory ${PWD}"
python_command="python3.10"

# Check python is available at python
${python_command} --version

# Find the chrome installation location 
chrome_location="$(which google-chrome)"
echo "Chrome location: ${chrome_location}"
export CHROME_PATH="${chrome_location}"

# List of unit testing locations 
working_dir="${PWD}"

location="tests/system"
requirement_file="requirements.txt"
dependencies_file="dependencies.sh"

cd "${location}"
echo "Working in ${PWD}"

# Install system dependencies
sudo ./${dependencies_file}
# setup python virtual environment 
echo "Setting up virtual environment"
${python_command} -m venv .venv 
# source virtual environment
source .venv/bin/activate 
# install dependencies 
echo "Installing dependencies"
pip install -r ${requirement_file}
# run pytest 
pytest

# Return back to start
echo "Tests complete, leaving ${PWD}"
cd "${working_dir}"
