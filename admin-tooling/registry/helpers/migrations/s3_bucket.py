from typing import Dict, Any
from ProvenaInterfaces.RegistryAPI import BundledItem, ItemDataset, S3Location
import json


def update_s3_location(old_bucket_name: str, new_bucket_name: str, old_item: Dict[str, Any]) -> Dict[str, Any]:
    # Parse the item as a registry item and dataset
    reg_item = BundledItem.parse_obj(old_item)
    resource = reg_item.item_payload

    if resource.get("item_subtype") != "DATASET":
        return old_item

    print("Dataset found - migrating:")
    data_store = ItemDataset.parse_obj(resource)

    # Update the item
    current_bucket = data_store.s3.bucket_name
    current_path = data_store.s3.path
    current_uri = data_store.s3.s3_uri

    # check things make sense
    if (current_bucket not in [old_bucket_name]):
        if (current_bucket == new_bucket_name):
            print(
                f"Warning, item {data_store.id} seems to be already be at the new location. Ignoring...")
        else:
            print(f"Unexpected origin bucket: {current_bucket}")
            raise ValueError()

    # Create new paths
    # update bucket
    new_bucket = new_bucket_name
    # update uri based on existing path + buckt
    new_uri = f"s3://{new_bucket}/{current_path}"
    # keep the old path
    new_path = current_path

    data_store.s3 = S3Location(
        bucket_name=new_bucket,
        path=new_path,
        s3_uri=new_uri
    )

    old_item["item_payload"] = json.loads(data_store.json(exclude_none=True))

    print(f"Migration complete for id: {data_store.id}")
    return old_item
