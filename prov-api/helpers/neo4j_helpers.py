from fastapi import HTTPException, Depends
from neo4j import GraphDatabase, Record, graph, basic_auth  # type: ignore
from config import Config
from typing import Optional, List, Any, Dict, Tuple, Callable
import networkx  # type: ignore
from dependencies.dependencies import secret_cache
from helpers.keycloak_helpers import retrieve_secret_value


def get_credentials(config: Config) -> Tuple[str, str]:
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
    """    connect_to_neo4j
        Connects to the neo4j endpoint using the bolt protocol.

        The target and auth is specified from environment variables 
        in the config.

        Returns
        -------
         : GraphDatabase.driver
            Returns a neo4j graph database driver object.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    user, password = get_credentials(config)
    return GraphDatabase.driver(
        f"bolt://{config.neo4j_host}:{config.neo4j_port}",
        encrypted=False,
        auth=basic_auth(user, password),
    )


def run_query(query: str, config: Config, driver : Optional[GraphDatabase.driver] = None) -> List[Record]:
    """    run_query
        Will generate a neo4j driver, then open a managed session, 
        run the query, and stream all results into a list of records.

        Arguments
        ----------
        query : str
            The cypher query to run against the DB

        Returns
        -------
         : List[Record]
            A list of neo4j.graph.Record objects. A record contains a 
            dictionary kv lookup style result.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
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
                start_id = start.get('meta:identifier_original')
                end_id = end.get('meta:identifier_original')

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
    # The neo4j tag created by prov-db-connector which contains just the
    # handle ID to match against
    id_tag = "meta:identifier_original"

    # The cypher query to make for upstream lineage - only concerned with datasets upstream
    query = f"""
    MATCH r=((parent : Entity {{`item_subtype`:'DATASET'}}) <-[*1..{depth}]-(start{{`{id_tag}`:'{starting_id}'}})) RETURN r
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
    # The neo4j tag created by prov-db-connector which contains just the
    # handle ID to match against
    id_tag = "meta:identifier_original"

    # The cypher query to make for upstream lineage - only concerned with datasets upstream
    query = f"""
    MATCH r=((parent : Entity {{`item_subtype`:'DATASET'}}) -[*1..{depth}]->(start{{`{id_tag}`:'{starting_id}'}})) RETURN r
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
    # The neo4j tag created by prov-db-connector which contains just the
    # handle ID to match against
    id_tag = "meta:identifier_original"

    # The cypher query to make for upstream lineage - only concerned with datasets upstream
    query = f"""
    MATCH r=((parent : Agent) <-[*1..{depth}]-(start{{`{id_tag}`:'{starting_id}'}})) RETURN r
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
    # The neo4j tag created by prov-db-connector which contains just the
    # handle ID to match against
    id_tag = "meta:identifier_original"

    # The query to see effected agents one step removed from any downstream occurrences i.e. 'effected people/organisations'
    query = f"""
    MATCH r=((agent: Agent) <-[]- (downstream) -[*0..{depth}]->(start{{`{id_tag}`:'{starting_id}'}})) RETURN r
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
    # The neo4j tag created by prov-db-connector which contains just the
    # handle ID to match against
    id_tag = "meta:identifier_original"

    # The cypher query to make for upstream lineage
    query = f"""
    MATCH r=((parent) <-[*1..{depth}]-(start{{`{id_tag}`:'{starting_id}'}})) RETURN r
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
    # The neo4j tag created by prov-db-connector which contains just the
    # handle ID to match against
    id_tag = "meta:identifier_original"

    # The cypher query to make for lineage
    query = f"""
    MATCH r=((start{{`{id_tag}`:'{starting_id}'}})<-[*1..{depth}]-(child)) RETURN r
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
