"""
Graph Database Management and Querying Module

This module provides functionality for managing and querying a graph database
using Neo4j. It includes classes and functions for creating, updating, and
querying graph structures, as well as utilities for comparing and applying
differences between graphs.

The module is designed to work with provenance data, using the PROV-O ontology
for relationship types and custom item categories and subtypes.

Key components: - Neo4j connection and query execution - Graph structure
representations (Node, NodeLink, NodeGraph) - Graph querying and traversal -
Graph comparison and diffing - Graph building and modification

Note: This module assumes the use of a Neo4j database and requires appropriate
configuration and credentials to connect to the database.

TODO: Consider alternative ways of embedding record IDs which will scale more as
record count increases.
"""
from typing import Dict, Callable, List
from enum import Enum, auto
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, List, Set, Any, Tuple, Callable
from enum import Enum
from config import Config
from ProvenaInterfaces.RegistryModels import ItemSubType
from ProvenaInterfaces.ProvenanceModels import *
from ProvenaInterfaces.RegistryModels import *
from typing import List, Any, Dict
from fastapi import HTTPException
from neo4j import GraphDatabase, Record, graph, basic_auth  # type: ignore
from config import Config
from typing import Optional, List, Any, Dict, Tuple, Callable
import networkx  # type: ignore
from dependencies.dependencies import secret_cache
from helpers.keycloak_helpers import retrieve_secret_value

# This is the property on which the principal id for the record is stored
IDENTIFIER_TAG = "id"


def get_credentials(config: Config) -> Tuple[str, str]:
    """
    Retrieve Neo4j database credentials based on the provided configuration.

    This function checks for test credentials first, and if not available,
    retrieves credentials from a secret store.

    Args:
        config (Config): Configuration object containing credential information.

    Returns:
        Tuple[str, str]: A tuple containing the username and password for Neo4j.

    Raises:
        AssertionError: If the secret value is not in the expected format.
    """
    if config.neo4j_test_password and config.neo4j_test_username:
        print("Using testing user/pass for neo4j!")
        return config.neo4j_test_username, config.neo4j_test_password
    # Make sure something is defined
    assert config.neo4j_auth_arn
    value = retrieve_secret_value(
        secret_arn=config.neo4j_auth_arn, secret_cache=secret_cache)
    split_auth = value.split('/')
    assert len(
        split_auth) == 2, "Couldn't split auth properly, is it in <user>/<password> format?"
    return (split_auth[0], split_auth[1])


def connect_to_neo4j(config: Config) -> GraphDatabase.driver:
    """
    Establishes a connection to the Neo4j database using the bolt protocol.

    Args:
        config (Config): Configuration object containing Neo4j connection
        details.

    Returns:
        GraphDatabase.driver: A Neo4j graph database driver object.
    """
    user, password = get_credentials(config)
    return GraphDatabase.driver(
        f"bolt://{config.neo4j_host}:{config.neo4j_port}",
        encrypted=False,
        auth=basic_auth(user, password),
    )


def run_query(query: str, config: Config, driver: Optional[GraphDatabase.driver] = None) -> List[Record]:
    """
    Executes a Cypher query against the Neo4j database and returns the results.

    This function creates a new driver connection if one is not provided,
    executes the query, and closes the connection afterward.

    Args:
        query (str): The Cypher query to execute.
        config (Config): Configuration object for database connection.
        driver (Optional[GraphDatabase.driver]): An existing driver connection, if available.

    Returns:
        List[Record]: A list of Neo4j Record objects containing the query results.

    Raises:
        RuntimeError: If attempting to query a mocked database.
        HTTPException: If there's an error executing the query.
    """
    if config.mock_graph_db:
        raise RuntimeError(
            "Asking for real data from graph DB during mock! Returning [].")
    # Create driver
    driver = connect_to_neo4j(config)
    # open session
    with driver.session() as session:
        # make query
        result = session.run(query)
        # get all results using iterator for result
        # which provides records
        records: List[Record] = [r for r in result]
    # close the driver since we are finished with it
    driver.close()
    return records


