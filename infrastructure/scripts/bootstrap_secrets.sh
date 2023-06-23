#!/bin/bash

wait_for_input() {
    read -p "Enter 'y' to continue or 'n' to abort: " choice
    if [[ $choice == "y" ]]; then
        echo "Continuing..."
    else
        echo "Aborting"
        exit 1
    fi
}

# Check if the first argument is present
if [[ -z "$1" ]]; then
    echo "Missing STAGE argument. Please provide the necessary input."
    exit 1
fi

stage=$1
echo "Working on stage $1, is this okay?"
wait_for_input


create_aws_secret() {
    local secret_name="$1"
    local client_id="$2"
    local description="$3"

    local secret_value=$(cat <<EOF
{
    "client_id": "$client_id",
    "client_secret": "TODO",
    "grant_type": "client_credentials"
}
EOF
)

    aws secretsmanager create-secret \
        --name "$secret_name" \
        --secret-string "$secret_value" \
        --description "$description"
}

echo "Checking AWS install"
aws --version
aws sts get-caller-identity 

echo "Does this look correct for your desired target account? Double check this!"
wait_for_input


echo "Creating secrets"

# Arrays with example values
client_ids=("data-store-api" "service_account_oidc_aws" "registry-api" "prov-api" "prov-job-dispatcher")
secret_names=("${stage}-data-store-api-service-account" "${stage}-data-store-api-oidc-service-account" "${stage}-registry-api-service-account" "${stage}-prov-api-service-account" "${stage}-prov-job-dispatcher-service-account")
descriptions=("Provides client id/client secret and grant type for the data store api keycloak client. Used by data store API automatically. Do not share." "Provides client id/client secret and grant type for the data store api OIDC keycloak client. Used by data store API automatically. Do not share." "Service account for the registry API enabling access to the handle service on behalf of users. Keep secret, do not share or use. Deployment only." "Service account for the prov API enabling access to the registry API on behalf of users. Keep secret, do not share or use. Deployment only." "Service account for the prov job dispatcher. lodges on behalf of the user. Do not share or use. Deployment only.")
cdk_variable_names=("data_store_api_service_account_arn" "data_store_oidc_service_account_arn" "registry_api_service_account_arn" "prov_api_service_account_arn" "prov_dispatcher_service_account_arn")


# Loop through the arrays
for ((i=0; i<${#client_ids[@]}; i++)); do
    create_aws_secret "${secret_names[i]}" "${client_ids[i]}" "${descriptions[i]}"
done

echo "Fetching created secrets and returning ARNs"
# Fetch ARNs for the created secrets using secret names
for ((i=0; i<${#client_ids[@]}; i++)); do
    secret_name=${secret_names[i]}
    secret_arn=$(aws secretsmanager describe-secret --secret-id "$secret_name" --query 'ARN' --output text)
    cdk_variable_name=${cdk_variable_names[i]}
    echo "$cdk_variable_name = \"$secret_arn\""
done