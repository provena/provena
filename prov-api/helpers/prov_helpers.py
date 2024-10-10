from ProvenaInterfaces.ProvenanceModels import *
from ProvenaInterfaces.RegistryModels import *
from helpers.prov_connector import GraphBuilder, Node, NodeProps, NodeLink, NodeGraph, ProvORelationType, NodeLinkProps
from typing import List, Dict


def model_run_to_graph(model_record: ModelRunRecord, record_id: str, workflow_template: ItemModelRunWorkflowTemplate) -> NodeGraph:
    """

    Creates a NodeGraph out of a model run + record ID. 

    The record ID is the tentative ID of the model run in the registry. 

    This graph is considered a 'record' in the graph, therefore marking each
    record with this id in the node/link props.

    Parameters
    ----------
    model_record : ModelRunRecord
        The record to convert
    record_id : str
        The ID of the record
    workflow_template : ItemModelRunWorkflowTemplate
        The template used - this is resolved since we require info inside it.

    Returns
    -------
    NodeGraph
        The resulting graph
    """

    # setup graph object builder
    builder = GraphBuilder(record_id=record_id)

    """
    ============
    CREATE NODES
    ============
    """
    builder.add_node(
        Node(id=record_id, subtype=ItemSubType.MODEL_RUN,
             category=ItemCategory.ACTIVITY, props=NodeProps(record_ids=record_id))
    )

    # setup default node and link props
    node_props = NodeProps(record_ids=record_id)
    link_props = NodeLinkProps(record_ids=record_id)

    # Create study if provided
    study_id = model_record.study_id
    if study_id is not None:
        builder.add_node(Node(id=study_id, subtype=ItemSubType.STUDY,
                              category=ItemCategory.ACTIVITY, props=node_props))

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

    # links the template ID -> the dataset(s) id that fulfil it
    input_dataset_template_object_map: Dict[str, List[str]] = {}
    output_dataset_template_object_map: Dict[str, List[str]] = {}

    for template_id, templated_datasets in provided_input_map.items():
        for templated_dataset in templated_datasets:
            if templated_dataset.dataset_type != DatasetType.DATA_STORE:
                # TODO implement other prov models for non IS registered data
                raise NotImplementedError(
                    f"Can only handle data store registered items. Template ID {template_id}.")

            # pull dataset id
            dataset_id = templated_dataset.dataset_id

            # will be replaced if already exists
            builder.add_node(Node(id=dataset_id, subtype=ItemSubType.DATASET,
                                  category=ItemCategory.ENTITY, props=node_props))

            # link the template ID -> prov entity
            datasets_match_list = input_dataset_template_object_map.get(
                template_id, [])
            datasets_match_list.append(dataset_id)
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

            # will be replaced if already exists
            builder.add_node(Node(id=dataset_id, subtype=ItemSubType.DATASET,
                                  category=ItemCategory.ENTITY, props=node_props))

            # link the template ID -> prov entity
            datasets_match_list = output_dataset_template_object_map.get(
                template_id, [])
            datasets_match_list.append(dataset_id)
            output_dataset_template_object_map[template_id] = datasets_match_list

    # add model run workflow definition
    workflow_template_id = model_record.workflow_template_id
    builder.add_node(Node(id=workflow_template_id, subtype=ItemSubType.WORKFLOW_TEMPLATE,
                          category=ItemCategory.ENTITY, props=node_props))

    # add dataset templates
    template_ids: Set[str] = set()
    for template_id in list(input_dataset_template_object_map.keys()) +\
            list(output_dataset_template_object_map.keys()):

        # create template (replace if duplicate)
        builder.add_node(Node(id=template_id, subtype=ItemSubType.DATASET_TEMPLATE,
                              category=ItemCategory.ENTITY, props=node_props))

        # update maps
        template_ids.add(template_id)

    # add associations

    # Add model
    model_id: str = workflow_template.software_id
    builder.add_node(Node(id=model_id, subtype=ItemSubType.MODEL,
                          category=ItemCategory.ENTITY, props=node_props))

    # Add modeller
    modeller_id = model_record.associations.modeller_id
    builder.add_node(Node(id=modeller_id, subtype=ItemSubType.PERSON,
                          category=ItemCategory.AGENT, props=node_props))

    # Add organisation if present
    organisation_id: Optional[str] = model_record.associations.requesting_organisation_id
    if organisation_id is not None:
        builder.add_node(Node(id=organisation_id, subtype=ItemSubType.ORGANISATION,
                              category=ItemCategory.AGENT, props=node_props))

    """
    ================
    CREATE RELATIONS
    ================
    """

    # if the model run is part of study, Model Run - wasInformedBy -> Study
    if study_id is not None:
        source = builder.get_node(record_id)
        target = builder.get_node(study_id)
        builder.add_link(NodeLink(relation=ProvORelationType.WAS_INFORMED_BY,
                                  source=source, target=target, props=link_props))

    # model run used input datasets
    for dataset_id_list in input_dataset_template_object_map.values():
        for dataset_id in dataset_id_list:
            source = builder.get_node(record_id)
            target = builder.get_node(dataset_id)
            builder.add_link(NodeLink(relation=ProvORelationType.USED,
                                      source=source, target=target, props=link_props))

    # output datasets --wasGeneratedBy--> model run activity
    for dataset_id_list in output_dataset_template_object_map.values():
        for dataset_id in dataset_id_list:
            source = builder.get_node(dataset_id)
            target = builder.get_node(record_id)
            builder.add_link(NodeLink(relation=ProvORelationType.WAS_GENERATED_BY,
                                      source=source, target=target, props=link_props))

    # model run --used--> model
    source = builder.get_node(record_id)
    target = builder.get_node(model_id)
    builder.add_link(NodeLink(relation=ProvORelationType.USED,
                              source=source, target=target, props=link_props))

    # mark the model run as using the workflow definition
    source = builder.get_node(record_id)
    target = builder.get_node(workflow_template_id)
    builder.add_link(NodeLink(relation=ProvORelationType.USED,
                              source=source, target=target, props=link_props))

    # explicit association additionally
    # model run --wasAssociatedWith--> modeller
    source = builder.get_node(record_id)
    target = builder.get_node(modeller_id)
    builder.add_link(NodeLink(relation=ProvORelationType.WAS_ASSOCIATED_WITH,
                              source=source, target=target, props=link_props))

    # model run --wasAssociatedWith--> requesting_organisation
    if organisation_id is not None:
        source = builder.get_node(record_id)
        target = builder.get_node(organisation_id)
        builder.add_link(NodeLink(relation=ProvORelationType.WAS_ASSOCIATED_WITH,
                                  source=source, target=target, props=link_props))

    # output datasets --wasAttributedTo--> modeller
    for dataset_id_list in output_dataset_template_object_map.values():
        for dataset_id in dataset_id_list:
            source = builder.get_node(dataset_id)
            target = builder.get_node(modeller_id)
            builder.add_link(NodeLink(relation=ProvORelationType.WAS_ATTRIBUTED_TO,
                                      source=source, target=target, props=link_props))

    # add relation between datasets and their dataset template
    for template_id in template_ids:
        source = builder.get_node(workflow_template_id)
        target = builder.get_node(template_id)
        builder.add_link(NodeLink(relation=ProvORelationType.HAD_MEMBER,
                                  source=source, target=target, props=link_props))

        if template_id in input_dataset_template_object_map:
            # there was an input(s) which fulfilled this template
            input_dataset_entities = input_dataset_template_object_map[template_id]
            for input_dataset_id in input_dataset_entities:
                source = builder.get_node(input_dataset_id)
                target = builder.get_node(template_id)
                builder.add_link(NodeLink(relation=ProvORelationType.WAS_INFLUENCED_BY,
                                          source=source, target=target, props=link_props))

        if template_id in output_dataset_template_object_map:
            # there was an output(s) which fulfilled this template
            output_dataset_ids = output_dataset_template_object_map[template_id]
            for output_dataset_id in output_dataset_ids:
                source = builder.get_node(output_dataset_id)
                target = builder.get_node(template_id)
                builder.add_link(NodeLink(relation=ProvORelationType.WAS_INFLUENCED_BY,
                                          source=source, target=target, props=link_props))

    # link the model/software entity as a member of the workflow definition
    source = builder.get_node(workflow_template_id)
    target = builder.get_node(model_id)
    builder.add_link(NodeLink(relation=ProvORelationType.HAD_MEMBER,
                              source=source, target=target, props=link_props))

    return builder.build()


