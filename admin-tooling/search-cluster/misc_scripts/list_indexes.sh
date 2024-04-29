#!/bin/bash -e

# This script is a hacky way to quickly list out and print to terminal all
# indexes on an open search cluster. You need to input your env e.g. DEV and
# endpoint base e.g. https://search-service.dev.domain.com

# Define environment name, HTTP method, endpoint URL and file containing payload
ENV_NAME="your env here"    # replace with valid environment name
METHOD="GET"               # GET operation to list indices  
ENDPOINT_BASE="BASE URL HERE" 
ENDPOINT="${ENDPOINT_BASE}/_cat/indices?v"   # Endpoint URL for listing all indices in Elasticsearch

# Call python script with defined parameters - this gets the index list
output=$(python run_command.py manual-command $ENV_NAME $METHOD $ENDPOINT)

# Define an empty array
declare -a indices

# We will use two counters here:
# i is for line numbers, j is for counting each 2nd line from line 3.
i=0
j=1

while IFS= read -r line; do
  i=$((i+1))
  if (( i >= 3 )); then
    if (( j%2 != 0 )); then   # Take every second line beginning at line 3
      index_name=$(echo $line | awk '{print $3}') 
      indices+=("$index_name")
    fi
    j=$((j+1))
  fi
done < <(echo "$output")

# Print all indices
for index in "${indices[@]}"; do
  echo "$index"
done