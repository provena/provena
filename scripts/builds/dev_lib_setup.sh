#!/bin/bash
local_lib_path="src/react-libs"

echo "Clearing existing copied shared lib contents"
rm -rf ${local_lib_path}

echo "Performing shared lib linking process"

# this is the location of the shared libraries (relative to ./src)
echo "lib_path=../../utilities/packages/typescript/react-libs/src"
lib_path="../../utilities/packages/typescript/react-libs/src"

# need to create from within the src folder
echo "cd src"
cd src

# create symbolic link and overwrite
echo "ln -sf ${lib_path} react-libs"
ln -sf ${lib_path} react-libs

echo "Completed DEV lib setup"
exit 0
