#!/usr/bin/env bash -e

if [ ${args[--ui_only]} ]; then
	ui_only_arg="--ui_only"
else
	ui_only_arg=""
fi

echo "./fb run app ${ui_only_arg} deploy --hotswap"

./fb run app ${ui_only_arg} deploy --hotswap
