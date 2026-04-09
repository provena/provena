"""
Direct DynamoDB registry export (bypasses the registry HTTP API).

Mirrors registry-api/helpers/admin_helpers.export_all_items and
registry-api/helpers/dynamo_helpers.list_all_items so the output matches
`import_export.py export-items` (JSON array of bundled items).
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import boto3
import typer
from ProvenaInterfaces.RegistryAPI import BundledItem
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params

# Typer CLI typing hint for parameters
ParametersType = List[str]

SAVE_DIRECTORY = "dumps"

env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

app = typer.Typer(pretty_exceptions_show_locals=False)


# --- Copied from registry-api/helpers/dynamo_helpers.remove_universal_key_attribute_from_item
#     so Dynamo items match the API export (universal_partition_key stripped).


def remove_universal_key_attribute_from_item(item: Dict[str, Any]) -> Dict[str, Any]:
    try:
        del item["universal_partition_key"]
    except Exception:
        pass
    return item


# --- Copied from registry-api/helpers/admin_helpers (consolidate_table_items, build_id_map, TableType)


class TableType(str, Enum):
    RESOURCE = "RESOURCE"
    LOCK = "LOCK"
    AUTH = "AUTH"


def build_id_map(item_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    item_map: Dict[str, Dict[str, Any]] = {}

    for item in item_list:
        if "id" not in item:
            dump = "Failed to dump contents."
            try:
                dump = json.dumps(item)
            except Exception:
                pass
            raise ValueError(f"Item was missing id property. Payload: {dump}.")
        item_map[item["id"]] = item

    return item_map


def consolidate_table_items(
    resource_items: List[Dict[str, Any]],
    lock_items: List[Dict[str, Any]],
    auth_items: List[Dict[str, Any]],
    source_of_truth: TableType = TableType.RESOURCE,
) -> List[BundledItem]:
    id_set: Set[str] = set()
    truth_items: Optional[List[Dict[str, Any]]] = None

    if source_of_truth == TableType.RESOURCE:
        truth_items = resource_items
    if source_of_truth == TableType.LOCK:
        truth_items = lock_items
    if source_of_truth == TableType.AUTH:
        truth_items = auth_items

    if truth_items is None:
        raise ValueError(
            f"The specified source of truth {source_of_truth} is not handled."
        )

    for item in truth_items:
        if "id" not in item:
            dump = "Failed to dump contents."
            try:
                dump = json.dumps(item)
            except Exception:
                pass
            raise ValueError(f"Item was missing id field. Payload: {dump}.")

        id_set.add(item["id"])

    resource_map = build_id_map(resource_items)
    lock_map = build_id_map(lock_items)
    auth_map = build_id_map(auth_items)

    bundled_items: List[BundledItem] = []
    for id in id_set:
        if id not in resource_map:
            raise KeyError(
                f"The resource item list does not contain the id {id} that was expected from the source of truth table {source_of_truth}."
            )
        if id not in lock_map:
            raise KeyError(
                f"The lock item list does not contain the id {id} that was expected from the source of truth table {source_of_truth}."
            )
        if id not in auth_map:
            raise KeyError(
                f"The auth item list does not contain the id {id} that was expected from the source of truth table {source_of_truth}."
            )

        bundled_items.append(
            BundledItem(
                id=id,
                item_payload=resource_map[id],
                lock_payload=lock_map[id],
                auth_payload=auth_map[id],
            )
        )

    return bundled_items


# --- Dynamo scan (same behaviour as registry-api/helpers/dynamo_helpers.list_all_items)


def list_all_items_from_table(table_name: str, region: Optional[str]) -> List[Dict[str, Any]]:
    kwargs: Dict[str, Any] = {}
    if region:
        kwargs["region_name"] = region
    table = boto3.resource("dynamodb", **kwargs).Table(table_name)

    items: List[Dict[str, Any]] = []
    response = table.scan()
    for item in response["Items"]:
        items.append(item)
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        for item in response["Items"]:
            items.append(item)

    return [remove_universal_key_attribute_from_item(dict(i)) for i in items]


# --- CloudFormation: resolve entity registry tables from stack logical IDs


def _ddb_tables_in_stack(cfn: Any, stack_name: str) -> List[Tuple[str, str]]:
    """Returns (LogicalResourceId, PhysicalResourceId) for DynamoDB tables."""
    out: List[Tuple[str, str]] = []
    paginator = cfn.get_paginator("list_stack_resources")
    for page in paginator.paginate(StackName=stack_name):
        for r in page["StackResourceSummaries"]:
            if r["ResourceType"] != "AWS::DynamoDB::Table":
                continue
            out.append((r["LogicalResourceId"], r["PhysicalResourceId"]))
    return out


def resolve_registry_tables_from_stack(stack_name: str, region: Optional[str]) -> Tuple[str, str, str]:
    """
    Finds resource / lock / auth registry tables by CloudFormation logical ID
    heuristics used by Provena CDK (constructs entity-registry, entity-registry-auth,
    entity-registry-lock).
    """
    kwargs: Dict[str, Any] = {}
    if region:
        kwargs["region_name"] = region
    cfn = boto3.client("cloudformation", **kwargs)

    rows = _ddb_tables_in_stack(cfn, stack_name)
    if not rows:
        raise ValueError(
            f"No AWS::DynamoDB::Table resources found in stack {stack_name!r}."
        )

    resource: Optional[str] = None
    lock_t: Optional[str] = None
    auth_t: Optional[str] = None

    for logical_id, physical_id in rows:
        lid = logical_id.lower()
        # Order matters: match lock/auth before generic "registry" resource table.
        if "registry" in lid and "lock" in lid:
            lock_t = physical_id
        elif "registry" in lid and "auth" in lid:
            auth_t = physical_id
        elif "registry" in lid and "lock" not in lid and "auth" not in lid:
            resource = physical_id

    if not (resource and lock_t and auth_t):
        lines = "\n".join(f"  {lid} -> {phys}" for lid, phys in sorted(rows))
        raise ValueError(
            "Could not classify registry resource / lock / auth tables from CloudFormation logical IDs. "
            "Pass --resource-table, --lock-table, and --auth-table explicitly.\n"
            f"DynamoDB tables in stack {stack_name!r}:\n{lines}"
        )

    return resource, lock_t, auth_t


def write_export_file(bundles: List[BundledItem], output: typer.FileTextWrite) -> None:
    """Same JSON shape as import_export.export_items (API export)."""
    payload = [json.loads(b.json()) for b in bundles]
    output.write(json.dumps(payload, indent=2))


@app.command("dump")
def dump_command(
    output: typer.FileTextWrite = typer.Option(
        f"{SAVE_DIRECTORY}/manual_export_" + str(datetime.now()) + ".json",
        help="Output path for the JSON array of bundled items (same format as export-items).",
    ),
    env_name: Optional[str] = typer.Option(
        None,
        help=f"Optional tooling environment; used for default AWS region ({valid_env_str}).",
    ),
    region: Optional[str] = typer.Option(
        None,
        help="AWS region for DynamoDB and CloudFormation. Overrides env_name region when set.",
    ),
    stack_name: Optional[str] = typer.Option(
        None,
        help="CloudFormation stack name; registry table names are resolved from stack resources.",
    ),
    resource_table: Optional[str] = typer.Option(
        None,
        help="Registry resource DynamoDB table name (overrides stack resolution).",
    ),
    lock_table: Optional[str] = typer.Option(
        None,
        help="Registry lock DynamoDB table name (overrides stack resolution).",
    ),
    auth_table: Optional[str] = typer.Option(
        None,
        help="Registry auth DynamoDB table name (overrides stack resolution).",
    ),
    param: ParametersType = typer.Option(
        [],
        help="Tooling environment parameter replacements, e.g. 'feature_number:1234'.",
    ),
) -> None:
    """
    Scan registry resource, lock, and auth DynamoDB tables and write the same bundled
    JSON as `export-items`, without calling the registry API (avoids HTTP 413 for large registries).
    """
    resolved_region = region
    if env_name:
        params = process_params(param)
        env = env_manager.get_environment(name=env_name, params=params)
        if resolved_region is None:
            resolved_region = env.aws_region

    table_args = (resource_table, lock_table, auth_table)
    if any(table_args) and not all(table_args):
        raise typer.BadParameter(
            "Provide all three of --resource-table, --lock-table, and --auth-table, or none of them."
        )

    if all(table_args):
        assert resource_table and lock_table and auth_table
        res, lck, auth = resource_table, lock_table, auth_table
    elif stack_name:
        res, lck, auth = resolve_registry_tables_from_stack(stack_name, resolved_region)
    else:
        raise typer.BadParameter(
            "Either specify --stack-name, or all of --resource-table, --lock-table, and --auth-table."
        )

    print(f"Scanning DynamoDB tables:\n  resource: {res}\n  lock: {lck}\n  auth: {auth}")
    if resolved_region:
        print(f"Region: {resolved_region}")

    resource_items = list_all_items_from_table(res, resolved_region)
    lock_items = list_all_items_from_table(lck, resolved_region)
    auth_items = list_all_items_from_table(auth, resolved_region)

    bundles = consolidate_table_items(
        resource_items=resource_items,
        lock_items=lock_items,
        auth_items=auth_items,
    )
    print(f"Writing {len(bundles)} bundled items")
    write_export_file(bundles, output)


@app.command("list-ddb-resources")
def list_ddb_resources(
    stack_name: str = typer.Argument(..., help="CloudFormation stack name."),
    env_name: Optional[str] = typer.Option(
        None,
        help=f"Optional tooling environment for default region ({valid_env_str}).",
    ),
    region: Optional[str] = typer.Option(None, help="AWS region (overrides env default)."),
    param: ParametersType = typer.Option([], help="Environment parameter replacements."),
) -> None:
    """Print DynamoDB table logical IDs and physical names for debugging stack resolution."""
    resolved_region = region
    if env_name:
        params = process_params(param)
        env = env_manager.get_environment(name=env_name, params=params)
        if resolved_region is None:
            resolved_region = env.aws_region

    kwargs: Dict[str, Any] = {}
    if resolved_region:
        kwargs["region_name"] = resolved_region
    cfn = boto3.client("cloudformation", **kwargs)
    rows = _ddb_tables_in_stack(cfn, stack_name)
    for lid, phys in sorted(rows):
        mark = ""
        ll = lid.lower()
        if "registry" in ll and "lock" in ll:
            mark = " (likely lock)"
        elif "registry" in ll and "auth" in ll:
            mark = " (likely auth)"
        elif "registry" in ll and "lock" not in ll and "auth" not in ll:
            mark = " (likely resource)"
        print(f"{lid} -> {phys}{mark}")