def generate_networkx_graph_from_lineage_paths(
    lineage_paths: List[graph.Path]
) -> networkx.DiGraph:
    """    generate_networkx_graph_from_lineage_paths
        Given a list of neo4j.graph.Path objects, will explore
        the paths using the known structure of the Path object.

        Using a simple approach, a networkx digraph is constructed
        which can be serialised into a D3.js compatible graph 
        style.

        The approach is: 
        - for each path 
            - for each step in relationship of path
                - if start node doesn't exist, add it 
                - if end node doesn't exist, add it 
                - if there is already a relationship between 
                these nodes, then do nothing 
                - else: add a link between nodes with the type 
                attribute set to the name of the prov relation

        This creates a digraph. The only major limitation is that if  
        a graph existed with multiple relations between the same nodes, only
        one such relation is captured.

        Arguments
        ----------
        lineage_paths : List[graph.Path]
            The list of graph paths that we want to traverse

        Returns
        -------
         : networkx.DiGraph
            The networkx digraph object

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Create digraph
    digraph = networkx.DiGraph()

    # explore all paths and relationships
    # and produce digraph
    for path in lineage_paths:
        # Check that path is not None
        if path:
            for rel in path.relationships:
                # pull nodes
                start: graph.Node = rel.start_node
                end: graph.Node = rel.end_node

                # get ids
                start_id = start.get(IDENTIFIER_TAG)
                end_id = end.get(IDENTIFIER_TAG)

                # check start/end in graph
                if not digraph.has_node(start_id):
                    # add start node into digraph
                    digraph.add_node(start_id, **{
                        'item_category': start.get('item_category'),
                        'item_subtype': start.get('item_subtype'),
                    })
                if not digraph.has_node(end_id):
                    # add end node into digraph
                    digraph.add_node(end_id, **{
                        'item_category': end.get('item_category'),
                        'item_subtype': end.get('item_subtype'),
                    })
                if not digraph.has_edge(start_id, end_id):
                    digraph.add_edge(start_id, end_id, **{
                        'type': rel.type
                    })

    return digraph


def special_contributing_dataset_query(starting_id: str, depth: int, config: Config) -> Dict[str, Any]:
    """
    Executes a special query to find contributing datasets up to a specified depth.

    This function queries the Neo4j database for datasets that contribute to the
    specified starting node, up to the given depth in the graph.

    Args:
        starting_id (str): The ID of the starting node.
        depth (int): The maximum depth to traverse in the graph.
        config (Config): Configuration object for database connection.

    Returns:
        Dict[str, Any]: A dictionary representing the graph in a D3.js-compatible format.

    Raises:
        RuntimeError: If attempting to query a mocked database.
        HTTPException: If there's an error executing the query.
    """
    if config.mock_graph_db:
        raise RuntimeError(
            "Asking for real data from graph DB during mock! Returning [].")

    # The cypher query to make for upstream lineage - only concerned with datasets upstream
    query = f"""
    MATCH r=((parent : Entity {{`item_subtype`:'DATASET'}}) <-[*1..{depth}]-(start{{`{IDENTIFIER_TAG}`:'{starting_id}'}})) RETURN r
    """

    # Run the query
    try:
        result = run_query(query, config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neo4j lineage query experienced an exception: {e}."
        )

    # Convert to list of paths by pulling out the 'r' field from the RETURN r in above
    # cypher query
    paths: List[Optional[graph.Path]] = [record.get('r') for record in result]

    # Apply simple exploration algorithm to traverse paths and produce networkx digraph
    graph = generate_networkx_graph_from_lineage_paths(
        lineage_paths=paths
    )

    # Return D3.js friendly serialisation
    return networkx.node_link_data(graph)


def special_effected_dataset_query(starting_id: str, depth: int, config: Config) -> Dict[str, Any]:
    """
    Executes a special query to find effect datasets up to a specified depth.

    This function queries the Neo4j database for datasets that result from the
    specified starting node, up to the given depth in the graph.

    Args:
        starting_id (str): The ID of the starting node.
        depth (int): The maximum depth to traverse in the graph.
        config (Config): Configuration object for database connection.

    Returns:
        Dict[str, Any]: A dictionary representing the graph in a D3.js-compatible format.

    Raises:
        RuntimeError: If attempting to query a mocked database.
        HTTPException: If there's an error executing the query.
    """
    if config.mock_graph_db:
        raise RuntimeError(
            "Asking for real data from graph DB during mock! Returning [].")

    # The cypher query to make for upstream lineage - only concerned with datasets upstream
    query = f"""
    MATCH r=((parent : Entity {{`item_subtype`:'DATASET'}}) -[*1..{depth}]->(start{{`{IDENTIFIER_TAG}`:'{starting_id}'}})) RETURN r
    """

    # Run the query
    try:
        result = run_query(query, config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neo4j lineage query experienced an exception: {e}."
        )

    # Convert to list of paths by pulling out the 'r' field from the RETURN r in above
    # cypher query
    paths: List[Optional[graph.Path]] = [record.get('r') for record in result]

    # Apply simple exploration algorithm to traverse paths and produce networkx digraph
    graph = generate_networkx_graph_from_lineage_paths(
        lineage_paths=paths
    )

    # Return D3.js friendly serialisation
    return networkx.node_link_data(graph)


def special_contributing_agent_query(starting_id: str, depth: int, config: Config) -> Dict[str, Any]:
    """
    Executes a special query to find contributing agents up to a specified depth.

    This function queries the Neo4j database for agents upstream from the
    specified starting node, up to the given depth in the graph.

    Args:
        starting_id (str): The ID of the starting node.
        depth (int): The maximum depth to traverse in the graph.
        config (Config): Configuration object for database connection.

    Returns:
        Dict[str, Any]: A dictionary representing the graph in a D3.js-compatible format.

    Raises:
        RuntimeError: If attempting to query a mocked database.
        HTTPException: If there's an error executing the query.
    """
    if config.mock_graph_db:
        raise RuntimeError(
            "Asking for real data from graph DB during mock! Returning [].")

    # The cypher query to make for upstream lineage - only concerned with datasets upstream
    query = f"""
    MATCH r=((parent : Agent) <-[*1..{depth}]-(start{{`{IDENTIFIER_TAG}`:'{starting_id}'}})) RETURN r
    """

    # Run the query
    try:
        result = run_query(query, config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neo4j lineage query experienced an exception: {e}."
        )

    # Convert to list of paths by pulling out the 'r' field from the RETURN r in above
    # cypher query
    paths: List[Optional[graph.Path]] = [record.get('r') for record in result]

    # Apply simple exploration algorithm to traverse paths and produce networkx digraph
    graph = generate_networkx_graph_from_lineage_paths(
        lineage_paths=paths
    )

    # Return D3.js friendly serialisation
    return networkx.node_link_data(graph)


def special_effected_agent_query(starting_id: str, depth: int, config: Config) -> Dict[str, Any]:
    """
    Executes a special query to find effected agents up to a specified depth.

    This function queries the Neo4j database for agents downstream from the
    specified starting node, up to the given depth in the graph.

    Args:
        starting_id (str): The ID of the starting node.
        depth (int): The maximum depth to traverse in the graph.
        config (Config): Configuration object for database connection.

    Returns:
        Dict[str, Any]: A dictionary representing the graph in a D3.js-compatible format.

    Raises:
        RuntimeError: If attempting to query a mocked database.
        HTTPException: If there's an error executing the query.
    """
    if config.mock_graph_db:
        raise RuntimeError(
            "Asking for real data from graph DB during mock! Returning [].")

    # The query to see effected agents one step removed from any downstream occurrences i.e. 'effected people/organisations'
    query = f"""
    MATCH r=((agent: Agent) <-[]- (downstream) -[*0..{depth}]->(start{{`{IDENTIFIER_TAG}`:'{starting_id}'}})) RETURN r
    """

    # Run the query
    try:
        result = run_query(query, config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neo4j lineage query experienced an exception: {e}."
        )

    # Convert to list of paths by pulling out the 'r' field from the RETURN r in above
    # cypher query
    paths: List[Optional[graph.Path]] = [record.get('r') for record in result]

    # Apply simple exploration algorithm to traverse paths and produce networkx digraph
    graph = generate_networkx_graph_from_lineage_paths(
        lineage_paths=paths
    )

    # Return D3.js friendly serialisation
    return networkx.node_link_data(graph)


def upstream_query(starting_id: str, depth: int, config: Config) -> Dict[str, Any]:
    """    lineage_query
        Performs a depth limited upstream query for a neo4j database. 
        This query is defined as, starting at a node identified uniquely by
        a handle id, traverse any relation in the parent direction i.e. 
        (parent) <-[]-(starting_node).

        The multiplicity of this exploration step is bounded by the depth 
        provided. 

        The result from the neo4j query is a list of records. A record is a kv
        store of returned elements from the cypher query. This is parsed into a 
        list of path objects. A path is a start, end and a list of steps/relationships
        along the way. 

        These paths are explored to generate a graph. The graph is a Networkx.DiGraph. 
        This digraph can be returned in a D3.js friendly json serialisation format.        

        Arguments
        ----------
        starting_id : str
            The handle ID which should uniquely identify a node in the graph
        depth : int
            The maximum depth to traverse in the <-[*1..depth]- wildcard 
        config : Config
            Connection config etc

        Returns
        -------
         : Dict[str, Any]
            The DiGraph serialisation format which is D3.js friendly.
            This format is JSON and contains a list of nodes with an id, 
            category and subtype + a list of links which have a from, 
            to and a relationship type.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    if config.mock_graph_db:
        raise RuntimeError(
            "Asking for real data from graph DB during mock! Returning [].")

    # The cypher query to make for upstream lineage
    query = f"""
    MATCH r=((parent) <-[*1..{depth}]-(start{{`{IDENTIFIER_TAG}`:'{starting_id}'}})) RETURN r
    """

    # Run the query
    try:
        result = run_query(query, config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neo4j lineage query experienced an exception: {e}."
        )

    # Convert to list of paths by pulling out the 'r' field from the RETURN r in above
    # cypher query
    paths: List[Optional[graph.Path]] = [record.get('r') for record in result]

    # Apply simple exploration algorithm to traverse paths and produce networkx digraph
    graph = generate_networkx_graph_from_lineage_paths(
        lineage_paths=paths
    )

    # Return D3.js friendly serialisation
    return networkx.node_link_data(graph)


