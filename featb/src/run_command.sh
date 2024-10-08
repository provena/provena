#!/usr/bin/env bash -e

stack_type=${args[target]}
commands=${other_args[*]}

python_command="python3.10"

# get the current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# split branch on hyphens
IFS='-'
branch_split=($current_branch)
unset IFS

# check that the second number is okay
ticket_number=${branch_split[1]}

main_branches=("main" "test" "stage" "prod")

for b_name in "${main_branches[@]}"; do
	# check it isn't a main branch
	if [ ${current_branch} == ${b_name} ]; then
		echo "Cannot deploy a feature branch from primary branch ${b_name}."
		exit 1
	fi
done

# check with user
echo "Running commands from current branch ${current_branch}."
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

# move into infra folder and running helper
cd infrastructure

echo "Creating python venv"
echo

# create a virtual environment
${python_command} -m venv .venv

echo "Sourcing venv"
echo

# source and install requirements
source .venv/bin/activate

# install latest pip
pip install pip --upgrade

echo "Installing requirements"
echo

pip install -r requirements.txt

echo "Running cdk on ${stack_type} with commands ${commands}..."

stage_arg="feat"
if [ ${args[--ui_only]} ]; then
	echo "Performing a UI Only deployment"
	stage_arg="feat-ui"
fi

# run the helper script
python app_run.py ${stage_arg} ${stack_type} "${commands}"
