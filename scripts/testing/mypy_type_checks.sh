#!/bin/bash -e

# Function to run mypy tests
function run_mypy_tests() {
    local location=$1
    local requirement_file=$2

    echo "Running tests for ${location} using ${requirement_file}"

    # Go to test working environment
    cd "${location}"
    echo "Working in ${PWD}"

    # Setup python virtual environment
    echo "Setting up virtual environment"
    ${python_command} -m venv .venv

    # Source virtual environment
    source .venv/bin/activate

    # Install dependencies
    echo "Installing dependencies"
    pip install --upgrade pip
    pip install -r "${requirement_file}"

    # Run mypy
    echo "Running mypy"
    mypy .

    # Return back to start
    echo "Tests complete, leaving ${PWD}"
    cd "${working_dir}"

    # Deactivate virtual environment
    deactivate
}

# Main script execution starts here

echo "Running mypy python type checks"

# Setup working dir and python command
working_dir="${PWD}"
python_command="python3"

# Check python is available
${python_command} --version

# Array of locations and requirement files
# Each odd index is a location, and the following even index is its corresponding requirement file
locations_and_requirements=(
    "search-api"
    "testing_requirements.txt"
    "tests/integration"
    "requirements.txt"
    "data-store-api"
    "testing_requirements.txt"
    "id-service-api"
    "testing_requirements.txt"
    "prov-api"
    "testing_requirements.txt"
    "registry-api"
    "testing_requirements.txt"
    "job-api"
    "dev-requirements.txt"
    "async-util/ddb_connector"
    "dev_requirements.txt"
    "async-util/ecs-sqs-python-tools"
    "dev_requirements.txt"
    "async-util/lambda_invoker"
    "dev_requirements.txt"
    "utilities/packages/python/provena-shared-functionality"
    "dev_requirements.txt"
    "utilities/packages/python/provena-interfaces"
    "testing-requirements.txt"
    "utilities/supporting-stacks/github-creds"
    "requirements-dev.txt"
    "utilities/supporting-stacks/feature-branch-manager"
    "requirements-dev.txt"
)

# Loop through the array and call the function
for ((i = 0; i < ${#locations_and_requirements[@]}; i+=2)); do
    location="${locations_and_requirements[i]}"
    requirement_file="${locations_and_requirements[i+1]}"
    run_mypy_tests "${location}" "${requirement_file}"
done

echo "Mypy type checks complete"
