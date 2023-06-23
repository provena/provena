#!/bin/bash -e

# Run from top level dir
echo "Running mypy python type checks"
python_command="python3"

# Setup working dir
working_dir="${PWD}"

# Check python is available at python
${python_command} --version

requirement_file="requirements.txt"
echo "Using requirement file ${requirement_file}"

# List of type checking locations 
# The CDK setup is also type checked but must have synthed to make it
# this far so not including at the moment
mypy_check_locations=("tests/integration")

# Go to each pytest environment 
for loc in ${mypy_check_locations[@]}; do 
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
	mypy .

	# Return back to start
	echo "Tests complete, leaving ${PWD}"
	cd "${working_dir}"
done

requirement_file="testing_requirements.txt"
echo "Using requirement file ${requirement_file}"

# List of type checking locations 
# The CDK setup is also type checked but must have synthed to make it
# this far so not including at the moment
mypy_check_locations=("data-store-api" "identity-service" "prov-api" "registry-api")

# Go to each pytest environment 
for loc in ${mypy_check_locations[@]}; do 
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
	mypy .

	# Return back to start
	echo "Tests complete, leaving ${PWD}"
	cd "${working_dir}"
done

echo "Mypy type checks complete"

