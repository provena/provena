#!/bin/bash
# Script for deploying feature branch manager

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

# Function to validate and split namespace/stage/config
validate_and_split() {
    local input=$1
    if [[ $input =~ ^[^/]+/[^/]+/[^/]+$ ]]; then
        IFS='/' read -r config_namespace config_stage config_name <<< "$input"
    else
        echo "Error: Input must be in the format namespace/stage/config"
        exit 1
    fi
}

# Function to display usage information
usage() {
    echo "Usage: $0 [--help] namespace/stage/config [--target git_url]"
    echo
    echo "Arguments:"
    echo "  namespace/stage/config     The namespace/stage/config for the feature branch manager"
    echo
    echo "Options:"
    echo "  --help                     Display this help message"
    echo "  --target git_url           (optional) Git URL for the config repo"
    echo
    echo "Note: 'namespace' is the config namespace, 'stage' is the config stage, and 'config' is the name of the config file (without .json extension)"
    echo
    echo "Example:"
    echo "  $0 org/dev/build --target https://github.com/org/config-repo.git"
    exit 1
}

# Parse command line arguments
if [ "$1" == "--help" ]; then
    usage
fi

if [ $# -lt 1 ]; then
    echo "Error: Missing required argument"
    usage
fi

validate_and_split "$1"
shift

target_repo=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            target_repo="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

print_message "python3.10 version: $(python3.10 --version)"

# Feature branch manager deployment
config_command="./config $config_namespace $config_stage"
if [ -n "$target_repo" ]; then
    config_command+=" --target $target_repo"
fi
print_message "Running $config_command"
$config_command

print_message "Changing to feature-branch-manager directory"
cd utilities/supporting-stacks/feature-branch-manager

setup_venv
print_message "Exporting CONFIG_ID=$config_name"
export CONFIG_ID=$config_name
print_message "Running cdk deploy for feature branch manager"
cdk deploy

print_message "Script completed successfully"