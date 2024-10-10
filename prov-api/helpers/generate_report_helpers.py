from typing import Dict, List, Any

from pydantic import ValidationError 
from config import Config
from fastapi import HTTPException

from ProvenaInterfaces.ProvenanceAPI import LineageResponse
from ProvenaInterfaces.RegistryAPI import ItemBase, ItemSubType, SeededItem, Node
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
    

def filter_for_export_prov_graph(upstream_nodes: List[Node], downstream_nodes: List[Node]) -> Dict[str,List[Node]]: 

    # Filter through both the upstream and downstream nodes. 

    filtered_response: Dict[str,List[Node]] = {
        "inputs": [], 
        "model_runs": [], 
        "outputs": []
    }

    # Small helper function to process the node and add it accordingly. 
    def process_node(node: Node, node_type: str) -> None: 
        if node.item_subtype in [ItemSubType.MODEL, ItemSubType.DATASET]:
            filtered_response[node_type].append(node)
        elif node.item_subtype == ItemSubType.MODEL_RUN:
            filtered_response["model_runs"].append(node)
    
    for node in upstream_nodes:
        process_node(node, "inputs")

    for node in downstream_nodes: 
        process_node(node, "outputs")

    return filtered_response

def parse_nodes(node_list: List[Any]) -> List[Node]: 

    # This function parses a list of "potential" nodes into the Node Pydantic Interface.  

    node_list_parsed: List[Node] = []

    if len(node_list) == 0: 
        # Do I handle this? Can there be a case where a model run does not have any assoicated inputs/outputs??
        raise HTTPException(status_code=400, detail="Cannot process the report generation.")

    try:
        for node in node_list: 
            node_list_parsed.append(Node(**node))
    except ValidationError as e: 
        raise HTTPException(status_code=400, detail="Something has gone wrong in parsing this node.")
        
    return node_list_parsed


async def generate_report_helper(starting_id: str, upstream_depth: int, shared_responses: Dict[str, List[Node]], config: Config, downstream_depth: int = 1) -> None:

    upstream_response: LineageResponse = await explore_upstream(starting_id=starting_id, depth=upstream_depth, config=config)
    downstream_response: LineageResponse = await explore_downstream(starting_id=starting_id, depth=downstream_depth, config=config)
        
    assert upstream_response.graph, "Node collections not found!"
    assert downstream_response.graph, "Node collections not found!"

    nodes_upstream: List[Any] = upstream_response.graph.get('nodes', [])
    nodes_downstream: List[Any] = downstream_response.graph.get('nodes', [])

    # Parsing the nodes.
    upstream_nodes_parsed = parse_nodes(nodes_upstream)
    downstream_nodes_parsed = parse_nodes(nodes_downstream)

    filtered_response = filter_for_export_prov_graph(upstream_nodes=upstream_nodes_parsed, 
                                                    downstream_nodes=downstream_nodes_parsed)
    
    # Add the results. 
    shared_responses["inputs"].extend(filtered_response["inputs"])
    shared_responses["model_runs"].extend(filtered_response["model_runs"])
    shared_responses["outputs"].extend(filtered_response["outputs"])    