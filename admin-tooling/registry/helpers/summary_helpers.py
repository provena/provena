
from SharedInterfaces.RegistryAPI import *
from SharedInterfaces.AuthAPI import AdminLinkUserLookupResponse
from typing import Dict, Any
import typer
from rich import print
from ToolingEnvironmentManager.Management import EnvironmentManager, PopulatedToolingEnvironment
import requests


def get_username_link(username: str, env: PopulatedToolingEnvironment, auth: Any) -> Optional[str]:
    """

    Fetches the linked person ID for a given user. If none -> no link.

    Uses admin link lookup service.

    Args:
        username (str): The username to fetch
        env (PopulatedToolingEnvironment): Env to target
        auth (Any): Auth function

    Returns:
        Optional[str]: Handle ID of person if linked
    """
    auth_endpoint = env.auth_api_endpoint

    res = requests.get(
        url=f"{auth_endpoint}/link/admin/lookup",
        params={'username': username},
        auth=auth()
    )

    assert res.status_code == 200, f"Non 200 code: {res.status_code}, error msg: {res.text}."

    json_content = res.json()
    check_res = AdminLinkUserLookupResponse.parse_obj(json_content)

    return check_res.person_id


def get_all_datasets(env: PopulatedToolingEnvironment, auth: Any) -> List[ItemDataset]:
    """

    Lists all datasets from the data-store-api

    Args:
        env (PopulatedToolingEnvironment): The env to target
        auth (Any): The auth function () => BearerAuth

    Returns:
        List[ItemDataset]: The list of datasets
    """
    ds_endpoint = env.datastore_api_endpoint

    pag_key: Any = None
    complete = False
    page_size = 50
    items: List[ItemDataset] = []

    while not complete:
        res = requests.post(
            url=f"{ds_endpoint}/registry/items/list",
            json=NoFilterSubtypeListRequest(
                page_size=page_size,
                pagination_key=pag_key
            ).dict(),
            auth=auth()
        )

        assert res.status_code == 200, f"Non 200 code: {res.status_code}, error msg: {res.text}."

        json_content = res.json()
        list_response = DatasetListResponse.parse_obj(json_content)

        assert list_response.status.success, f"Non success: {list_response.status.details}."

        if list_response.items:
            items.extend(list_response.items)

        pag_key = list_response.pagination_key

        if not pag_key:
            complete = True

    return items


def perform_dataset_link_audit(
    env: PopulatedToolingEnvironment,
    output: typer.FileTextWrite,
    get_auth: Any,
) -> None:
    """
    Lists all datasets, and then checks if the registered owner username is linked. 

    Produces an output audit with this information as well as other summary statistics.

    Uses the admin link user service so authorised user must have auth api admin permission.
    """

    # step one - list all datasets
    print("Getting all datasets...")
    print()
    datasets = get_all_datasets(env=env, auth=get_auth)

    # step two - map username to dataset(s)
    username_to_dataset_list: Dict[str, List[ItemDataset]] = {}
    for ds in datasets:
        user = ds.owner_username
        user_datasets = username_to_dataset_list.get(user, [])
        user_datasets.append(ds)
        username_to_dataset_list[user] = user_datasets

    # step three - get set of usernames and map to linked user (if any)
    print("Getting all username links...")
    print()
    username_set: Set[str] = set(username_to_dataset_list.keys())
    username_to_linked_person: Dict[str, Optional[str]] = {}
    for user in username_set:
        username_to_linked_person[user] = get_username_link(
            username=user,
            env=env,
            auth=get_auth
        )

    # step four - cross reference and get a report mapping linked/unlinked users to datasets
    print("Building report...")
    print()

    report_content: str = "REPORT\n\n"

    # PART A list of unlinked users with datasets
    report_content += "UNLINKED USERS (with datasets):\n\n"
    count = 0
    for user, link in username_to_linked_person.items():
        if link is None:
            count += 1
            report_content += f"{user}\n"

    report_content += f"Total unlinked user count: {count}\n"
    report_content += "-------------------------------------\n\n\n"

    # PART B list of linked users with datasets
    report_content += "LINKED USERS (with datasets):\n\n"
    count = 0
    for user, link in username_to_linked_person.items():
        if link is not None:
            count += 1
            report_content += f"User: {user}, linked to: {link}\n"

    report_content += f"Total linked user count: {count}\n"
    report_content += "-------------------------------------\n\n\n"

    # PART C list of datasets by person + count + linked/unlinked
    report_content += "DATASET STATISTICS\n\n"
    dataset_count = 0
    user_count = 0

    for user, link in username_to_linked_person.items():
        user_count += 1
        dataset_list = username_to_dataset_list[user]
        dataset_count += len(dataset_list)
        linked = link is not None
        dataset_str = "\n".join(
            [ds.collection_format.dataset_info.name for ds in dataset_list])
        report_content += f"User: {user}, this user is {'LINKED' if linked else 'UNLINKED'}.\nDatasets ({len(dataset_list)}):\n"
        report_content += dataset_str + "\n\n"

    report_content += f"Total dataset count: {dataset_count}\n"
    report_content += f"Total user count: {user_count}\n"
    report_content += "-------------------------------------"

    print("Dumping report...")
    print()

    print(report_content)

    print(f"Writing report to {output.name}...")
    print()

    output.write(report_content)
    output.close()
