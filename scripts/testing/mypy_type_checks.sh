#!/bin/bash -e

# Function to run mypy tests
function run_mypy_tests() {
    local requirement_file=$1
    local location=$2

    # goto test working environment
    cd "${location}"
    echo "Working in ${PWD}"

    # setup python virtual environment
    echo "Setting up virtual environment"
    python_command="python3"
    ${python_command} -m venv .venv
    # source virtual environment
    source .venv/bin/activate
    # install dependencies
    echo "Installing dependencies"
    pip install -r "${requirement_file}"
    # run pytest
    mypy .

    # Return back to start
    echo "Tests complete, leaving ${PWD}"
    cd "${working_dir}"
}

# Run from top level dir
echo "Running mypy python type checks"
python_command="python3"

# Setup working dir
working_dir="${PWD}"

# Check python is available at python
${python_command} --version

# Array of requirement files
requirement_files=(
    # integration
    "requirements.txt"
    # data store, identity service, prov api, registry api
    "testing_requirements.txt"
    "testing_requirements.txt"
    "testing_requirements.txt"
    "testing_requirements.txt"
    # job api
    "dev-requirements.txt"
    # async utils (ddb connector)
    "dev_requirements.txt"
    # async utils (ecs sqs python tools)
    "dev_requirements.txt"
    # async utils (lambda invoker)
    "dev_requirements.txt"
)

# List of type checking locations
mypy_check_locations=(
    "tests/integration"
    "data-store-api"
    "identity-service"
    "prov-api"
    "registry-api"
    "job-api"
    "async-util/ddb_connector"
    "async-util/ecs-sqs-python-tools"
    "async-util/lambda_invoker"
)

# Loop through the arrays and call the function
for ((i = 0; i < ${#mypy_check_locations[@]}; i++)); do
    requirement_file="${requirement_files[i]}"
    mypy_check_location="${mypy_check_locations[i]}"

    echo "Using requirement file ${requirement_file}"
    run_mypy_tests "${requirement_file}" "${mypy_check_location}"
done

echo "Mypy type checks complete"
