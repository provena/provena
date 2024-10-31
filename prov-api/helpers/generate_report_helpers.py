import io
import os
from typing import Dict, List, Any, Callable, Tuple, Set, Optional
from dataclasses import dataclass, field
from enum import Enum

from pydantic import ValidationError 
from config import Config
from fastapi import HTTPException

from KeycloakFastAPI.Dependencies import ProtectedRole
from ProvenaInterfaces.RegistryAPI import ItemBase, ItemSubType, SeededItem, Node
from helpers.entity_validators import RequestStyle, validate_model_run_id, validate_study_id
from helpers.prov_connector import upstream_query, downstream_query
from helpers.registry_helpers import fetch_item_from_registry_with_subtype

from tempfile import NamedTemporaryFile

from docx import Document
from docx.text.paragraph import Paragraph
from docx.shared import RGBColor
import docx
from docx.shared import Inches

class NodeType(str, Enum): 
    INPUTS = "inputs"
    MODEL_RUNS = "model_runs"
    OUTPUTS = "outputs"

class NodeDirection(str, Enum):
    UPSTREAM = "UPSTREAM"
    DOWNSTREAM = "DOWNSTREAM"

@dataclass
class ReportNodeCollection():
    
    inputs: List[ItemBase] = field(default_factory=list)
    model_runs: List[ItemBase] = field(default_factory=list)
    outputs: List[ItemBase] = field(default_factory=list)
    
    # Additional sets to track unique IDs for each category
    input_ids: Set[str] = field(default_factory=set)
    model_run_ids: Set[str] = field(default_factory=set)
    output_ids: Set[str] = field(default_factory=set)

    def add_node(self, node: ItemBase, node_type: NodeType) -> None:

        # Handle nodes of type MODEL_RUN
        if node.item_subtype == ItemSubType.MODEL_RUN and node.id not in self.model_run_ids:
            self.model_runs.append(node)
            self.model_run_ids.add(node.id)
        
        # Handle input nodes (datasets and models)
        elif node_type == NodeType.INPUTS and node.item_subtype in {ItemSubType.MODEL, ItemSubType.DATASET} and node.id not in self.input_ids:
            self.inputs.append(node)
            self.input_ids.add(node.id)
        
        # Handle output nodes (datasets only)
        elif node_type == NodeType.OUTPUTS and node.item_subtype == ItemSubType.DATASET and node.id not in self.output_ids:
            self.outputs.append(node)
            self.output_ids.add(node.id)
        
