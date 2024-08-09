# Initialize global variables and perform setup tasks
initialize() {
  set -e  # Exit immediately if a command exits with a non-zero status
  # Set DEBUG flag if environment variable is set to 'true'
  [[ "${DEBUG}" == "true" ]] && set -x
  # Initialize variables
  TEMP_DIR=""
  ENV_FILE="env.json"
  
  # Ensure jq is installed
  if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed. Please install jq and try again."
    exit 1
  fi
}

# Read the default target repository from env.json
read_default_target() {
  if [[ -f "$ENV_FILE" ]]; then
    jq -r ".$NAMESPACE.$STAGE // empty" "$ENV_FILE"
  fi
}

# Update or create env.json with the new target repository
update_env_file() {
  local target="$1"
  if [[ -f "$ENV_FILE" ]]; then
    # Update existing file
    jq --arg ns "$NAMESPACE" --arg stage "$STAGE" --arg target "$target" \
      '.[$ns][$stage] = $target' "$ENV_FILE" > "${ENV_FILE}.tmp" && mv "${ENV_FILE}.tmp" "$ENV_FILE"
  else
    # Create new file
    jq -n --arg ns "$NAMESPACE" --arg stage "$STAGE" --arg target "$target" \
      '{($ns): {($stage): $target}}' > "$ENV_FILE"
  fi
}

# Clone the target repository into a temporary directory
clone_repo() {
  TEMP_DIR=$(mktemp -d)
  echo "Cloning repository into temporary directory: $TEMP_DIR"
  git clone "$TARGET_REPO" "$TEMP_DIR"
}

# Copy files from the cloned repository to the local workspace
copy_files() {
  local source_dir="$1"
  echo "Copying files from $source_dir to current directory"
  cp -R "$source_dir/$NAMESPACE/$STAGE"/* .
}

# Clean up temporary directory
cleanup() {
  if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
    echo "Cleaning up temporary directory: $TEMP_DIR"
    rm -rf "$TEMP_DIR"
  fi
}

# Validate command-line arguments and set global variables
validate_args() {
  # Validate namespace and stage
  if [[ -z "${args[namespace]}" || -z "${args[stage]}" ]]; then
    echo "Error: Both namespace and stage must be specified."
    exit 1
  fi

  # Set global variables based on command-line arguments
  NAMESPACE="${args[namespace]}"
  STAGE="${args[stage]}"
  TARGET_REPO="${args[--target]}"
  REPO_DIR="${args[--repo-dir]}"

  # Check if either --target or --repo-dir is provided
  if [[ -n "$TARGET_REPO" && -n "$REPO_DIR" ]]; then
    echo "Error: Cannot specify both --target and --repo-dir."
    exit 1
  elif [[ -z "$TARGET_REPO" && -z "$REPO_DIR" ]]; then
    # If neither is provided, check env file for default values
    TARGET_REPO=$(read_default_target)
    if [[ -z "$TARGET_REPO" ]]; then
      echo "Error: No target repository specified, no --repo-dir provided, and no default found in $ENV_FILE"
      exit 1
    else
      echo "Using default target repository from $ENV_FILE"
    fi
  fi
}

initialize
validate_args

if [[ -n "$REPO_DIR" ]]; then
  # Use pre-cloned repository
  if [[ ! -d "$REPO_DIR" ]]; then
    echo "Error: Specified repo directory does not exist: $REPO_DIR"
    exit 1
  fi
  copy_files "$REPO_DIR"
else
  # Use target repository (either specified or from env.json)
  clone_repo
  copy_files "$TEMP_DIR"
  update_env_file "$TARGET_REPO"
  cleanup
fi

echo "Configuration update complete for namespace: $NAMESPACE, stage: $STAGE"