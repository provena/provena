#!/usr/bin/env bash -e

python_command="python3.10"

# get the current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# split branch on hyphens
IFS='-'
branch_split=($current_branch)
unset IFS

# check that the second number is okay
ticket_number=${branch_split[1]}

stack_prefix="f${ticket_number}"

main_branches=("main" "test" "stage" "prod")

pipeline_link_q_string=$(echo "{\"f\":{\"text\":\"${stack_prefix}\"},\"s\":{\"property\":\"updated\",\"direction\":-1},\"n\":10,\"i\":0}" | base64 -w 0)
pipeline_link="https://ap-southeast-2.console.aws.amazon.com/codesuite/codepipeline/pipelines?region=ap-southeast-2&pipelines-meta=${pipeline_link_q_string}"

for b_name in "${main_branches[@]}"; do
	# check it isn't a main branch
	if [ ${current_branch} == ${b_name} ]; then
		echo "Cannot deploy a feature branch from primary branch ${b_name}."
		exit 1
	fi
done

# check with user
echo "Deploying from current branch ${current_branch}."
read -p "Is this correct? (yY)" -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
	echo "Continuing"
else
	echo "Aborting"
	exit 1
fi

# check with user
echo "Parsed the ticket number as ${ticket_number}."
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

echo "Running CDK deploy of pipeline with feature configuration"
echo

unset PIPELINE_ALERTS
if [ ${args[--notify]} ]; then
	echo "Enabling pipeline alerts"
	export PIPELINE_ALERTS="true"
fi

unset ENABLE_API_MONITORING
if [ ${args[--monitoring]} ]; then
	echo "Enabling API monitoring via Sentry"
	export ENABLE_API_MONITORING="true"
fi

ui_only_arg="--no-ui-only"
unset UI_ONLY
if [ ${args[--ui_only]} ]; then
	echo "Performing a UI Only deployment"
	ui_only_arg="--ui-only"
fi

# run the helper script to deploy feature branch
echo "Running helper function: 'python app_run.py FEAT pipeline ${ui_only_arg} deploy --require-approval never'"
python app_run.py FEAT pipeline ${ui_only_arg} "deploy --require-approval never"

echo "Pipeline deploy completed, monitor and update deployment from ${pipeline_link} on the BUILD account."
