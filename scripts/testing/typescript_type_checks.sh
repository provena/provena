#!/bin/bash -e

# Setup NVM
echo "Installing NVM"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash

# adding nvm to path
echo "Adding nvm to path"

# Setup NVM dir
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Check nvm is present
echo "NVM version"
nvm --version

# install node 16
echo "Installing node 16"
nvm install 16

# use 16
echo "Using node 16"
nvm use 16

# Displaying npm and node version
echo "npm version"
npm --version

echo "node version"
node --version

# Run from top level dir
echo "Working directory ${PWD}"

echo "Running TypeScript type checks"

working_dir="${PWD}"

# List of type checking locations
ts_check_locations=("utilities/packages/typescript/react-libs" "data-store-ui" "landing-portal-ui" "registry-ui" "prov-ui")

# Check npm is present
npm --version

# Go to each pytest environment
for loc in ${ts_check_locations[@]}; do
	# goto test working environment
	cd "${loc}"
	echo "Working in ${PWD}"

	# install npm requirements
	echo "Installing node dependencies"
	npm install

	# run the type check
	echo "Running type check command"
	npx tsc

	# Return back to start
	echo "Type check complete, leaving ${PWD}"
	cd "${working_dir}"
done

echo "Type check testing complete"
