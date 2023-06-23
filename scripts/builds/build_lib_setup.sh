#!/bin/bash

echo "Setting up shared library"

lib_name="react-libs"
lib_path="../utilities/packages/typescript/${lib_name}/src"
local_lib_path="src/${lib_name}"

echo "Removing existing library install"
echo "rm -rf ${local_lib_path}"
rm -rf ${local_lib_path}

echo "Making replacement directory"
echo "mkdir ${local_lib_path}"
mkdir ${local_lib_path}

echo "Copying from shared lib into local build path"
echo "cp -r ${lib_path}/* ${local_lib_path}"
cp -r ${lib_path}/* ${local_lib_path}

echo "Completed BUILD lib setup"
exit 0