def downstream_query(starting_id: str, depth: int, config: Config) -> Dict[str, Any]:
    """    lineage_query
        Performs a depth limited downstream query for a neo4j database. 
        This query is defined as, starting at a node identified uniquely by
        a handle id, traverse any relation in the child direction i.e. 
        (starting_node)<-[]-(child_node).

        The multiplicity of this exploration step is bounded by the depth 
        provided. 

        The result from the neo4j query is a list of records. A record is a kv
        store of returned elements from the cypher query. This is parsed into a 
        list of path objects. A path is a start, end and a list of steps/relationships
        along the way. 

        These paths are explored to generate a graph. The graph is a Networkx.DiGraph. 
        This digraph can be returned in a D3.js friendly json serialisation format.        

        Arguments
        ----------
        starting_id : str
            The handle ID which should uniquely identify a node in the graph
        depth : int
            The maximum depth to traverse in the <-[*1..depth]- wildcard 
        config : Config
            Connection config etc

        Returns
        -------
         : Dict[str, Any]
            The DiGraph serialisation format which is D3.js friendly.
            This format is JSON and contains a list of nodes with an id, 
            category and subtype + a list of links which have a from, 
            to and a relationship type.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    if config.mock_graph_db:
        raise RuntimeError(
            "Asking for real data from graph DB during mock! Returning [].")

    # The cypher query to make for lineage
    query = f"""
    MATCH r=((start{{`{IDENTIFIER_TAG}`:'{starting_id}'}})<-[*1..{depth}]-(child)) RETURN r
    """

    # Run the query
    try:
        result = run_query(query, config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neo4j lineage query experienced an exception: {e}."
        )

    # Convert to list of paths by pulling out the 'r' field from the RETURN r in above
    # cypher query
    paths: List[Optional[graph.Path]] = [record.get('r') for record in result]

    # Apply simple exploration algorithm to traverse paths and produce networkx digraph
    graph = generate_networkx_graph_from_lineage_paths(
        lineage_paths=paths
    )

    # Return D3.js friendly serialisation
    return networkx.node_link_data(graph)


class NodeLinkProps(BaseModel):
    """
    Represents properties of a link between nodes in the graph.
    """

    # Comma separated list of IDs (required)
    record_ids: str

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeLinkProps):
            return False
        return self.record_ids == other.record_ids


class NodeProps(BaseModel):
    """
    Represents properties of a node in the graph.
    """
    # Comma separated list of IDs (required)
    record_ids: str

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeProps):
            return False
        return self.record_ids == other.record_ids


class Node(BaseModel):
    """
    Node in the graph model.
    """
    # The unique ID (handle) of the node
    id: str = Field(..., description="Unique identifier for the node")
    # Other properties spread onto the node
    props: NodeProps
    # The subtype
    subtype: ItemSubType
    # Category
    category: ItemCategory

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Node):
            return False
        return (self.id == other.id and
                self.props == other.props and
                self.subtype == other.subtype and
                self.category == other.category)

    class Config:
        # Allows hash mapping of Node - immutable
        frozen = True


class ProvORelationType(str, Enum):
    """
    Allowed relations from ProvO - this is a superset of what the python prov
    extension currently supports.
    """

    WAS_DERIVED_FROM = "wasDerivedFrom"
    WAS_INFLUENCED_BY = "wasInfluencedBy"
    WAS_REVISION_OF = "wasRevisionOf"
    WAS_QUOTED_FROM = "wasQuotedFrom"
    HAD_PRIMARY_SOURCE = "hadPrimarySource"
    HAD_MEMBER = "hadMember"
    ALTERNATE_OF = "alternateOf"
    SPECIALIZATION_OF = "specializationOf"
    WAS_GENERATED_BY = "wasGeneratedBy"
    USED = "used"
    WAS_INVALIDATED_BY = "wasInvalidatedBy"
    WAS_ATTRIBUTED_TO = "wasAttributedTo"
    WAS_INFORMED_BY = "wasInformedBy"
    WAS_ASSOCIATED_WITH = "wasAssociatedWith"
    ACTED_ON_BEHALF_OF = "actedOnBehalfOf"

    @staticmethod
    def get_from_label(input: str) -> 'ProvORelationType':
        """

        Given the input label will case desensitize and lookup from enum

        Parameters
        ----------
        input : str
            The relation name

        Returns
        -------
        ProvORelationType
            Matching relation

        Raises
        ------
        ValueError
            If no relation matches
        """
        normalized_input = input.lower().replace(' ', '').replace('_', '')
        for relation_type in ProvORelationType:
            if normalized_input == relation_type.value.lower():
                return relation_type
        raise ValueError(f"No matching ProvORelationType found for '{input}'")

    def __str__(self) -> str:
        return self.value


class NodeLink(BaseModel):
    """
    A link between nodes
    """

    # from
    source: Node
    # to
    target: Node

    # What type of relation is this
    relation: ProvORelationType

    # What props?
    props: NodeLinkProps

    def get_coord(self) -> Tuple[str, str]:
        """

        Gets source/target tuple for node link

        Returns
        -------
        Tuple[str, str]
            source.id, target.id
        """
        return (self.source.id, self.target.id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeLink):
            return False
        return (self.source == other.source and
                self.target == other.target and
                self.relation == other.relation and
                self.props == other.props)


# Map of node ID -> Node
NodeMap = Dict[str, Node]
# Map of links from source,target -> NodeLink
LinkMap = Dict[Tuple[str, str], NodeLink]


class NodeGraph(BaseModel):
    record_id: str
    links: List[NodeLink]

    def get_node_set(self) -> Set[Node]:
        # gets set of unique nodes
        node_set: Set[Node] = set()

        for link in self.links:
            node_set.add(link.source)
            node_set.add(link.target)

        return node_set

    def get_node_map(self) -> NodeMap:
        return {node.id: node for node in self.get_node_set()}

    def get_link_set(self) -> Set[NodeLink]:
        return set(self.links)

    def get_link_map(self) -> LinkMap:
        link_map: LinkMap = {}
        for link in self.links:
            link_map[(link.source.id, link.target.id)] = link
        return link_map

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeGraph):
            return False

        # Compare node sets
        if self.get_node_set() != other.get_node_set():
            return False

        # Compare link maps
        self_link_map = self.get_link_map()
        other_link_map = other.get_link_map()

        if len(self_link_map) != len(other_link_map):
            return False

        for (source_id, target_id), link in self_link_map.items():
            if (source_id, target_id) not in other_link_map:
                return False
            other_link = other_link_map[(source_id, target_id)]
            if link != other_link:
                return False

        return True

    @staticmethod
    def from_link_map(record_id: str, links: LinkMap) -> 'NodeGraph':
        # Assumes that all nodes are involved in links - no dangling nodes allowed!
        return NodeGraph(record_id=record_id, links=list(links.values()))

    def to_json_pretty(self) -> Dict:
        """
        Creates a nicely formatted JSON representation of the NodeGraph.

        Returns:
            str: A pretty-printed JSON string representing the NodeGraph.
        """
        # Get the set of unique nodes
        nodes = self.get_node_set()

        # Create a dictionary to represent the graph
        graph_dict: Dict[str, Any] = {
            "nodes": [],
            "links": []
        }

        # Add nodes to the dictionary
        for node in nodes:
            node_dict = {
                "id": node.id,
                "subtype": node.subtype,
                "category": node.category,
                "props": {
                    "record_ids": node.props.record_ids
                }
            }
            graph_dict["nodes"].append(node_dict)

        # Add links to the dictionary
        for link in self.links:
            link_dict = {
                "source": link.source.id,
                "target": link.target.id,
                "relation": str(link.relation),
                "props": {
                    "record_ids": link.props.record_ids
                }
            }
            graph_dict["links"].append(link_dict)

        # Convert the dictionary to a pretty-printed JSON string
        return graph_dict


class DiffActionType(str, Enum):
    """
    Supported graph modifications - each is dispatched into a Neo4j operation
    and class in the diff manager class
    """

    # Add a new node to the graph
    ADD_NEW_NODE = auto()

    # Completely remove a node from the graph
    REMOVE_NODE = auto()

    # Add a brand new link to the graph
    ADD_NEW_LINK = auto()

    # Remove a link completely from the graph
    REMOVE_LINK = auto()

    # Remove a record id on link from the CSV list of record ids
    REMOVE_RECORD_ID_FROM_LINK = auto()

    # Remove a record id on node from the CSV list of record ids
    REMOVE_RECORD_ID_FROM_NODE = auto()

    # Add record id on link to the CSV list of record ids
    ADD_RECORD_ID_TO_LINK = auto()

    # Add record id on node to the CSV list of record ids
    ADD_RECORD_ID_TO_NODE = auto()

# ==============
# ACTION CLASSES
# ==============


class DiffAction(BaseModel):
    action_type: DiffActionType


class AddNewNode(DiffAction):
    node: Node


class RemoveNode(DiffAction):
    node_id: str


class AddNewLink(DiffAction):
    link: NodeLink


class RemoveLink(DiffAction):
    link: NodeLink


class RemoveRecordIdFromLink(DiffAction):
    link: NodeLink
    record_id: str


class RemoveRecordIdFromNode(DiffAction):
    node_id: str
    record_id: str


class AddRecordIdToLink(DiffAction):
    link: NodeLink
    record_id: str


class AddRecordIdToNode(DiffAction):
    node_id: str
    record_id: str


def diff_graphs(old_graph: NodeGraph, new_graph: NodeGraph) -> List[DiffAction]:
    """

    Generates a list of actions (unsorted) which conservatively modifies the old
    graph to match the new graph. The logic tries to not remove any node or
    links which are involved in an existing record.

    Parameters
    ----------
    old_graph : NodeGraph
        The old graph (NOTE: The record id's on these elements are accurate)
    new_graph : NodeGraph
        The new graph (NOTE: This graph does not include all record IDs on the
        property because it reflects a 'new' graph.)

    Returns
    -------
    List[DiffAction]
        A list of actions to take
    """
    assert old_graph.record_id == new_graph.record_id, "Should not diff graphs with different record IDs!"
    record_id = new_graph.record_id

    actions: List[DiffAction] = []

    # Get all nodes and links for new and old

    # Old nodes
    old_node_set = old_graph.get_node_set()
    old_node_map = old_graph.get_node_map()

    # Old links
    old_link_set = old_graph.get_link_set()
    old_link_map = old_graph.get_link_map()

    # new nodes
    new_node_set = new_graph.get_node_set()
    new_node_map = new_graph.get_node_map()

    # new links
    new_link_set = new_graph.get_link_set()
    new_link_map = new_graph.get_link_map()

    # Process nodes

    # Removed nodes are those which were in the original set but no longer are
    removed_nodes = old_node_set - new_node_set

    # Added nodes are those in the new set which weren't in the old
    added_nodes = new_node_set - old_node_set

    # Intersection defines both
    in_both = new_node_set.intersection(old_node_set)

    for node in added_nodes:
        new_node = new_node_map[node.id]
        # New node which is not in old nodes
        actions.append(AddNewNode(
            action_type=DiffActionType.ADD_NEW_NODE, node=new_node))

    for node in removed_nodes:
        # Remove record id if others, or delete if just this record
        removed_node = old_node_map[node.id]
        old_record_ids = set(removed_node.props.record_ids.split(','))
        # TODO optimise
        if len(old_record_ids) <= 1 and record_id in old_record_ids:
            # Just this single record ID - so remove the node
            actions.append(RemoveNode(
                action_type=DiffActionType.REMOVE_NODE, node_id=node))
        else:
            # Contains other links as well - so don't remove
            actions.append(RemoveRecordIdFromNode(
                action_type=DiffActionType.REMOVE_RECORD_ID_FROM_NODE, node_id=node, record_id=record_id))
    for node in in_both:
        old_version = old_node_map[node.id]
        # all we want to do is ensure that the record ID is in this one already
        old_record_ids = set(old_version.props.record_ids.split(','))
        if record_id not in old_record_ids:
            actions.append(AddRecordIdToNode(
                action_type=DiffActionType.ADD_RECORD_ID_TO_NODE, node_id=node, record_id=record_id))

    # Process links

    # Removed nodes are those which were in the original set but no longer are
    removed_links = old_link_set - new_link_set

    # Added links are those in the new set which weren't in the old
    added_links = new_link_set - old_link_set

    # Intersection defines both
    links_in_both = new_link_set.intersection(old_link_set)

    for link in added_links:
        new_link = new_link_map[link.get_coord()]
        # New link which is not in old links
        actions.append(AddNewLink(
            action_type=DiffActionType.ADD_NEW_LINK, link=new_link))

    for link in removed_links:
        # Remove record id if others, or delete if just this record
        removed_link = old_link_map[link.get_coord()]
        old_record_ids = set(removed_link.props.record_ids.split(','))
        # TODO optimise
        if len(old_record_ids) <= 1 and record_id in old_record_ids:
            # Just this single record ID - so remove the link
            actions.append(RemoveLink(
                action_type=DiffActionType.REMOVE_LINK, link=removed_link))
        else:
            # Contains other records as well - so don't remove
            actions.append(RemoveRecordIdFromLink(
                action_type=DiffActionType.REMOVE_RECORD_ID_FROM_LINK, link=removed_link, record_id=record_id))

    for link in links_in_both:
        old_link = old_link_map[link.get_coord()]
        # all we want to do is ensure that the record ID is in this one already
        old_record_ids = set(old_link.props.record_ids.split(','))
        if record_id not in old_record_ids:
            actions.append(AddRecordIdToLink(
                action_type=DiffActionType.ADD_RECORD_ID_TO_LINK, link=old_link, record_id=record_id))

    return actions


class Neo4jGraphManager():
    """
    This class manages basic record level read/write with the Neo4J graph.
    """
    driver: GraphDatabase.driver
    _config: Config

    def __init__(self, config: Config) -> None:
        """

        Construct the driver and store config

        Parameters
        ----------
        config : Config
            Config
        """
        # Create driver
        self.driver = connect_to_neo4j(config)
        self._config = config

    def merge_add_graph_to_db(self, graph: NodeGraph) -> None:
        """
        Writes a NodeGraph to the Neo4j database.

        This is an additive merge mode which will never destroy. Not suitable for editing.

        Will update record_ids with additional record IDs if not already present.

        Args:
            graph (NodeGraph): The NodeGraph to be written to the database.
        """
        if self._config.mock_graph_db:
            print("Mocked graph write")
            return None

        with self.driver.session() as session:
            # Create or merge nodes
            for node in graph.get_node_set():
                cypher_query = """
                MERGE (n:Node {id: $id})
                SET n.item_subtype = $subtype,
                    n.item_category = $category,
                    n.record_ids = CASE
                        WHEN n.record_ids IS NULL THEN $record_ids
                        WHEN NOT $record_ids IN split(n.record_ids, ',') THEN n.record_ids + ',' + $record_ids
                        ELSE n.record_ids
                    END
                """
                session.run(cypher_query, {
                    'id': node.id,
                    'subtype': node.subtype.value,
                    'category': node.category.value,
                    'record_ids': node.props.record_ids
                })

            # Create or merge relationships
            for link in graph.links:
                relation_label = link.relation.value
                cypher_query = """
                MATCH (source:Node {id: $source_id})
                MATCH (target:Node {id: $target_id})
                MERGE (source)-[r:""" + relation_label + """]->(target)
                SET r.record_ids = CASE
                    WHEN r.record_ids IS NULL THEN $record_ids
                    WHEN NOT $record_ids IN split(r.record_ids, ',') THEN r.record_ids + ',' + $record_ids
                    ELSE r.record_ids
                END
                """
                session.run(cypher_query, {
                    'source_id': link.source.id,
                    'target_id': link.target.id,
                    'record_ids': link.props.record_ids
                })

        print(f"Successfully merge-wrote NodeGraph to the database.")

    def get_graph_by_record_id(self, record_id: str) -> NodeGraph:
        """
        Gets a NodeGraph from the Neo4j database.

        This works by traversing the graph and looking for nodes/relations which have the record_id property on them.

        It then builds out the nodes and links from this result into the NodeGraph object.

        Args:
            graph (NodeGraph): The NodeGraph read from the db.
        """

        if self._config.mock_graph_db:
            raise RuntimeError(
                "Asking for real data from graph DB during mock! Returning [].")
        # This method retrieves an existing node graph by looking for nodes and links which match the record_id property

        # Cypher query to get all nodes and relationships where record_id is in the record_ids property
        query = """
        MATCH (n)
        WHERE $record_id IN split(n.record_ids, ',')
        WITH n
        MATCH (n)-[r]->(m)
        WHERE $record_id IN split(r.record_ids, ',') AND $record_id IN split(m.record_ids, ',')
        RETURN n, r, m
        """

        # Execute the query
        with self.driver.session() as session:
            # query to get all relevant nodes/links
            result = session.run(query, record_id=record_id)

            # Process the results
            nodes = {}
            links = {}

            for record in result:
                # work out the relationship/nodes
                start_node = record['n']
                end_node = record['m']
                relationship = record['r']

                # Process start node
                if start_node.id not in nodes:
                    nodes[start_node.id] = Node(
                        id=start_node['id'],
                        subtype=ItemSubType(start_node['item_subtype']),
                        category=ItemCategory(start_node['item_category']),
                        props=NodeProps(record_ids=start_node['record_ids'])
                    )

                # Process end node
                if end_node.id not in nodes:
                    nodes[end_node.id] = Node(
                        id=end_node['id'],
                        subtype=ItemSubType(end_node['item_subtype']),
                        category=ItemCategory(end_node['item_category']),
                        props=NodeProps(record_ids=end_node['record_ids'])
                    )

                # Process relationship
                link_key = (start_node.id, end_node.id)
                if link_key not in links:
                    links[link_key] = NodeLink(
                        source=nodes[start_node.id],
                        target=nodes[end_node.id],
                        relation=ProvORelationType.get_from_label(
                            relationship.type),
                        props=NodeLinkProps(
                            record_ids=relationship['record_ids'])
                    )

        # Construct and return the NodeGraph
        return NodeGraph(record_id=record_id, links=list(links.values()))


class GraphBuilder:
    """
    Helper class which wraps the graph class. Provides a more interactive r/w interface for iteratively building a graph.
    """
    _nodes: Dict[str, Node] = {}
    _links: Dict[Tuple[str, str], NodeLink] = {}
    _record_id: str

    def __init__(self, record_id: str) -> None:
        self._record_id = record_id

    def add_node(self, node: Node) -> None:
        """
        Add a node to the graph builder.

        Args:
            node (Node): The node to add.
        """
        self._nodes[node.id] = node

    def add_link(self, link: NodeLink) -> None:
        """
        Add a link to the graph builder.

        Args:
            link (NodeLink): The link to add.
        """
        self._links[(link.source.id, link.target.id)] = link
        # Ensure both nodes are in the node map - replace if present already
        self.add_node(link.source)
        self.add_node(link.target)

    @property
    def node_map(self) -> Dict[str, Node]:
        """
        Get the node map.

        Returns:
            Dict[str, Node]: A dictionary mapping node IDs to Node objects.
        """
        return self._nodes

    @property
    def link_map(self) -> Dict[Tuple[str, str], NodeLink]:
        """
        Get the link map.

        Returns:
            Dict[Tuple[str, str], NodeLink]: A dictionary mapping (source_id, target_id) tuples to NodeLink objects.
        """
        return self._links

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Get a node by its ID.

        Args:
            node_id (str): The ID of the node to retrieve.

        Returns:
            Optional[Node]: The Node object if found, None otherwise.
        """
        return self._nodes.get(node_id)

    def get_link(self, source_id: str, target_id: str) -> Optional[NodeLink]:
        """
        Get a link by its source and target node IDs.

        Args:
            source_id (str): The ID of the source node.
            target_id (str): The ID of the target node.

        Returns:
            Optional[NodeLink]: The NodeLink object if found, None otherwise.
        """
        return self._links.get((source_id, target_id))

    def build(self) -> NodeGraph:
        """
        Build and validate the NodeGraph.

        Returns:
            NodeGraph: The validated NodeGraph object.

        Raises:
            ValueError: If there are dangling nodes (nodes not connected by any link).
        """
        # Check for dangling nodes
        connected_nodes = set()
        for link in self._links.values():
            connected_nodes.add(link.source.id)
            connected_nodes.add(link.target.id)

        dangling_nodes = set(self._nodes.keys()) - connected_nodes
        if dangling_nodes:
            raise ValueError(
                f"Dangling nodes found: {', '.join(dangling_nodes)}")

        # Create the NodeGraph
        try:
            return NodeGraph(record_id=self._record_id, links=list(self._links.values()))
        except ValidationError as e:
            raise ValueError(f"Invalid NodeGraph: {str(e)}")

    def clear(self) -> None:
        """
        Clear all nodes and links from the builder.
        """
        self._nodes.clear()
        self._links.clear()


class GraphDiffApplier:
    """
    This is a class which manages graph diff operations.

    Notably it can take an old -> new graph, then generate a diff and apply it.
    """

    def __init__(self, neo4j_manager: Neo4jGraphManager):
        # Setup manager
        self.neo4j_manager = neo4j_manager
        # Register handlers
        # Actually a list of DiffAction -> mypy doesn't understand!
        self.handlers: Dict[DiffActionType, Callable[[Any], None]] = {
            DiffActionType.ADD_RECORD_ID_TO_NODE: self._handle_add_record_id_to_node,
            DiffActionType.ADD_NEW_NODE: self._handle_add_new_node,
            DiffActionType.ADD_RECORD_ID_TO_LINK: self._handle_add_record_id_to_link,
            DiffActionType.ADD_NEW_LINK: self._handle_add_new_link,
            DiffActionType.REMOVE_RECORD_ID_FROM_LINK: self._handle_remove_record_id_from_link,
            DiffActionType.REMOVE_LINK: self._handle_remove_link,
            DiffActionType.REMOVE_RECORD_ID_FROM_NODE: self._handle_remove_record_id_from_node,
            DiffActionType.REMOVE_NODE: self._handle_remove_node,
        }

    def apply_diff(self, old_graph: NodeGraph, new_graph: NodeGraph) -> None:
        """

        Generates, sorts, then applies a list of graph diffs.

        Parameters
        ----------
        old_graph : NodeGraph
            The existing graph (NOTE: populated with all record ids)
        new_graph : NodeGraph
            The proposed/new graph (NOTE: only contains this records record ids)
        """
        # Diff the graphs
        diff_actions = diff_graphs(old_graph, new_graph)
        # sort thea ctions
        sorted_actions = self._sort_diff_actions(diff_actions)
        # apply all actions

        for action in sorted_actions:
            handler = self.handlers.get(action.action_type)
            if not handler:
                raise RuntimeError(
                    f"Missing a handler for action type: {action}. Aborting.")

        for action in sorted_actions:
            handler = self.handlers.get(action.action_type)
            if handler:
                handler(action)

    def _sort_diff_actions(self, actions: List[DiffAction]) -> List[DiffAction]:
        """

        Defines an ordering for actions which seems safest.

        Parameters
        ----------
        actions : List[DiffAction]
            The list of actions

        Returns
        -------
        List[DiffAction]
            The sorted list of actions
        """
        action_order = {
            DiffActionType.ADD_RECORD_ID_TO_NODE: 1,
            DiffActionType.ADD_NEW_NODE: 2,
            DiffActionType.ADD_RECORD_ID_TO_LINK: 3,
            DiffActionType.ADD_NEW_LINK: 4,
            DiffActionType.REMOVE_RECORD_ID_FROM_LINK: 5,
            DiffActionType.REMOVE_LINK: 6,
            DiffActionType.REMOVE_RECORD_ID_FROM_NODE: 7,
            DiffActionType.REMOVE_NODE: 8
        }
        return sorted(actions, key=lambda x: action_order[x.action_type])

    def _handle_add_record_id_to_node(self, action: AddRecordIdToNode) -> None:
        with self.neo4j_manager.driver.session() as session:
            cypher_query = """
            MATCH (n:Node {id: $node_id})
            SET n.record_ids = CASE
                WHEN n.record_ids IS NULL THEN $record_id
                WHEN NOT $record_id IN split(n.record_ids, ',') THEN n.record_ids + ',' + $record_id
                ELSE n.record_ids
            END
            """
            session.run(cypher_query, node_id=action.node_id,
                        record_id=action.record_id)

    def _handle_add_new_node(self, action: AddNewNode) -> None:
        with self.neo4j_manager.driver.session() as session:
            cypher_query = """
            MERGE (n:Node {
                id: $id,
                item_subtype: $subtype,
                item_category: $category,
                record_ids: $record_ids
            })
            """
            session.run(cypher_query, id=action.node.id, subtype=action.node.subtype.value,
                        category=action.node.category.value, record_ids=action.node.props.record_ids)

    def _handle_add_record_id_to_link(self, action: AddRecordIdToLink) -> None:
        with self.neo4j_manager.driver.session() as session:
            cypher_query = f"""
            MATCH (source:Node {{id: $source_id}})-[r:{action.link.relation.value}]->(target:Node {{id: $target_id}})
            SET r.record_ids = CASE
                WHEN r.record_ids IS NULL THEN $record_id
                WHEN NOT $record_id IN split(r.record_ids, ',') THEN r.record_ids + ',' + $record_id
                ELSE r.record_ids
            END
            """
            session.run(cypher_query, source_id=action.link.source.id,
                        target_id=action.link.target.id, record_id=action.record_id)

    def _handle_add_new_link(self, action: AddNewLink) -> None:
        with self.neo4j_manager.driver.session() as session:
            cypher_query = f"""
            MATCH (source:Node {{id: $source_id}})
            MATCH (target:Node {{id: $target_id}})
            CREATE (source)-[r:{action.link.relation.value} {{record_ids: $record_ids}}]->(target)
            """
            session.run(cypher_query, source_id=action.link.source.id, target_id=action.link.target.id,
                        record_ids=action.link.props.record_ids)

    def _handle_remove_record_id_from_link(self, action: RemoveRecordIdFromLink) -> None:
        with self.neo4j_manager.driver.session() as session:
            cypher_query = f"""
            MATCH (source:Node {{id: $source_id}})-[r:{action.link.relation.value}]->(target:Node {{id: $target_id}})
            WHERE $record_id IN split(r.record_ids, ',')
            SET r.record_ids = reduce(s = '', x IN split(r.record_ids, ',') |
                CASE WHEN x <> $record_id
                    THEN CASE WHEN s = '' THEN x ELSE s + ',' + x END
                    ELSE s
                END
            )
            """
            session.run(cypher_query, source_id=action.link.source.id,
                        target_id=action.link.target.id, record_id=action.record_id)

    def _handle_remove_link(self, action: RemoveLink) -> None:
        with self.neo4j_manager.driver.session() as session:
            cypher_query = f"""
            MATCH (source:Node {{id: $source_id}})-[r:{action.link.relation.value}]->(target:Node {{id: $target_id}})
            DELETE r
            """
            session.run(cypher_query, source_id=action.link.source.id,
                        target_id=action.link.target.id)

    def _handle_remove_record_id_from_node(self, action: RemoveRecordIdFromNode) -> None:
        with self.neo4j_manager.driver.session() as session:
            cypher_query = """
            MATCH (n:Node {id: $node_id})
            WHERE $record_id IN split(n.record_ids, ',')
            SET n.record_ids = reduce(s = '', x IN split(n.record_ids, ',') |
                CASE WHEN x <> $record_id
                    THEN CASE WHEN s = '' THEN x ELSE s + ',' + x END
                    ELSE s
                END
            )
            """
            session.run(cypher_query, node_id=action.node_id,
                        record_id=action.record_id)

    def _handle_remove_node(self, action: RemoveNode) -> None:
        with self.neo4j_manager.driver.session() as session:
            cypher_query = """
            MATCH (n:Node {id: $node_id})
            WHERE n.record_ids IS NULL OR n.record_ids = ''
            DELETE n
            """
            session.run(cypher_query, node_id=action.node_id)