async def validate_node_id(node_id: str, item_subtype: ItemSubType, request_style: RequestStyle, config: Config) -> None: 
    """Validates that a provided node (id + subtype) does exist within the registry.
    This only currently works with Model Runs and Study Entities. 

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

    try:
        
        validation_mapping: Dict[ItemSubType, Callable] = {
            ItemSubType.MODEL_RUN: validate_model_run_id,
            ItemSubType.STUDY: validate_study_id
        }

        validator_func = validation_mapping.get(item_subtype)

        if not validator_func:
            raise HTTPException(status_code=400, detail=f"Unsupported item subtype for validation.\
                                Received subtype {item_subtype.value}, but the supported subtypes\
                                are {','.join(validation_mapping.keys())}")
        
        response = await validator_func(id=node_id, request_style=request_style, config=config)

        if isinstance(response, str):
            raise HTTPException(status_code=400, detail=f"Validation error with provided {item_subtype.value}: {response}")
        
        if isinstance(response, SeededItem):
            raise HTTPException(status_code=400, detail=f"Seeded item with provided {item_subtype.value} cannot be used for this query!")
    
    except HTTPException as e: 
        raise e
    
    except Exception as e: 
        raise HTTPException(status_code=500, detail=f"Error when validating study or model run entities: {str(e)}")


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

    # Worst case scenario handling, this is unlikely to happen.
    if len(node_list) == 0:
        raise HTTPException(status_code=400, detail="Cannot process the report generation. Node list is empty.")
    
    try:
        
        for node in node_list:
            try: 
                node_list_parsed.append(Node(**node))
            except ValidationError as e:
                # The node object has not been parsed, so not safe to get it directly. 
                node_id = node.get('id', 'undefined id')
                raise HTTPException(status_code=400, detail=f"Validation error in node with id {node_id}. Error {str(e)}")
            except Exception as e: 
                raise HTTPException(status_code=500, detail=f"Error parsing nodes - {str(e)}")
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during node parsing - {str(e)}")
    
    return node_list_parsed


async def generate_report(user: ProtectedRole, starting_id: str, upstream_depth: int, config: Config, collection_shared: ReportNodeCollection) -> ReportNodeCollection:
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

    collection = await fetch_parse_all_upstream_downstream_nodes(
                                                    user = user, 
                                                    starting_id=starting_id, 
                                                    upstream_depth=upstream_depth,
                                                    config=config,
                                                    collection = collection_shared)

    return collection

async def fetch_parse_all_upstream_downstream_nodes(user: ProtectedRole, 
                                                    starting_id: str, 
                                                    upstream_depth: int, 
                                                    config: Config, 
                                                    collection: ReportNodeCollection,
                                                    downstream_depth: int = 1, 
                                                    ) -> ReportNodeCollection: 
    
    """_summary_

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    HTTPException
        _description_
    HTTPException
        _description_
    """
    
    try:

        # Fetch both upstream and downstream nodes.
        upstream_response: Dict[str, Any] = upstream_query(starting_id=starting_id, depth=upstream_depth, config=config)
        downstream_response: Dict[str, Any] = downstream_query(starting_id=starting_id, depth=downstream_depth, config=config)

        assert upstream_response.get('nodes'), "Upstream node collections not found!"
        assert downstream_response.get('nodes'), "Downstream node collections not found!"

        nodes_upstream: List[Any] = upstream_response.get('nodes', [])
        nodes_downstream: List[Any] = downstream_response.get('nodes', [])

        # Process the nodes in both directions 
        await process_node_collection(
            nodes = nodes_upstream, 
            direction = NodeDirection.UPSTREAM,
            user = user,
            config = config,
            collection = collection
        )

        await process_node_collection(
            nodes = nodes_downstream,
            direction = NodeDirection.DOWNSTREAM,
            user = user, 
            config = config,
            collection = collection
        )

        return collection
            
    except AssertionError as e: 
        raise HTTPException(status_code=404, detail=f"The provided model run with id {starting_id} - error: {str(e)}")
    
    except Exception as e: 
        raise HTTPException(status_code=500, detail=f"Error fetching upstream/downstream nodes - error: {str(e)}")


async def process_node_collection(
        nodes: List[Any], 
        direction: NodeDirection,
        user: ProtectedRole, 
        config: Config, 
        collection: ReportNodeCollection
) -> ReportNodeCollection:
    
    parsed_nodes = parse_nodes(nodes)
    node_type = NodeType.INPUTS if direction == NodeDirection.UPSTREAM else NodeType.OUTPUTS

    for node in parsed_nodes:
        if should_load_node(node, direction):
            loaded_item = await fetch_item_from_registry_with_subtype(
                proxy_username=user.user.username, 
                id=node.id,
                item_subtype=node.item_subtype,
                config=config
            )

            collection.add_node(node=loaded_item.item, node_type=node_type)

    return collection

def should_load_node(node: Node, direction: NodeDirection) -> bool:
    if direction == NodeDirection.UPSTREAM: 
        return node.item_subtype in{
            ItemSubType.MODEL_RUN,
            ItemSubType.MODEL,
            ItemSubType.DATASET
        }
    
    return node.item_subtype == ItemSubType.DATASET 

def add_hyperlink(paragraph: Paragraph, text: str, url: str) -> Optional[docx.oxml.CT_Hyperlink]: 
        # Sourced from: https://stackoverflow.com/questions/47666642/adding-an-hyperlink-in-msword-by-using-python-docx

        part = paragraph.part
        r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

        # Create the w:hyperlink tag and add needed values
        hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
        hyperlink.set(docx.oxml.shared.qn('r:id'), r_id, )

        # Create a new run object (a wrapper over a 'w:r' element)
        new_run = docx.text.run.Run(
            docx.oxml.shared.OxmlElement('w:r'), paragraph)
        new_run.text = text

        # Set the run's style to the builtin hyperlink style, defining it if necessary
        #new_run.style = get_or_create_hyperlink_style(part.document)
        # Alternatively, set the run's formatting explicitly
        new_run.font.color.rgb = docx.shared.RGBColor(0, 0, 255)
        new_run.font.underline = True

        # Join all the xml elements together
        hyperlink.append(new_run._element)
        paragraph._p.append(hyperlink)
        return hyperlink

def generate_word_file(node_collection: ReportNodeCollection) -> str: 
    """Generates and creates a temporary word file using Python-docx.
   
    Returns
    -------
    str
        The newly created temporary file path.
    """

    try:
        # Need to convert/parse into a suitable format that can be iterated through. 
        document = Document()
        document.add_heading('Model Run Study Close Out Report', 0)

        table = document.add_table(rows=4, cols=2)
        table.style = 'Table Grid'

        # First row here is the modelling-team-name
        table.cell(0,0).text = "Modelling Team"
        table.cell(0,1).text = "TODO"

        # Second row here is the inputs
        input_row = table.rows[1].cells[0]
        input_row.text = "Inputs:"
        input_data_cell = table.cell(1,1)
        for input_node in node_collection.inputs:
            paragraph = input_data_cell.add_paragraph(input_node.display_name + ",")
            url = "http://hdl.handle.net/" + input_node.id
            add_hyperlink(paragraph, text=url, url=url)

        # Third row here is the model runs
        model_run_row = table.rows[2].cells[0]
        model_run_row.text = "Model Runs:" 
        model_run_row_data_cell = table.cell(2,1)
        for model_run_node in node_collection.model_runs:
            paragraph = model_run_row_data_cell.add_paragraph(model_run_node.display_name)
            url = "http://hdl.handle.net/" + model_run_node.id
            add_hyperlink(paragraph, text=url, url=url)

        # Fourth row here is the outputs
        output_row = table.rows[3].cells[0]
        output_row.text = "Outputs:"
        output_row_data_cell = table.cell(3,1)
        for output_node in node_collection.outputs:
            paragraph = output_row_data_cell.add_paragraph(output_node.display_name)
            url = "http://hdl.handle.net/" + output_node.id
            add_hyperlink(paragraph, text=url, url=url)

        # Temporarily save the document to return it. 
        with NamedTemporaryFile(delete=False, suffix='.docx') as tmpFile: 
            document.save(tmpFile.name)
            # Return the path of the temporary file.
            return tmpFile.name
           
    except Exception as e: 
        raise HTTPException(status_code=500, detail=f"Error generating the word file: {str(e)}")
    

def remove_file(file_path: str) -> None: 
    """Deletes the specified file from the server.

    Parameters
    ----------
    file_path : str
        The file path of the document to be deleted.
    """

    try:
        os.remove(file_path)

    except FileNotFoundError as e: 
        raise HTTPException(status_code=500, detail=f"Unable to delete the file with path {file_path} - {str(e)}")
    
    except Exception as e: 
        raise HTTPException(status_code=500, detail=f"Something has gone wrong in deleting the file {str(e)}")

def get_model_runs_from_study(study_node_id:str, config:Config, depth:int = 1) -> List[Node]: 
    
    try:
        # Query downstream to get all linked model runs at depth 1. 
        # This may contain more than one model run.
        downstream_model_run_response = downstream_query(starting_id=study_node_id, depth=depth, config=config)
        assert downstream_model_run_response.get('nodes'), "Downstream node collections not found!"

        model_run_nodes: List[Node] = parse_nodes(downstream_model_run_response.get('nodes', []))
        return model_run_nodes
    
    except AssertionError as e:
        raise HTTPException(status_code=404, detail=f"The provided study run with id {study_node_id} - error: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching downstream nodes from the provided study with id {study_node_id} - error: {str(e)}")

async def generate_report_helper(
        node_id: str, 
        upstream_depth: int, 
        item_subtype: ItemSubType, 
        roles: ProtectedRole, 
        config: Config
) -> str: 
    
    try:
        
        # Create the request style, here we assert where the HTTP request came from. 
        request_style: RequestStyle = RequestStyle(
            user_direct=roles.user, service_account=None
        )

        report_nodes: ReportNodeCollection = ReportNodeCollection()

        # do checks accordingly. 
        await validate_node_id(node_id=node_id, item_subtype=item_subtype, request_style=request_style, config=config)

        if item_subtype == ItemSubType.MODEL_RUN: 
            report_nodes = await generate_report(user=roles, 
                                                 starting_id=node_id, 
                                                 upstream_depth=upstream_depth, 
                                                 config=config,
                                                 collection_shared=report_nodes)

        elif item_subtype == ItemSubType.STUDY: 

            # Get all model runs associated with the study.
            model_run_nodes = get_model_runs_from_study(study_node_id=node_id, config=config)

            # Now branch out with the model runs in here and explore them as above (depth 1-3 upstream and depth 1 downstream)
            # The model run will be the new updated starting id.
            for model_run_node in model_run_nodes:
                if model_run_node.item_subtype == ItemSubType.MODEL_RUN:
                    model_run_id = model_run_node.id
                    # Extract the upstream and downstream entities from this node. 
                    report_nodes = await generate_report(user=roles, 
                                                         starting_id=model_run_id, 
                                                         upstream_depth=upstream_depth, 
                                                         config=config,
                                                         collection_shared=report_nodes)                

        else: 
            raise HTTPException(status_code=400, detail=f"Unsupported node with item subtype {item_subtype.value} requested.\
                                This endpoint only supports subtype of STUDY and MODEL_RUN.")

        # All the nodes involved in the model run/study have been populated. 
        generated_doc_path = generate_word_file(report_nodes)
        
        if os.path.exists(generated_doc_path): 
            return generated_doc_path
        else: 
            raise HTTPException(status_code=400, detail= "Error generating your study-closeout document")
        
    except HTTPException as e: 
        raise e 
    
    except Exception as e: 
        raise HTTPException(status_code=500, detail=f"Error in report generation: {str(e)}")     
