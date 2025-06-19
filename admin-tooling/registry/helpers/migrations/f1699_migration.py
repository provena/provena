from typing import Dict, Any, Dict, List, Callable
from ProvenaInterfaces.RegistryModels import RecordInfo
from ProvenaInterfaces.RegistryAPI import BundledItem, RecordType, ItemDataset, ReleasedStatus, ItemSubType, ItemModelRunWorkflowTemplate, ItemModelRun


def f1699_migrator_function(all_items: List[Dict[str, Any]], parse: bool = True) -> List[Dict[str, Any]]:
    # Find all dataset items as the migration applies only to them
    def subtype_filter(subtype: ItemSubType) -> Callable[[Dict[str, Any]], bool]:
        def temp_filter(item: Dict[str, Any]) -> bool:
            reg_item = BundledItem.parse_obj(item)

            # pull out the item payload
            payload = reg_item.item_payload

            # check the type of the item and apply suitable modifiers if applicable
            record_base = RecordInfo.parse_obj(payload)

            if record_base.record_type == RecordType.COMPLETE_ITEM and record_base.item_subtype == subtype:
                return True

            return False

        return temp_filter
    
    datasets = list(filter(subtype_filter(ItemSubType.DATASET), all_items))
    for ds in datasets:
        # for current metadata
        created_date = ds['item_payload']['collection_format']['dataset_info']['created_date']
        published_date = ds['item_payload']['collection_format']['dataset_info']['published_date']
        assert type(created_date) == str, f"created_date is not a string: {created_date}"
        assert type(published_date) == str, f"published_date is not a string: {published_date}"
        # delete them from dataset info and add the new one (at the same time)
        ds['item_payload']['collection_format']['dataset_info']['created_date'] = {
            "relevant": True, # maybe needs to be string?
            "value": created_date
        }
        ds['item_payload']['collection_format']['dataset_info']['published_date'] = {
            "relevant": True,
            "value": published_date
        }

        # for each history entry
        for hist_entry in ds['item_payload']['history']:
            created_date = hist_entry['item']['collection_format']['dataset_info']['created_date']
            published_date = hist_entry['item']['collection_format']['dataset_info']['published_date']
            assert type(created_date) == str, f"created_date is not a string: {created_date}"
            assert type(published_date) == str, f"published_date is not a string: {published_date}"
            # delete them from dataset info and add the new one (at the same time)
            hist_entry['item']['collection_format']['dataset_info']['created_date'] = {
                "relevant": True,
                "value": created_date
            }
            hist_entry['item']['collection_format']['dataset_info']['published_date'] = {
                "relevant": True,
                "value": published_date
            }


    return all_items