def create_to_graph(created_item_id: str, created_item_subtype: ItemSubType, create_activity_id: str, agent_id: str) -> NodeGraph:
    """
    Generates a graph representation of a creation activity.
    Ready to be lodged into graph DB.

    Args:
        created_item_id (str): The ID of the created item
        created_item_subtype (ItemSubType): The subtype of the created item
        (currently assumed to be Entity category)
        create_activity_id (str): The creation activity ID
        agent_id (str): The agent to link to
    Returns:
        NodeGraph: The realised node graph
    """

    # Setup graph object builder
    builder = GraphBuilder(record_id=create_activity_id)

    # setup default node and link props
    node_props = NodeProps(record_ids=create_activity_id)
    link_props = NodeLinkProps(record_ids=create_activity_id)

    """
    ==============
    CREATE OBJECTS
    ==============
    """
    # Create activity
    builder.add_node(
        Node(id=create_activity_id, subtype=ItemSubType.CREATE,
             category=ItemCategory.ACTIVITY, props=node_props)
    )

    # Add Agent
    builder.add_node(
        Node(id=agent_id, subtype=ItemSubType.PERSON,
             category=ItemCategory.AGENT, props=node_props)
    )

    # Create the correct item created
    builder.add_node(
        Node(id=created_item_id, subtype=created_item_subtype,
             category=ItemCategory.ENTITY, props=node_props)
    )

    """
    ================
    CREATE RELATIONS
    ================
    """
    # mark that the created item was generated by the create activity
    builder.add_link(
        NodeLink(relation=ProvORelationType.WAS_GENERATED_BY,
                 source=builder.get_node(created_item_id),
                 target=builder.get_node(create_activity_id),
                 props=link_props)
    )

    # activity was associated with agent
    builder.add_link(
        NodeLink(relation=ProvORelationType.WAS_ASSOCIATED_WITH,
                 source=builder.get_node(create_activity_id),
                 target=builder.get_node(agent_id),
                 props=link_props)
    )

    # created was attributed to agent
    builder.add_link(
        NodeLink(relation=ProvORelationType.WAS_ATTRIBUTED_TO,
                 source=builder.get_node(created_item_id),
                 target=builder.get_node(agent_id),
                 props=link_props)
    )

    return builder.build()


