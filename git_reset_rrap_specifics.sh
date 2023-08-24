#!/bin/bash

# Which paths to reset? These represent files/paths which have rrap specific info to exclude
paths=(
    "README.md"
    "utility_infrastructure"
    "fb"
    ".github/pull_request_template.md"
    "admin-tooling/environments.json"
    "admin-tooling/README.md"
    "admin-tooling/functionality-tests"
    "featb"
    "feature-branch-manager"
    "github-tools"
    "infrastructure/configs/provena"
    "infrastructure/configs/rrap"
    "infrastructure/configs/config_map.py"
    "infrastructure/provena/keycloak/themes"
    "infrastructure/provena/utility_stacks"

    "registry-api/thunder-tests"
    "data-store-api/thunder-tests"
    "auth-api/thunder-tests"
    "job-api/thunder-tests"
    "prov-api/thunder-tests"
    "search-api/thunder-tests"
    "identity-service/thunder-tests"

    "data-store-ui/.env.dev"
    "data-store-ui/.env.feat"
    "data-store-ui/.env.peter"
    "data-store-ui/.env.prod"
    "data-store-ui/.env.stage"
    "data-store-ui/.env.test"
    "landing-portal-ui/.env.dev"
    "landing-portal-ui/.env.peter"
    "landing-portal-ui/.env.feat"
    "landing-portal-ui/.env.prod"
    "landing-portal-ui/.env.stage"
    "landing-portal-ui/.env.test"
    "prov-ui/.env.dev"
    "prov-ui/.env.peter"
    "prov-ui/.env.feat"
    "prov-ui/.env.prod"
    "prov-ui/.env.stage"
    "prov-ui/.env.test"
    "registry-ui/.env.dev"
    "registry-ui/.env.peter"
    "registry-ui/.env.feat"
    "registry-ui/.env.prod"
    "registry-ui/.env.stage"
    "registry-ui/.env.test"
)

# Loop through the array and run git reset -- <path> for each string
for path in "${paths[@]}"; do
    git reset -- "$path"
done
