#!/bin/bash -e

# Function to run pytest and set up virtual environment
function run_pytest() {
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
    pytest

    # Return back to start
    echo "Tests complete, leaving ${PWD}"
    cd "${working_dir}"
}

# Checking if we need to login to docker hub
if [[ -z "${DOCKERHUB_PASSWORD}" ]]; then
    echo "No docker credentials found - using unauthenticated docker pulls."
    echo "If you are experiencing rate limits, consider logging in."
else
    if [[ -z "${DOCKERHUB_USERNAME}" ]]; then
        echo "Provided dockerhub password but not username! Aborting"
        exit 1
    fi

    echo "Found dockerhub username and password environment variables - attempting login."
    echo "${DOCKERHUB_PASSWORD}" | docker login --username "${DOCKERHUB_USERNAME}" --password-stdin
    echo "Login successful"
fi

# Run from top level dir
echo "Working directory ${PWD}"
python_command="python3"

# Check python is available at python
${python_command} --version

# List of unit testing locations
working_dir="${PWD}"

# Array of locations and corresponding requirement files
locations=(
    "utilities/packages/python/shared-interfaces"
    "prov-api"
    "data-store-api"
    "id-service-api"
    "auth-api"
    "registry-api"
    "job-api"
)

requirement_files=(
    "testing-requirements.txt"
    "testing_requirements.txt"
    "testing_requirements.txt"
    "testing_requirements.txt"
    "testing_requirements.txt"
    "testing_requirements.txt"
    "dev-requirements.txt"
)

# Loop through the arrays and call the function
for ((i = 0; i < ${#locations[@]}; i++)); do
    location="${locations[i]}"
    requirement_file="${requirement_files[i]}"

    run_pytest "${requirement_file}" "${location}"
done
