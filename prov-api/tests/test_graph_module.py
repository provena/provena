import tests.env_setup
import pytest
from typing import Dict
from helpers.prov_connector import *

# Helper function to create a test node


def create_test_node(id: str, category: ItemCategory, subtype: ItemSubType, record_ids: Optional[str] = None) -> Node:
    return Node(
        id=id,
        category=category,
        subtype=subtype,
        props=NodeProps(record_ids=record_ids if record_ids else id)
    )

# Helper function to create a test link


def create_test_link(source: Node, target: Node, relation: ProvORelationType, record_ids: Optional[str] = None) -> NodeLink:
    return NodeLink(
        source=source,
        target=target,
        relation=relation,
        props=NodeLinkProps(
            record_ids=record_ids if record_ids else f"{source},{target}")
    )

# Test Node class


def test_node_creation() -> None:
    """
    Test the creation of a Node object and its properties.
    """
    node = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET)
    assert node.id == "node1"
    assert node.category == ItemCategory.ENTITY
    assert node.subtype == ItemSubType.DATASET
    assert node.props.record_ids == "node1"


def test_node_equality() -> None:
    """
    Test that two Node objects with the same properties are considered equal.
    """
    node1 = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET)
    node2 = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET)
    assert node1 == node2


def test_node_inequality() -> None:
    """
    Test that two Node objects with different properties are not considered equal.
    """
    node1 = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET)
    node2 = create_test_node(
        "node2", ItemCategory.ENTITY, ItemSubType.DATASET)
    assert node1 != node2

# Test NodeLink class


def test_node_link_creation() -> None:
    """
    Test the creation of a NodeLink object and its properties.
    """
    source = create_test_node(
        "source", ItemCategory.ENTITY, ItemSubType.DATASET)
    target = create_test_node(
        "target", ItemCategory.ENTITY, ItemSubType.DATASET)
    link = create_test_link(
        source, target, ProvORelationType.WAS_DERIVED_FROM, "source,target")

    assert link.source == source
    assert link.target == target
    assert link.relation == ProvORelationType.WAS_DERIVED_FROM
    assert link.props.record_ids == "source,target"


def test_node_link_equality() -> None:
    """
    Test that two NodeLink objects with the same properties are considered equal.
    """
    source = create_test_node(
        "source", ItemCategory.ENTITY, ItemSubType.DATASET)
    target = create_test_node(
        "target", ItemCategory.ENTITY, ItemSubType.DATASET)
    link1 = create_test_link(
        source, target, ProvORelationType.WAS_DERIVED_FROM)
    link2 = create_test_link(
        source, target, ProvORelationType.WAS_DERIVED_FROM)
    assert link1 == link2


def test_node_link_inequality() -> None:
    """
    Test that two NodeLink objects with different properties are not considered equal.
    """
    source = create_test_node(
        "source", ItemCategory.ENTITY, ItemSubType.DATASET)
    target1 = create_test_node(
        "target1", ItemCategory.ENTITY, ItemSubType.DATASET)
    target2 = create_test_node(
        "target2", ItemCategory.ENTITY, ItemSubType.DATASET)
    link1 = create_test_link(
        source, target1, ProvORelationType.WAS_DERIVED_FROM)
    link2 = create_test_link(
        source, target2, ProvORelationType.WAS_DERIVED_FROM)
    assert link1 != link2

# Test NodeGraph class


def test_node_graph_creation() -> None:
    """
    Test the creation of a NodeGraph object and its properties.
    """
    source = create_test_node(
        "source", ItemCategory.ENTITY, ItemSubType.DATASET)
    target = create_test_node(
        "target", ItemCategory.ENTITY, ItemSubType.DATASET)
    link = create_test_link(source, target, ProvORelationType.WAS_DERIVED_FROM)
    graph = NodeGraph(record_id="graph1", links=[link])

    assert graph.record_id == "graph1"
    assert len(graph.links) == 1
    assert graph.links[0] == link


