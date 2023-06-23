function venv() {
  # function to setup python venv
  if [[ ! $reuse_venv ]]; then
    echo "Setting up venv"

    # clear any existing venv
    rm -rf .venv

    # create new and install requirements
    python3.10 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
  else
    echo "Reusing existing virtual environment"
    source .venv/bin/activate
  fi

}

function confirm {
  read -p "Are you sure you want to continue? (y/n) " answer
  if [ "$answer" != "y" ]; then
    echo "Aborted."
    return 1
  fi
}

# constants
empty_json_path="dumps/empty.json"
backup_path="dumps/${stage}/clear-app-stage-backup.json"

stage=${args[stage]}
reuse_venv=${args[--reuse_venv]}

# save starting point
current_dir=$(pwd)

# Step one  - import empty into registry and apply

echo "Moving to import/export tooling"
cd admin-tooling/registry

# setup venv
venv

echo "Creating empty json"
echo "[]" >${empty_json_path}

echo "Making a backup in ${backup_path} just in case!"
python import_export.py export-items ${stage} --output ${backup_path}

echo "About to clear ${stage}"
confirm || exit 1

echo "Running clear without apply, you may need to sign in"
python import_export.py import-items ${stage} ${empty_json_path} SYNC_DELETION_ALLOWED --allow-deletion

echo "About to apply clear on ${stage}"
confirm || exit 1

echo "Running clear with apply!"
python import_export.py import-items ${stage} ${empty_json_path} SYNC_DELETION_ALLOWED --apply --allow-deletion

echo "Import completed"

# Step two - clear graph
cd ${current_dir}

echo "Moving to graph tooling"
cd admin-tooling/prov-store

# setup venv
venv

echo "About to clear graph on stage: ${stage}"
confirm || exit 1

echo "Running graph clear op"
python graph_admin.py ${stage}

echo "Graph clear completed"

echo "Depending on usage of this stage, you may need to clear the user link service as well"
