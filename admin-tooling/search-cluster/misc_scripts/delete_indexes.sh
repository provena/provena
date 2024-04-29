#!/bin/bash

# This script is a hacky way to quickly delete a list of indexes from the open
# search cluster. You need to list your indices below, input your env e.g. DEV
# and endpoint base e.g. https://search-service.dev.domain.com

# PROCEED WITH CAUTION - will delete all listed indexes without any
# prompts/checks

# List of indices to delete (list them below)
declare -a indices=(
"1234"
"3564"
                    )

# Common endpoint URL
endpoint_base="your service endpoint here"
env="your env here"

for index in "${indices[@]}"
do
   echo "Deleting index: $index"
   
   # Construct the full endpoint including the index
   endpoint="$endpoint_base/$index"
   
   # Run the Python command
   python run_command.py manual-command ${env} DELETE "$endpoint"
done