def test_node_graph_get_node_set() -> None:
    """
    Test the get_node_set method of NodeGraph.
    """
    source = create_test_node(
        "source", ItemCategory.ENTITY, ItemSubType.DATASET)
    target = create_test_node(
        "target", ItemCategory.ENTITY, ItemSubType.DATASET)
    link = create_test_link(source, target, ProvORelationType.WAS_DERIVED_FROM)
    graph = NodeGraph(record_id="graph1", links=[link])

    node_set = graph.get_node_set()
    assert len(node_set) == 2
    assert source in node_set
    assert target in node_set


def test_node_graph_get_link_set() -> None:
    """
    Test the get_link_set method of NodeGraph.
    """
    source = create_test_node(
        "source", ItemCategory.ENTITY, ItemSubType.DATASET)
    target = create_test_node(
        "target", ItemCategory.ENTITY, ItemSubType.DATASET)
    link = create_test_link(source, target, ProvORelationType.WAS_DERIVED_FROM)
    graph = NodeGraph(record_id="graph1", links=[link])

    link_set = graph.get_link_set()
    assert len(link_set) == 1
    assert link in link_set

# Test GraphBuilder class


def test_graph_builder() -> None:
    """
    Test the GraphBuilder class for constructing a NodeGraph.
    """
    builder = GraphBuilder(record_id="graph1")

    node1 = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET)
    node2 = create_test_node(
        "node2", ItemCategory.ENTITY, ItemSubType.DATASET)
    link = create_test_link(node1, node2, ProvORelationType.WAS_DERIVED_FROM)

    builder.add_node(node1)
    builder.add_node(node2)
    builder.add_link(link)

    graph = builder.build()

    assert graph.record_id == "graph1"
    assert len(graph.links) == 1
    assert graph.links[0] == link
    assert len(graph.get_node_set()) == 2


def test_graph_builder_clear() -> None:
    """
    Test the clear method of GraphBuilder.
    """
    builder = GraphBuilder(record_id="graph1")

    node = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET)
    builder.add_node(node)

    assert len(builder.node_map) == 1

    builder.clear()

    assert len(builder.node_map) == 0
    assert len(builder.link_map) == 0


def test_graph_builder_dangling_node() -> None:
    """
    Test that GraphBuilder raises an error when there's a dangling node.
    """
    builder = GraphBuilder(record_id="graph1")

    node = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET)
    builder.add_node(node)

    with pytest.raises(ValueError, match="Dangling nodes found"):
        builder.build()

# Test diff_graphs function


def test_diff_graphs_add_node() -> None:
    """
    Test the diff_graphs function for adding a new node.
    """
    old_graph = NodeGraph(record_id="graph1", links=[])

    new_node = create_test_node(
        "new_node", ItemCategory.ENTITY, ItemSubType.DATASET)
    new_graph = NodeGraph(record_id="graph1", links=[])
    new_graph.links.append(create_test_link(
        new_node, new_node, ProvORelationType.WAS_DERIVED_FROM))

    diff_actions = diff_graphs(old_graph, new_graph)

    # One for adding the node, one for adding the link
    assert len(diff_actions) == 2
    assert any(isinstance(action, AddNewNode) for action in diff_actions)


def test_diff_graphs_remove_node() -> None:
    """
    Test the diff_graphs function for removing a node.
    """
    record_id = "old_node"
    old_node = create_test_node(
        "old_node", ItemCategory.ENTITY, ItemSubType.DATASET, record_ids=record_id)
    old_graph = NodeGraph(record_id=record_id, links=[create_test_link(
        old_node, old_node, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id)])

    new_graph = NodeGraph(record_id=record_id, links=[])

    diff_actions = diff_graphs(old_graph, new_graph)

    # One for removing the node, one for removing the link
    assert len(diff_actions) == 2
    assert any(isinstance(action, RemoveNode) for action in diff_actions)


