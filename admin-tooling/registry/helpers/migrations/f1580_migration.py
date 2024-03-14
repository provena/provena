from typing import Dict, Any, Dict, List, Callable
from SharedInterfaces.RegistryModels import RecordInfo
from SharedInterfaces.RegistryAPI import BundledItem, RecordType, ItemDataset, ReleasedStatus, ItemSubType, ItemModelRunWorkflowTemplate, ItemModelRun


def f1580_migrator_function(all_items: List[Dict[str, Any]], parse: bool = True) -> List[Dict[str, Any]]:
    # Find all templates and model runs
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

    # filter into the types (these are by reference so can modify directly)
    templates = list(filter(subtype_filter(
        ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE), all_items))
    model_runs = list(filter(subtype_filter(ItemSubType.MODEL_RUN), all_items))

    for template in templates:
        print(f"Processing template: " + template['id'])
        # get the version 
        software_version = template['item_payload']['software_version']

        # delete it
        del template['item_payload']['software_version']

        # and remove from all history 
        for hist_entry in template['item_payload']['history']:
            del hist_entry['item']['software_version']

        # find the relevant model runs
        for model_run in model_runs:
            print(f"looking at {model_run['id']} with template {model_run['item_payload']['record']['workflow_template_id']}")
            if model_run['item_payload']['record']['workflow_template_id'] == template['id']:
                print(f"Found matching model run " + model_run['id'])
                model_run['item_payload']['record']['model_version'] = software_version
        
    return all_items