#!/bin/bash -e

# check python and aws cli
python --version
aws --version

# move to feature manager folder  (assumes from base dir)
cd admin-tooling/prov-exporter

# install venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# export to given stage CSV detailed report
output_name="${STAGE}_detailed_export.csv"
python prov-exporter.py generate-export-aws DETAILED_LISTING ${output_name}

# now upload report to the specified bucket
prefix="${STAGE}_exports"
full_name="${prefix}/$(date +'%d_%m_%y_%H%M')_detailed.csv"

aws s3 cp ${output_name} s3://${BUCKET_NAME}/${full_name}