def test_diff_graphs_add_link() -> None:
    """
    Test the diff_graphs function for adding a new link.
    """
    record_id = "record_id"
    node1 = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET, record_ids=record_id)
    node2 = create_test_node(
        "node2", ItemCategory.ENTITY, ItemSubType.DATASET, record_ids=record_id)

    old_graph = NodeGraph(record_id=record_id, links=[])
    old_graph.links.append(create_test_link(
        node1, node1, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id))
    old_graph.links.append(create_test_link(
        node2, node2, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id))

    new_graph = NodeGraph(record_id=record_id, links=[])
    new_graph.links.extend(old_graph.links)
    new_graph.links.append(create_test_link(
        node1, node2, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id))

    diff_actions = diff_graphs(old_graph, new_graph)

    assert len(diff_actions) == 1
    assert isinstance(diff_actions[0], AddNewLink)


def test_diff_graphs_remove_link() -> None:
    """
    Test the diff_graphs function for removing a link.
    """
    record_id = "record_id"
    node1 = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET, record_ids=record_id)
    node2 = create_test_node(
        "node2", ItemCategory.ENTITY, ItemSubType.DATASET, record_ids=record_id)

    old_graph = NodeGraph(record_id=record_id, links=[])
    old_graph.links.append(create_test_link(
        node1, node1, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id))
    old_graph.links.append(create_test_link(
        node2, node2, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id))
    old_graph.links.append(create_test_link(
        node1, node2, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id))

    new_graph = NodeGraph(record_id=record_id, links=[])
    new_graph.links.append(create_test_link(
        node1, node1, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id))
    new_graph.links.append(create_test_link(
        node2, node2, ProvORelationType.WAS_DERIVED_FROM, record_ids=record_id))

    diff_actions = diff_graphs(old_graph, new_graph)

    assert len(diff_actions) == 1
    assert isinstance(diff_actions[0], RemoveLink)

# Test ProvORelationType


def test_provo_relation_type_from_label() -> None:
    """
    Test the get_from_label method of ProvORelationType.
    """
    assert ProvORelationType.get_from_label(
        "wasDerivedFrom") == ProvORelationType.WAS_DERIVED_FROM
    assert ProvORelationType.get_from_label(
        "was derived from") == ProvORelationType.WAS_DERIVED_FROM
    assert ProvORelationType.get_from_label(
        "WAS_DERIVED_FROM") == ProvORelationType.WAS_DERIVED_FROM

    with pytest.raises(ValueError):
        ProvORelationType.get_from_label("invalid_relation")

# Test NodeGraph to_json_pretty method


def test_node_graph_to_json_pretty() -> None:
    """
    Test the to_json_pretty method of NodeGraph.
    """
    node1 = create_test_node(
        "node1", ItemCategory.ENTITY, ItemSubType.DATASET)
    node2 = create_test_node(
        "node2", ItemCategory.ENTITY, ItemSubType.DATASET)
    link = create_test_link(node1, node2, ProvORelationType.WAS_DERIVED_FROM)

    graph = NodeGraph(record_id="graph1", links=[link])

    json_data = graph.to_json_pretty()

    assert isinstance(json_data, dict)
    assert "nodes" in json_data
    assert "links" in json_data
    assert len(json_data["nodes"]) == 2
    assert len(json_data["links"]) == 1

# Helper function to create a test node with multiple record IDs


def create_multi_record_node(id: str, category: ItemCategory, subtype: ItemSubType, record_ids: str) -> Node:
    return Node(
        id=id,
        category=category,
        subtype=subtype,
        props=NodeProps(record_ids=record_ids)
    )

# Helper function to create a test link with multiple record IDs


def create_multi_record_link(source: Node, target: Node, relation: ProvORelationType, record_ids: str) -> NodeLink:
    return NodeLink(
        source=source,
        target=target,
        relation=relation,
        props=NodeLinkProps(record_ids=record_ids)
    )


def count_trues(boolean_list: List[bool]) -> int:
    """
    Count the number of True values in a list of booleans.

    Args:
        boolean_list (List[bool]): A list of boolean values.

    Returns:
        int: The count of True values in the list.
    """
    return sum(boolean_list)


