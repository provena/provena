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

# Constants
pre_migration_prefix="f1699_pre"
post_migration_prefix="f1699_post"

apply=${args[--apply]}
stage=${args[stage]}
reuse_venv=${args[--reuse_venv]}

# generate the apply part of argument if supplied
apply_arg=""
if [[ $apply ]]; then
    echo "Changes will be applied since --apply flag was specified"
    apply_arg="--apply"
fi

# save starting point
current_dir=$(pwd)

# Step one  - export registry

echo "Moving to export tooling"
cd admin-tooling/registry

# setup venv
venv

echo "Running export, you may need to sign in"

export_output_name="dumps/${pre_migration_prefix}_${stage}.json"
migration_output_name="dumps/${post_migration_prefix}_${stage}.json"

python import_export.py export-items ${stage} --output ${export_output_name}

echo "Export completed"

# Step two - migrate the items (uses migrations script in admin tooling)
cd ${current_dir}

echo "Moving to migration tooling"
cd admin-tooling/registry

echo "Venv already setup here"

echo "Running migration"
python import_export.py modifiers f1699-migration ${stage} ${export_output_name} ${migration_output_name}

echo "Migration completed locally - running import to registry"

# Step three - import the items
cd ${current_dir}

echo "Moving to import tooling"
cd admin-tooling/registry

echo "Venv already setup here"

echo "Running import"
python import_export.py import-items ${stage} ${migration_output_name} SYNC_ADD_OR_OVERWRITE ${apply_arg}

echo "Process completed"
