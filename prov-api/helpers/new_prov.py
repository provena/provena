from typing import Dict, Callable, List
from enum import Enum
from neo4j import GraphDatabase  # type: ignore
from pydantic import BaseModel, Field
from typing import Dict, List, Set, Any, Tuple, Callable, Union
from enum import Enum, auto
from ProvenaInterfaces.ProvenanceModels import ModelRunRecord
from config import Config
from ProvenaInterfaces.RegistryModels import ItemSubType, ItemModelRunWorkflowTemplate, SeededItem
from helpers.validate_model_run_record import validate_model_run_record, validate_model_run_workflow_template
from helpers.entity_validators import RequestStyle
from helpers.registry_helpers import seed_model_run
from helpers.neo4j_helpers import connect_to_neo4j, run_query
import prov.model as prov  # type: ignore
from ProvenaInterfaces.ProvenanceModels import *
from ProvenaInterfaces.RegistryModels import *
from typing import List, Any, Dict
from helpers.prov_helpers import produce_attribute_set, produce_dataset, produce_workflow_template, produce_dataset_template, produce_model, produce_modeller, produce_organisation


class NodeLinkProps(BaseModel):
    # Comma separated list of IDs (required)
    record_ids: str

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeLinkProps):
            return False
        return self.record_ids == other.record_ids


class NodeProps(BaseModel):
    # Comma separated list of IDs (required)
    record_ids: str

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeProps):
            return False
        return self.record_ids == other.record_ids


class Node(BaseModel):
    id: str = Field(..., description="Unique identifier for the node")
    props: NodeProps
    subtype: ItemSubType
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
        frozen = True


class ProvORelationType(str, Enum):
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
        normalized_input = input.lower().replace(' ', '').replace('_', '')
        for relation_type in ProvORelationType:
            if normalized_input == relation_type.value.lower():
                return relation_type
        raise ValueError(f"No matching ProvORelationType found for '{input}'")

    def __str__(self) -> str:
        return self.value


class NodeLink(BaseModel):
    # from
    source: Node
    # to
    target: Node

    # What type of relation is this
    relation: ProvORelationType

    # What props?
    props: NodeLinkProps

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeLink):
            return False
        return (self.source == other.source and
                self.target == other.target and
                self.relation == other.relation and
                self.props == other.props)


# Map of links from source,target -> NodeLink
NodeMap = Dict[str, Node]
LinkMap = Dict[Tuple[str, str], NodeLink]


class DiffActionType(str, Enum):
    ADD_NEW_NODE = auto()
    REMOVE_NODE = auto()
    ADD_NEW_LINK = auto()
    REMOVE_LINK = auto()
    REMOVE_RECORD_ID_FROM_LINK = auto()
    REMOVE_RECORD_ID_FROM_NODE = auto()
    ADD_RECORD_ID_TO_LINK = auto()
    ADD_RECORD_ID_TO_NODE = auto()


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


