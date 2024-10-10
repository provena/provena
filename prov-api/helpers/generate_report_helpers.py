from typing import Dict, List, Any 
from config import Config
from fastapi import HTTPException

from ProvenaInterfaces.ProvenanceAPI import LineageResponse
from ProvenaInterfaces.RegistryAPI import ItemBase, ItemSubType, SeededItem
from helpers.entity_validators import RequestStyle, validate_model_run_id, validate_study_id

from routes.explore.explore import explore_downstream, explore_upstream


async def validate_node_id(node_id: str, item_subtype: ItemSubType, request_style: RequestStyle, config: Config) -> None: 
    
    if item_subtype == ItemSubType.MODEL_RUN:
        response = await validate_model_run_id(id=node_id, request_style=request_style, config=config)
    elif item_subtype == ItemSubType.STUDY:
        response = await validate_study_id(id=node_id, request_style=request_style, config=config)
    else:
        raise HTTPException(status_code=400, detail="Unsupported item subtype for validation.")

    if isinstance(response, str):
        raise HTTPException(status_code=400, detail=f"Validation error with provided {item_subtype.value}: {response}")
    
    if isinstance(response, SeededItem):
        raise HTTPException(status_code=400, detail="Seeded item cannot be used for this query!")
    

def filter_nodes(nodes: List[Any], explore_type: str, filtered: Dict[str,List[ItemBase]]) -> None: 
     
    for node in nodes: 
            if node.get('item_subtype') == ItemSubType.MODEL or node.get('item_subtype') == ItemSubType.DATASET:
                filtered[explore_type].append(node)

            elif node.get('item_subtype') == ItemSubType.MODEL_RUN:
                filtered["model_runs"].append(node)


def filter_for_export_prov_graph(upstream_nodes: List[ItemBase], downstream_nodes: List[ItemBase]) -> Dict[str,List[ItemBase]]: 

    # Filter through both the upstream and downstream nodes. 

    filtered_response: Dict[str,List[ItemBase]] = {
        "inputs": [], 
        "model_runs": [], 
        "outputs": []
    }

    filter_nodes(nodes= upstream_nodes, explore_type="inputs", filtered= filtered_response)
    filter_nodes(nodes= downstream_nodes, explore_type="outputs", filtered=filtered_response)

    return filtered_response



async def generate_report_helper(starting_id: str, upstream_depth: int, shared_responses: Dict[str, List[ItemBase]], config: Config, downstream_depth: int = 1) -> None:

    upstream_response: LineageResponse = await explore_upstream(starting_id=starting_id, depth=upstream_depth, config=config)
    downstream_response: LineageResponse = await explore_downstream(starting_id=starting_id, depth=downstream_depth, config=config)
        
    assert upstream_response.graph, "Node collections not found!"
    assert downstream_response.graph, "Node collections not found!"

    nodes_upstream: List[ItemBase] = upstream_response.graph.get('nodes', [])
    nodes_downstream: List[ItemBase] = downstream_response.graph.get('nodes', [])

    filtered_response = filter_for_export_prov_graph(upstream_nodes=nodes_upstream, 
                                                    downstream_nodes=nodes_downstream)
    
    # Add the results. 
    shared_responses["inputs"].extend(filtered_response["inputs"])
    shared_responses["model_runs"].extend(filtered_response["model_runs"])
    shared_responses["outputs"].extend(filtered_response["outputs"])    