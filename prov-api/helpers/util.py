from pydantic import BaseModel
import json
from typing import Dict, Any, List

from ProvenaInterfaces.RegistryAPI import ItemBase, ItemSubType

def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    return json.loads(model.json(exclude_none=True))


def filter_nodes(nodes: List[Any], explore_type: str, filtered: Dict[str,List[ItemBase]]) -> None: 
     
    for node in nodes: 
            if node.get('item_subtype') == ItemSubType.MODEL or node.get('item_subtype') == ItemSubType.DATASET:
                filtered[explore_type].append(node)

            elif node.get('item_subtype') == ItemSubType.MODEL_RUN:
                filtered["model_runs"].append(node)


def filter_for_export_prov_graph(upstream_nodes: List[Any], downstream_nodes: List[Any]) -> Dict[str,List[ItemBase]]: 

    # Filter through both the upstream and downstream nodes. 

    filtered_response: Dict[str,List[ItemBase]] = {
        "inputs": [], 
        "model_runs": [], 
        "outputs": []
    }

    filter_nodes(nodes= upstream_nodes, explore_type="inputs", filtered= filtered_response)
    filter_nodes(nodes= downstream_nodes, explore_type="outputs", filtered=filtered_response)

    return filtered_response



# Wrapper around the validate_by method for study and model runs 