def diff_graphs(old_graph: NodeGraph, new_graph: NodeGraph) -> List[DiffAction]:
    # TODO consider changing relation type

    assert old_graph.record_id == new_graph.record_id, "Should not diff graphs with different record IDs!"
    record_id = new_graph.record_id

    actions: List[DiffAction] = []

    old_nodes = {node.id: node for node in old_graph.get_node_set()}
    new_nodes = {node.id: node for node in new_graph.get_node_set()}
    old_links = old_graph.get_link_map()
    new_links = new_graph.get_link_map()

    # Process nodes
    # TODO optimise performance here
    removed_nodes = [
        node_id for node_id in old_nodes if node_id not in new_nodes]
    added_nodes = [
        node_id for node_id in new_nodes if node_id not in old_nodes]
    in_both = list(set(new_nodes.keys()).intersection(set(old_nodes.keys())))

    for node_id in added_nodes:
        new_node = new_nodes[node_id]
        # New node which is not in old nodes
        actions.append(AddNewNode(
            action_type=DiffActionType.ADD_NEW_NODE, node=new_node))

    for node_id in removed_nodes:
        # Remove record id if others, or delete if just this record
        removed_node = old_nodes[node_id]
        old_record_ids = set(removed_node.props.record_ids.split(','))
        # TODO optimise
        if len(old_record_ids) <= 1 and record_id in old_record_ids:
            # Just this single record ID - so remove the node
            actions.append(RemoveNode(
                action_type=DiffActionType.REMOVE_NODE, node_id=node_id))
        else:
            # Contains other links as well - so don't remove
            actions.append(RemoveRecordIdFromNode(
                action_type=DiffActionType.REMOVE_RECORD_ID_FROM_NODE, node_id=node_id, record_id=record_id))
    for node_id in in_both:
        old_version = old_nodes[node_id]
        # all we want to do is ensure that the record ID is in this one already
        old_record_ids = set(old_version.props.record_ids.split(','))
        if record_id not in old_record_ids:
            actions.append(AddRecordIdToNode(
                action_type=DiffActionType.ADD_RECORD_ID_TO_NODE, node_id=node_id, record_id=record_id))

    # Process nodes
    # TODO optimise performance here
    removed_links = [
        link_id for link_id in old_links if link_id not in new_links]
    added_links = [
        link_id for link_id in new_links if link_id not in old_links]
    links_in_both = list(
        set(new_links.keys()).intersection(set(old_links.keys())))

    for link_id in added_links:
        new_link = new_links[link_id]
        # New link which is not in old links
        actions.append(AddNewLink(
            action_type=DiffActionType.ADD_NEW_LINK, link=new_link))

    for link_id in removed_links:
        # Remove record id if others, or delete if just this record
        removed_link = old_links[link_id]
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

    for link_id in links_in_both:
        old_link = old_links[link_id]
        # all we want to do is ensure that the record ID is in this one already
        old_record_ids = set(old_link.props.record_ids.split(','))
        if record_id not in old_record_ids:
            actions.append(AddRecordIdToLink(
                action_type=DiffActionType.ADD_RECORD_ID_TO_LINK, link=old_link, record_id=record_id))

    return actions


class Neo4jGraphManager():
    driver: GraphDatabase.driver

    def __init__(self, config: Config) -> None:
        # Create driver
        self.driver = connect_to_neo4j(config)

    def merge_add_graph_to_db(self, graph: NodeGraph) -> None:
        """
        Writes a NodeGraph to the Neo4j database.
        Args:
            graph (NodeGraph): The NodeGraph to be written to the database.
        """
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
            result = session.run(query, record_id=record_id)

            # Process the results
            nodes = {}
            links = {}

            for record in result:
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


class GraphDiffApplier:
    def __init__(self, neo4j_manager: Neo4jGraphManager):
        self.neo4j_manager = neo4j_manager
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
        print("Generating graph diff")
        diff_actions = diff_graphs(old_graph, new_graph)
        print(f"Found {len(diff_actions)} actions.")

        print("Sorting...")
        sorted_actions = self._sort_diff_actions(diff_actions)
        print("Done.")

        for action in sorted_actions:
            print(f"Applying {action}")
            handler = self.handlers.get(action.action_type)
            if handler:
                handler(action)
            else:
                print(
                    f"No handler found for action type: {action.action_type}")
            print("done.")

    def _sort_diff_actions(self, actions: List[DiffAction]) -> List[DiffAction]:
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


