#!/usr/bin/env bash -e

ticket_number=${args[ticket]}
feature_desc=${args[name]}
base_branch=${args[base]}

# branch name
branch_name="feat-${ticket_number}-${feature_desc}"

git checkout ${base_branch}
git pull
git checkout -b ${branch_name}
git push --set-upstream origin ${branch_name}

echo "Created and published feature branch ${branch_name} based on ${base_branch}. Use fb deploy to deploy the sandbox infrastructure for this feature branch."
