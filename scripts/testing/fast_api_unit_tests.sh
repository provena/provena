#!/bin/bash -e

# Run from top level dir
echo "Working directory ${PWD}"
python_command="python3"

# Check python is available at python
${python_command} --version

# List of unit testing locations
working_dir="${PWD}"

# data store API and ID service do not require any environment variables (everything pulled run time)

# Identity service requires handle authorisation information as environment variables, this is injected at infrastructure automation stage
locations=("prov-api" "data-store-api" "auth-api" "registry-api")
requirement_file="testing_requirements.txt"

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
	# run pytest
	pytest

	# Return back to start
	echo "Tests complete, leaving ${PWD}"
	cd "${working_dir}"
done
