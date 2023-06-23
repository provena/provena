#!/bin/bash -e
script_dir="scripts/interface_management"
dep_file="dependencies.sh"
py_script_file="export_interfaces.py"
req_file="requirements.txt"
python_command="python3"

# Move into working directory
cd ${script_dir}

# Install dependencies 
./"${dep_file}"

# Setup python venv 
${python_command} --version
${python_command} -m venv .venv 
source .venv/bin/activate 
pip install -r "${req_file}"

# Run the export 
python "${py_script_file}"
