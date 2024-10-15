import io
import os
from typing import Dict, List, Any, Callable, ByteString

from pydantic import ValidationError 
from config import Config
from fastapi import HTTPException

from ProvenaInterfaces.ProvenanceAPI import LineageResponse
from ProvenaInterfaces.RegistryAPI import ItemBase, ItemSubType, SeededItem, Node
from helpers.entity_validators import RequestStyle, validate_model_run_id, validate_study_id
from helpers.neo4j_helpers import upstream_query, downstream_query

from tempfile import NamedTemporaryFile

from docx import Document
from docx.shared import Inches

async def validate_node_id(node_id: str, item_subtype: ItemSubType, request_style: RequestStyle, config: Config) -> None: 
    """_summary_

    Parameters
    ----------
    node_id : str
        _description_
    item_subtype : ItemSubType
        _description_
    request_style : RequestStyle
        _description_
    config : Config
        _description_

    Raises
    ------
    HTTPException
        _description_
    HTTPException
        _description_
    HTTPException
        _description_
    """
    
    validation_mapping: Dict[ItemSubType, Callable] = {
        ItemSubType.MODEL_RUN: validate_model_run_id,
        ItemSubType.STUDY: validate_study_id
    }

    validator_func = validation_mapping.get(item_subtype)

    if not validator_func:
        raise HTTPException(status_code=400, detail="Unsupported item subtype for validation.")
    
    response = await validator_func(id=node_id, request_style=request_style, config=config)

    if isinstance(response, str):
        raise HTTPException(status_code=400, detail=f"Validation error with provided {item_subtype.value}: {response}")
    
    if isinstance(response, SeededItem):
        raise HTTPException(status_code=400, detail="Seeded item cannot be used for this query!")
    

def filter_for_export_prov_graph(upstream_nodes: List[Node], downstream_nodes: List[Node]) -> Dict[str,List[Node]]: 
    """_summary_

    Parameters
    ----------
    upstream_nodes : List[Node]
        _description_
    downstream_nodes : List[Node]
        _description_

    Returns
    -------
    Dict[str,List[Node]]
        _description_
    """

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
    """_summary_

    Parameters
    ----------
    node_list : List[Any]
        _description_

    Returns
    -------
    List[Node]
        _description_

    Raises
    ------
    HTTPException
        _description_
    HTTPException
        _description_
    """

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
    """_summary_

    Parameters
    ----------
    starting_id : str
        _description_
    upstream_depth : int
        _description_
    shared_responses : Dict[str, List[Node]]
        _description_
    config : Config
        _description_
    downstream_depth : int, optional
        _description_, by default 1
    """

    upstream_response: Dict[str, Any] = upstream_query(starting_id=starting_id, depth=upstream_depth, config=config)
    downstream_response: Dict[str, Any] = downstream_query(starting_id=starting_id, depth=downstream_depth, config=config)

    print(upstream_response, downstream_response)

    assert upstream_response.get('graph'), "Node collections not found!"
    assert downstream_response.get('graph'), "Node collections not found!"

    nodes_upstream: List[Any] = upstream_response['graph'].get('nodes', [])
    nodes_downstream: List[Any] = downstream_response['graph'].get('nodes', [])

    # Parsing the nodes.
    upstream_nodes_parsed: List[Node] = parse_nodes(nodes_upstream)
    downstream_nodes_parsed: List[Node] = parse_nodes(nodes_downstream)

    filtered_response = filter_for_export_prov_graph(upstream_nodes=upstream_nodes_parsed, 
                                                    downstream_nodes=downstream_nodes_parsed)
    
    # Add the results. 
    shared_responses["inputs"].extend(filtered_response["inputs"])
    shared_responses["model_runs"].extend(filtered_response["model_runs"])
    shared_responses["outputs"].extend(filtered_response["outputs"])    


def generate_word_file() -> str: 
    """Generates and creates a temporary word file. 
    TODO: Need to add the list of collected nodes into here for processing into table.

    Returns
    -------
    str
        The newly created temporary file path.
    """

    # Need to convert/parse into a suitable format that can be iterated through. 

    document = Document()
    document.add_heading('Model Run Study Close Out Report', 0)

    p = document.add_paragraph('A plain paragraph having some ')
    p.add_run('bold').bold = True
    p.add_run(' and some ')
    p.add_run('italic.').italic = True

    # Need to temporarily save the document in some form (either on the server) or in memory

    with NamedTemporaryFile(delete=False, suffix='.docx') as tmpFile: 
        document.save(tmpFile.name)
        # Return the path of the temporary file.
        return tmpFile.name


def remove_word_file(file_path: str) -> None: 
    """_summary_
    """

    os.remove(file_path)



