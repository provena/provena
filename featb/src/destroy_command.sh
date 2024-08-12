#!/usr/bin/env bash -e

# decode args
ticket_number=${args[ticket]}
feature_desc=${args[name]}
branch_name="feat-${ticket_number}-${feature_desc}"

python_command="python3.10"

# check with user
echo "Deleting app and pipeline stack for feature branch: ${branch_name}."
read -p "Is this correct? (yY)" -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
	echo "Continuing"
else
	echo "Aborting"
	exit 1
fi


echo "Exporting ticket number and branch name"
export TICKET_NUMBER=${ticket_number}
export BRANCH_NAME=${current_branch}

echo "Moving into infrastructure folder"
echo

# move into infra folder
cd infrastructure

echo "Checking cdk install"
echo

# check that cdk is working
cdk --version

echo "Checking AWS CLI install"
echo

# check that AWS CLI seems to be working
aws sts get-caller-identity

echo "Creating python venv"
echo

# create a virtual environment
${python_command} -m venv .venv

echo "Sourcing venv"
echo

# source and install requirements
source .venv/bin/activate

echo "Installing requirements"
echo

pip install -r requirements.txt

ui_only_arg="--no-ui-only"
unset UI_ONLY
if [ ${args[--ui_only]} ]; then
	echo "Performing a UI Only deployment"
	ui_only_arg="--ui-only"
fi

echo "Running CDK destroy of app with feature configuration"
echo

echo "Running helper function: 'python app_run.py FEAT app ${ui_only_arg} destroy --require-approval never'"
python app_run.py FEAT app ${ui_only_arg} "destroy --require-approval never"

echo "Running CDK destroy of pipeline with feature configuration"
echo

echo "Running helper function: 'python app_run.py FEAT pipeline ${ui_only_arg} destroy --require-approval never'"
python app_run.py FEAT pipeline ${ui_only_arg} "destroy --require-approval never"

echo "Pipeline and app destroy completed."