def version_to_graph(
    from_version_id: str,
    to_version_id: str,
    version_activity_id: str,
    item_subtype: ItemSubType,
    agent_id: str
) -> NodeGraph:
    """

    Takes information about a Version provenance activity and creates a
    NodeGraph representation

    Parameters
    ----------
    from_version_id : str
        The from item's ID
    to_version_id : str
        The to item's ID
    version_activity_id : str
        The activity ID
    item_subtype : ItemSubType
        The subtype of the item (same for from and to)
    agent_id : str
        The Person who did it

    Returns
    -------
    NodeGraph
        Resulting node graph
    """

    # Setup graph object builder
    builder = GraphBuilder(record_id=version_activity_id)

    # setup default node and link props
    node_props = NodeProps(record_ids=version_activity_id)
    link_props = NodeLinkProps(record_ids=version_activity_id)

    """
    ==============
    CREATE OBJECTS
    ==============
    """
    # Create version activity
    builder.add_node(
        Node(id=version_activity_id, subtype=ItemSubType.VERSION,
             category=ItemCategory.ACTIVITY, props=node_props)
    )

    # Add Agent
    builder.add_node(
        Node(id=agent_id, subtype=ItemSubType.PERSON,
             category=ItemCategory.AGENT, props=node_props)
    )

    # From Entity
    builder.add_node(
        Node(id=from_version_id, subtype=item_subtype,
             category=ItemCategory.ENTITY, props=node_props)
    )

    # To Entity
    builder.add_node(
        Node(id=to_version_id, subtype=item_subtype,
             category=ItemCategory.ENTITY, props=node_props)
    )

    """
    ================
    CREATE RELATIONS
    ================
    """
    # mark that the created item was generated by the create activity
    builder.add_link(
        NodeLink(relation=ProvORelationType.WAS_GENERATED_BY,
                 source=builder.get_node(to_version_id),
                 target=builder.get_node(version_activity_id),
                 props=link_props)
    )

    # activity was associated with agent
    builder.add_link(
        NodeLink(relation=ProvORelationType.WAS_ASSOCIATED_WITH,
                 source=builder.get_node(version_activity_id),
                 target=builder.get_node(agent_id),
                 props=link_props)
    )

    # created was attributed to agent
    builder.add_link(
        NodeLink(relation=ProvORelationType.WAS_ATTRIBUTED_TO,
                 source=builder.get_node(to_version_id),
                 target=builder.get_node(agent_id),
                 props=link_props)
    )

    # create activity used from
    builder.add_link(
        NodeLink(relation=ProvORelationType.USED,
                 source=builder.get_node(version_activity_id),
                 target=builder.get_node(from_version_id),
                 props=link_props)
    )

    return builder.build()
