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

# from https://stackoverflow.com/questions/1527049/how-can-i-join-elements-of-an-array-in-bash
function join_by {
	local IFS="$1"
	shift
	echo "$*"
}

feat_desc=$(join_by - "${branch_split[@]:2}")

main_branches=("main" "test" "stage" "prod")

pipeline_link_q_string=$(echo "{\"f\":{\"text\":\"f${ticket_number}\"},\"s\":{\"property\":\"updated\",\"direction\":-1},\"n\":10,\"i\":0}" | base64 -w 0)
pipeline_link="https://ap-southeast-2.console.aws.amazon.com/codesuite/codepipeline/pipelines?region=ap-southeast-2&pipelines-meta=${pipeline_link_q_string}"

general_prefix="https://"
base_url=${args[--url]}
general_postfix=".${base_url}/"

url_prefix="f${ticket_number}"

if [ ${args[--ui_only]} ]; then
	names=("landing-portal" "data-store-ui" "prov-ui" "registry-ui")
	postfixes=("" "-data" "-prov" "-registry")
else
	names=("landing-portal" "job-api" "data-store-api" "data-store-ui" "auth-api" "prov-api" "prov-ui" "registry-api" "registry-ui")
	postfixes=("" "-job-api" "-data-api" "-data" "-auth-api" "-prov-api" "-prov" "-registry-api" "-registry")
fi

echo "Feature branch name: **${current_branch}**"
echo

if [ ${args[--ui_only]} ]; then
	echo "**UI Only Deployment**"
	echo
fi

echo "URL Prefix: ${url_prefix}"
echo

echo "Pipeline links: [pipelines](${pipeline_link})"
echo

echo "Deployed components:"
echo
for index in "${!names[@]}"; do
	name=${names[$index]}
	postfix=${postfixes[$index]}

	echo "[$name](${general_prefix}${url_prefix}${postfix}${general_postfix})"
	echo
done

if [ ${args[--ui_only]} ]; then
	ui_only_arg=" --ui_only "
else
	ui_only_arg=" "
fi

echo "To tear down feature deployment: ./fb destroy${ui_only_arg}${ticket_number} ${feat_desc}"