def test_diff_graphs_add_record_id_to_link() -> None:
    """
    Test the diff_graphs function for adding a record ID to an existing link.
    """
    # Graph 1
    node1 = create_test_node("node1", ItemCategory.ENTITY,
                             ItemSubType.DATASET, "graph1")
    node2 = create_test_node("node2", ItemCategory.ENTITY,
                             ItemSubType.DATASET, "graph1")
    old_link = create_multi_record_link(
        node1, node2, ProvORelationType.WAS_DERIVED_FROM, "graph1")
    old_graph = NodeGraph(record_id="graph1", links=[old_link])

    # Graph 2
    # New link which touches graph 2 with same IDs
    new_link = create_multi_record_link(
        node1, node2, ProvORelationType.WAS_DERIVED_FROM, "graph2")
    new_graph = NodeGraph(record_id="graph2", links=[new_link])

    diff_actions = diff_graphs(old_graph, new_graph)

    assert len(diff_actions) == 3
    assert count_trues([isinstance(action, AddRecordIdToLink)
                        for action in diff_actions]) == 1
    assert count_trues([isinstance(action, AddRecordIdToNode)
                        for action in diff_actions]) == 2


def test_diff_graphs_complex_scenario() -> None:
    """
    Test the diff_graphs function for a complex scenario involving multiple changes.
    """

    # In this scenario we add a new node and remove two. In one case the node is
    # deleted, in another it is retained due to an existing link

    # Create old graph
    node1 = create_multi_record_node(
        "1", ItemCategory.ENTITY, ItemSubType.DATASET, "record1")
    node2 = create_multi_record_node(
        "2", ItemCategory.ENTITY, ItemSubType.DATASET, "record1, record2")
    node3 = create_multi_record_node(
        "3", ItemCategory.ENTITY, ItemSubType.DATASET, "record1, record2")
    node4 = create_multi_record_node(
        "4", ItemCategory.ENTITY, ItemSubType.DATASET, "record1")
    link1 = create_multi_record_link(
        node1, node2, ProvORelationType.WAS_DERIVED_FROM, "record1, record2")
    link2 = create_multi_record_link(
        node1, node3, ProvORelationType.WAS_DERIVED_FROM, "record1, record2")
    link3 = create_multi_record_link(
        node1, node4, ProvORelationType.WAS_DERIVED_FROM, "record1")
    old_graph = NodeGraph(record_id="record1", links=[link1, link2, link3])

    # Create new graph with changes

    # Same as node 1
    new_node1 = create_multi_record_node(
        "1", ItemCategory.ENTITY, ItemSubType.DATASET, "record1")
    new_node2 = create_multi_record_node(
        "2", ItemCategory.ENTITY, ItemSubType.DATASET, "record1")
    new_node5 = create_multi_record_node(
        "5", ItemCategory.ENTITY, ItemSubType.DATASET, "record1")
    new_link1 = create_multi_record_link(
        new_node1, new_node2, ProvORelationType.WAS_DERIVED_FROM, "record1")
    new_link2 = create_multi_record_link(
        new_node1, new_node5, ProvORelationType.WAS_DERIVED_FROM, "record1")
    new_graph = NodeGraph(record_id="record1", links=[new_link1, new_link2])

    diff_actions = diff_graphs(old_graph, new_graph)

    # Check the number of actions
    assert len(diff_actions) == 6

    # Count the occurrences of each action type
    action_counts: Dict[str, int] = {}
    for action in diff_actions:
        action_type = type(action).__name__
        action_counts[action_type] = action_counts.get(action_type, 0) + 1

    # Verify the expected number of each action type
    assert action_counts.get('RemoveRecordIdFromNode', 0) == 1
    assert action_counts.get('RemoveRecordIdFromLink', 0) == 1
    assert action_counts.get('AddNewNode', 0) == 1
    assert action_counts.get('AddNewLink', 0) == 1
    assert action_counts.get('RemoveLink', 0) == 1
    assert action_counts.get('RemoveNode', 0) == 1
