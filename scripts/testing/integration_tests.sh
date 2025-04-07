#!/bin/bash -e

# Run from top level dir
echo "Working directory ${PWD}"
python_command="python3.10"

# Check python is available at python
${python_command} --version

# List of unit testing locations 
working_dir="${PWD}"

locations=("tests/integration")
requirement_file="requirements.txt"

# Go to each pytest environment 
for loc in ${locations[@]}; do 
	# goto test working environment
	cd "${loc}"
	echo "Working in ${PWD}"

	# setup python virtual environment 
	echo "Setting up virtual environment"
	${python_command} -m venv .venv 
	# source virtual environment
	source .venv/bin/activate 
	# install dependencies 
	echo "Installing dependencies"
	pip install -r ${requirement_file}
	# run pytest with print statements
	pytest -s

	# Return back to start
	echo "Tests complete, leaving ${PWD}"
	cd "${working_dir}"
done