async def graph_from_model_run_record(model_record: ModelRunRecord, request_style: RequestStyle, config: Config, record_id: Optional[str] = None) -> Tuple['NodeGraph', prov.ProvDocument]:
    # this seeds the item on behalf of the user - based on the request style
    # this could be the proxied username or direct from the token
    username: str
    if request_style.service_account:
        assert request_style.service_account.on_behalf_username
        username = request_style.service_account.on_behalf_username
    elif request_style.user_direct:
        username = request_style.user_direct.username
    else:
        raise ValueError("Invalid validation settings")

    # resolve the workflow definition
    workflow_template = await validate_model_run_workflow_template(
        id=model_record.workflow_template_id,
        request_style=request_style,
        config=config
    )
    assert isinstance(workflow_template, ItemModelRunWorkflowTemplate)

    # service account is always used for this request
    if not record_id:
        seeded_item: SeededItem = await seed_model_run(
            proxy_username=username,
            config=config
        )
        record_id = seeded_item.id

    # Build the document and graph
    document = prov.ProvDocument()
    nodes: NodeMap = {}
    links: LinkMap = {}

    # add default Provena namespace
    document.set_default_namespace('http://hdl.handle.net/')

    # universal entity map
    universal_entity_map: Dict[str, prov.ProvEntity] = {}
    universal_activity_map: Dict[str, prov.ProvActivity] = {}
    universal_agent_map: Dict[str, prov.ProvAgent] = {}

    """
    ==============
    CREATE OBJECTS
    ==============
    """
    # Create model run activity
    model_run_activity: prov.ProvActivity = document.activity(
        identifier=record_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ACTIVITY,
            item_subtype=ItemSubType.MODEL_RUN,
            id=record_id
        )
    )
    universal_activity_map[record_id] = model_run_activity

    # root node
    root_node = Node(id=record_id, subtype=ItemSubType.MODEL_RUN,
                     category=ItemCategory.ACTIVITY, props=NodeProps(record_ids=record_id))
    nodes[record_id] = root_node

    # Create study if provided
    study_id = model_record.study_id
    if study_id is not None:
        study_node: prov.ProvActivity = document.activity(
            identifier=study_id,
            other_attributes=produce_attribute_set(
                item_category=ItemCategory.ACTIVITY,
                item_subtype=ItemSubType.STUDY,
                id=study_id
            )
        )
        universal_activity_map[study_id] = study_node
        nodes[study_id] = Node(id=study_id, subtype=ItemSubType.STUDY,
                               category=ItemCategory.ACTIVITY, props=NodeProps(record_ids=record_id))

    # Add input datasets

    # pull out templates and produce a map from template ID to dataset that fulfils it
    # Get provided inputs/outputs and validate existence
    provided_input_templates_list: List[TemplatedDataset] = model_record.inputs
    provided_output_templates_list: List[TemplatedDataset] = model_record.outputs

    # produce a dictionary mapping template -> TemplatedDataset

    # inputs
    provided_input_map: Dict[str, List[TemplatedDataset]] = {}
    for input_template in provided_input_templates_list:
        # fetch the matched records and add the entry
        matched_list = provided_input_map.get(
            input_template.dataset_template_id, [])
        matched_list.append(input_template)
        provided_input_map[input_template.dataset_template_id] = matched_list

    # outputs
    provided_output_map: Dict[str, List[TemplatedDataset]] = {}
    for output_template in provided_output_templates_list:
        # fetch the matched records and add the entry
        matched_list = provided_output_map.get(
            output_template.dataset_template_id, [])
        matched_list.append(output_template)
        provided_output_map[output_template.dataset_template_id] = matched_list

    # links the template ID -> the dataset(s) that fulfil it
    input_dataset_template_object_map: Dict[str,
                                            List[prov.ProvEntity]] = {}
    output_dataset_template_object_map: Dict[str, List[prov.ProvEntity]] = {
    }

    for template_id, templated_datasets in provided_input_map.items():
        for templated_dataset in templated_datasets:
            if templated_dataset.dataset_type != DatasetType.DATA_STORE:
                # TODO implement other prov models for non IS registered data
                raise NotImplementedError(
                    f"Can only handle data store registered items. Template ID {template_id}.")

            # pull dataset id
            dataset_id = templated_dataset.dataset_id

            if dataset_id in universal_entity_map:
                prov_entity = universal_entity_map[dataset_id]
            else:
                # produce the prov dataset entity
                prov_entity = produce_dataset(
                    prov_document=document,
                    dataset_id=dataset_id,
                    record_id=record_id
                )

            # add to universal map (may already be there)
            universal_entity_map[dataset_id] = prov_entity
            nodes[dataset_id] = Node(id=dataset_id, subtype=ItemSubType.DATASET,
                                     category=ItemCategory.ENTITY, props=NodeProps(record_ids=record_id))

            # link the template ID -> prov entity
            datasets_match_list = input_dataset_template_object_map.get(
                template_id, [])
            datasets_match_list.append(prov_entity)
            input_dataset_template_object_map[template_id] = datasets_match_list

    # Add output datasets

    # check that only data store type data is used at the moment
    for template_id, templated_datasets in provided_output_map.items():
        for templated_dataset in templated_datasets:
            if templated_dataset.dataset_type != DatasetType.DATA_STORE:
                # TODO implement other prov models for non IS registered data
                raise NotImplementedError(
                    f"Can only handle data store registered items. Template ID {template_id}.")

            # pull dataset id
            dataset_id = templated_dataset.dataset_id

            if dataset_id in universal_entity_map:
                prov_entity = universal_entity_map[dataset_id]
            else:
                # produce the prov dataset entity
                prov_entity = produce_dataset(
                    prov_document=document,
                    dataset_id=dataset_id,
                    record_id=record_id
                )

            # add to universal map (may already be there)
            universal_entity_map[dataset_id] = prov_entity
            nodes[dataset_id] = Node(id=dataset_id, subtype=ItemSubType.DATASET,
                                     category=ItemCategory.ENTITY, props=NodeProps(record_ids=record_id))

            # link the template ID -> prov entity
            datasets_match_list = output_dataset_template_object_map.get(
                template_id, [])
            datasets_match_list.append(prov_entity)
            output_dataset_template_object_map[template_id] = datasets_match_list

    # add model run workflow definition
    workflow_template_id = model_record.workflow_template_id
    workflow_template_entity: prov.ProvEntity = produce_workflow_template(
        prov_document=document,
        workflow_template_id=workflow_template_id,
        record_id=record_id
    )
    universal_entity_map[workflow_template_id] = workflow_template_entity
    nodes[workflow_template_id] = Node(id=workflow_template_id, subtype=ItemSubType.WORKFLOW_TEMPLATE,
                                       category=ItemCategory.ENTITY, props=NodeProps(record_ids=record_id))

    # add dataset templates
    template_id_object_map: Dict[str, prov.ProvEntity] = {}
    for template_id in list(input_dataset_template_object_map.keys()) +\
            list(output_dataset_template_object_map.keys()):
        # check if already created template
        if template_id in universal_entity_map:
            entity = universal_entity_map[template_id]
        else:
            # otherwise create it
            entity = produce_dataset_template(
                prov_document=document,
                dataset_template_id=template_id,
                record_id=record_id
            )
        # update maps
        template_id_object_map[template_id] = entity
        universal_entity_map[template_id] = entity
        nodes[template_id] = Node(id=template_id, subtype=ItemSubType.DATASET_TEMPLATE,
                                  category=ItemCategory.ENTITY, props=NodeProps(record_ids=record_id))

    # add associations

    # Add model
    model_id: str = workflow_template.software_id
    model: prov.ProvEntity = produce_model(
        prov_document=document,
        model_id=model_id,
        record_id=record_id
    )
    # add to entity map
    universal_entity_map[model_id] = model
    nodes[model_id] = Node(id=model_id, subtype=ItemSubType.MODEL,
                           category=ItemCategory.ENTITY, props=NodeProps(record_ids=record_id))

    # Add modeller
    modeller_id = model_record.associations.modeller_id
    modeller: prov.ProvAgent = produce_modeller(
        prov_document=document,
        modeller_resource=modeller_id,
        record_id=record_id
    )
    # add to agent map
    universal_agent_map[modeller_id] = modeller
    nodes[modeller_id] = Node(id=modeller_id, subtype=ItemSubType.PERSON,
                              category=ItemCategory.AGENT, props=NodeProps(record_ids=record_id))

    # Add organisation if present
    requesting_organisation: Optional[prov.ProvAgent] = None
    organisation_id: Optional[str] = model_record.associations.requesting_organisation_id
    if organisation_id is not None:
        requesting_organisation = produce_organisation(
            prov_document=document,
            organisation_resource=organisation_id,
            record_id=record_id
        )
        # add to agent map
        universal_agent_map[organisation_id] = requesting_organisation
        nodes[organisation_id] = Node(id=organisation_id, subtype=ItemSubType.ORGANISATION,
                                      category=ItemCategory.AGENT, props=NodeProps(record_ids=record_id))

    """
    ================
    CREATE RELATIONS
    ================
    """

    # if the model run is part of study, Model Run - wasInformedBy -> Study
    if study_id is not None:
        model_run_activity.wasInformedBy(
            informant=universal_activity_map[study_id]
        )
        source = nodes[record_id]
        target = nodes[study_id]
        links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.WAS_INFORMED_BY,
                                                 source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # model run used input datasets
    for dataset_list in input_dataset_template_object_map.values():
        for dataset in dataset_list:
            model_run_activity.used(
                entity=dataset
            )
            source = nodes[record_id]
            target = nodes[str(dataset.identifier)]
            links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.USED,
                                                     source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # output datasets --wasGeneratedBy--> model run activity
    for dataset_list in output_dataset_template_object_map.values():
        for dataset in dataset_list:
            # this may be a duplicate but should not matter TODO validate that a
            # dataset which fulfils multiple templates doesn't have the used
            # relation multiple times
            dataset.wasGeneratedBy(
                activity=model_run_activity
            )
            source = nodes[str(dataset.identifier)]
            target = nodes[str(model_run_activity.identifier)]
            links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.WAS_GENERATED_BY,
                                                     source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # model run --used--> model
    model_run_activity.used(
        entity=model
    )

    source = nodes[str(model_run_activity.identifier)]
    target = nodes[str(model.identifier)]
    links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.USED,
                                             source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # mark the model run as using the workflow definition
    model_run_activity.used(
        entity=workflow_template_entity
    )

    source = nodes[str(model_run_activity.identifier)]
    target = nodes[str(workflow_template_entity.identifier)]
    links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.USED,
                                             source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # explicit association additionally
    # model run --wasAssociatedWith--> modeller
    model_run_activity.wasAssociatedWith(
        agent=modeller
    )
    source = nodes[str(model_run_activity.identifier)]
    target = nodes[str(modeller.identifier)]
    links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.WAS_ASSOCIATED_WITH,
                                             source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # model run --wasAssociatedWith--> requesting_organisation
    # TODO redirect through 'on behalf of qualified association'
    if requesting_organisation:
        model_run_activity.wasAssociatedWith(
            agent=requesting_organisation
        )
        source = nodes[str(model_run_activity.identifier)]
        target = nodes[str(requesting_organisation.identifier)]
        links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.WAS_ASSOCIATED_WITH,
                                                 source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # output datasets --wasAttributedTo--> modeller
    for dataset_list in output_dataset_template_object_map.values():
        for dataset in dataset_list:
            dataset.wasAttributedTo(
                agent=modeller
            )
            source = nodes[str(dataset.identifier)]
            target = nodes[str(modeller.identifier)]
            links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.WAS_ATTRIBUTED_TO,
                                                     source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # add relation between datasets and their dataset template
    for template_id, template_entity in template_id_object_map.items():
        # link the template into the workflow definition
        workflow_template_entity.hadMember(
            entity=template_entity
        )
        source = nodes[str(workflow_template_entity.identifier)]
        target = nodes[str(template_entity.identifier)]
        links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.HAD_MEMBER,
                                                 source=source, target=target, props=NodeLinkProps(record_ids=record_id))

        if template_id in input_dataset_template_object_map:
            # there was an input(s) which fulfilled this template
            input_dataset_entities = input_dataset_template_object_map[template_id]
            for input_dataset_entity in input_dataset_entities:
                document.influence(
                    influencee=input_dataset_entity,
                    influencer=template_entity
                )
                source = nodes[str(input_dataset_entity.identifier)]
                target = nodes[str(template_entity.identifier)]
                links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.WAS_INFLUENCED_BY,
                                                         source=source, target=target, props=NodeLinkProps(record_ids=record_id))

        if template_id in output_dataset_template_object_map:
            # there was an output(s) which fulfilled this template
            output_dataset_entities = output_dataset_template_object_map[template_id]
            for output_dataset_entity in output_dataset_entities:
                document.influence(
                    influencee=output_dataset_entity,
                    influencer=template_entity
                )
                source = nodes[str(output_dataset_entity.identifier)]
                target = nodes[str(template_entity.identifier)]
                links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.WAS_INFLUENCED_BY,
                                                         source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # link the model/software entity as a member of the workflow definition
    workflow_template_entity.hadMember(
        entity=model
    )
    source = nodes[str(workflow_template_entity.identifier)]
    target = nodes[str(model.identifier)]
    links[(source.id, target.id)] = NodeLink(relation=ProvORelationType.HAD_MEMBER,
                                             source=source, target=target, props=NodeLinkProps(record_ids=record_id))

    # now build the graph from the nodes and links
    return NodeGraph.from_link_map(record_id=record_id, links=links), document
