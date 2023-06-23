#!/bin/bash -e

# Check that bucket name is present
if [[ -z "${BUCKET_NAME}" ]]; then
	echo "No BUCKET_NAME environment variable was present. Unsure where to deploy build files to. Aborting..."
	exit 1
fi

# Check that working directory is present
if [[ -z "${WORKING_DIRECTORY}" ]]; then
	echo "No WORKING_DIRECTORY environment variable was present. Not sure where to build from. Aborting..."
	exit 1
fi

echo "Deploying to ${BUCKET_NAME}"
echo "Building from ${WORKING_DIRECTORY}"

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

# Move to work dir
echo "Moving into working directory"
cd ${WORKING_DIRECTORY}

# Install npm dep's
echo "Installing npm dependencies npm version $(npm --version)"
npm install

# Building
echo "Running npm build"
npm run build

echo "Deploying to ${BUCKET_NAME} bucket and deleting other artifacts in bucket"
aws s3 sync ./build/ s3://${BUCKET_NAME} --delete
