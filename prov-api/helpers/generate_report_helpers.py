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
    """Validates that a provided node (id + subtype) does exist within the registry.

    Parameters
    ----------
    node_id : str
        The ID of the node.
    item_subtype : ItemSubType
        The subtype of the node.
    request_style : RequestStyle
        The style of the request (user, service account etc)
    config : Config
        A config object containing information about the different endpoints of the system.

    Raises
    ------
    HTTPException
        If an invalid subtype is provided.
    HTTPException
        If fetched entity contains an error this exception is raised.
    HTTPException
        If the fetched entity is of type SeededItem this exception is raised.
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
    """Takes a list of upstream and downstream nodes and processes them into into different categories of 
    inputs, models and outputs. 

    Parameters
    ----------
    upstream_nodes : List[Node]
        A list of all upstream nodes. 
    downstream_nodes : List[Node]
        A list of all downstream nodes.

    Returns
    -------
    Dict[str,List[Node]]
        A dictionary containing the "inputs", "outputs" and "model-runs" involved within the study/model-run.
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
    """Parses a list of potential nodes into a list of Valid Node objects.

    This function takes a list of potential nodes, attempts to parse them into 
    the Node Pydantic model, and returns a list of validated Node objects. 

    Parameters
    ----------
    node_list : List[Any]
        A list of items that can potentially be parsed as Node objects.

    Returns
    -------
    List[Node]
        A list of parsed Node objects.


    Raises
    ------
    HTTPException
        Raised if the provided node_list is empty.
    HTTPException
        Raised if validation fails while parsing any node in the list.
    """

    node_list_parsed: List[Node] = []

    if len(node_list) == 0: 
        # Do I handle this? Can there be a case where a model run does not have any assoicated inputs/outputs?? - I don't think so.
        raise HTTPException(status_code=400, detail="Cannot process the report generation.")
    try:
        for node in node_list: 
            node_list_parsed.append(Node(**node))
    except ValidationError as e: 
        raise HTTPException(status_code=400, detail="Something has gone wrong in parsing this node.")
        
    return node_list_parsed


async def generate_report_helper(starting_id: str, upstream_depth: int, shared_responses: Dict[str, List[Node]], config: Config, downstream_depth: int = 1) -> None:
    """Generates the report by querying upstream and downstream data, parsing nodes, and filtering results.

    This helper function performs upstream and downstream queries, parses the node responses, filters them 
    for relevant data, and stores the results into a shared dictionary for further report generation.

    Parameters
    ----------
    starting_id : str
        The starting node ID to perform the queries from.
    upstream_depth : int
        The depth of the upstream query to traverse upto.
    shared_responses : Dict[str, List[Node]]
        A dictionary which contains the parsed and filtered nodes. 
        Contains 'inputs', 'model_runs', and 'outputs' as keys.
    config : Config
        A config object containing information about the different endpoints of the system.
    downstream_depth : int, optional
        The depth of the downstream query to traverse to, by default 1
    """

    upstream_response: Dict[str, Any] = upstream_query(starting_id=starting_id, depth=upstream_depth, config=config)
    downstream_response: Dict[str, Any] = downstream_query(starting_id=starting_id, depth=downstream_depth, config=config)

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
    """Generates and creates a temporary word file using Python-docx.
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


def remove_file(file_path: str) -> None: 
    """Deletes the specified file from the server.

    Parameters
    ----------
    file_path : str
        The file path of the document to be deleted.
    """

    os.remove(file_path)



