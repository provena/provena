import prov.model as prov  # type: ignore
from SharedInterfaces.ProvenanceModels import *
from SharedInterfaces.RegistryModels import *
from typing import List, Any, Dict


def produce_attribute_set(
    item_category: ItemCategory,
    item_subtype: ItemSubType,
    id: str
) -> Dict[str, Any]:
    """    produce_attribute_set
        Produces the set of attributes to add to the python-prov object.
        These end up as direct attributes on the nodes in neo4j.

        There is currently limitations around these attributes. Namely that
        when a node is shared between model runs, there must not be a 'merge
        conflict'. A merge conflict can occur when there is an attribute with the
        same name, but different values. This is the reason why the handle ID
        for the model run record is embedded as the name of the attribute
        rather than the value.

        TODO research this further and document.

        Arguments
        ----------
        item_category : ItemCategory
            The category of the item
        item_subtype : ItemSubType
            The sub type of the item
        id : str
            The handle ID of the item

        Returns
        -------
         : Dict[str, Any]
            A set of attributes to add to the item

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return {
        f'model_run/{id}': True,
        'item_category': item_category.value,
        'item_subtype': item_subtype.value
    }


def produce_dataset_template(
    prov_document: prov.ProvDocument,
    dataset_template_id: str,
    record_id: str
) -> prov.ProvEntity:
    return prov_document.entity(
        identifier=dataset_template_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ENTITY,
            item_subtype=ItemSubType.DATASET_TEMPLATE,
            id=record_id
        ))


def produce_dataset(
    prov_document: prov.ProvDocument,
    dataset_id: str,
    record_id: str
) -> prov.ProvEntity:
    """    produce_dataset
        Produces the python prov dataset object. 


        Arguments
        ----------
        prov_document : prov.ProvDocument
            The parent python prov document
        dataset_resource : DatasetResource
            The dataset resource 
        record_id : str
            The model run record id

        Returns
        -------
         : prov.ProvEntity
            The python prov entity

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return prov_document.entity(
        identifier=dataset_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ENTITY,
            item_subtype=ItemSubType.DATASET,
            id=record_id
        ))


def produce_workflow_template(
    prov_document: prov.ProvDocument,
    workflow_template_id: str,
    record_id: str
) -> prov.ProvEntity:
    return prov_document.collection(
        identifier=workflow_template_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ENTITY,
            item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,
            id=record_id
        )
    )


def produce_model(
    prov_document: prov.ProvDocument,
    model_id: str,
    record_id: str
) -> prov.ProvEntity:
    """    produce_model
        Produces the python prov entity for the model

        Arguments
        ----------
        prov_document : prov.ProvDocument
            Parent prov document
        model_resource : ModelResource
            The model information/resource
        record_id : str
            The parent model run record id

        Returns
        -------
         : prov.ProvEntity
            The python prov entity

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return prov_document.entity(
        identifier=model_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ENTITY,
            item_subtype=ItemSubType.MODEL,
            id=record_id
        )
    )


def produce_modeller(
    prov_document: prov.ProvDocument,
    modeller_resource: ModellerResource,
    record_id: str
) -> prov.ProvAgent:
    """    produce_modeller
        Produces a python prov modeller agent

        Arguments
        ----------
        prov_document : prov.ProvDocument
            The parent python prov document
        modeller_resource : ModellerResource
            The information about the modeller
        record_id : str
            The record id for the parent model run

        Returns
        -------
         : prov.ProvAgent
            The python prov agent

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return prov_document.agent(
        identifier=modeller_resource,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.AGENT,
            item_subtype=ItemSubType.PERSON,
            id=record_id
        )
    )


def produce_organisation(
    prov_document: prov.ProvDocument,
    organisation_resource: OrganisationResource,
    record_id: str
) -> prov.ProvAgent:
    """    produce_organisation
        Produces the python prov agent

        Arguments
        ----------
        prov_document : prov.ProvDocument
            Parent prov document
        organisation_resource : OrganisationResource
            The information about the organisation
        record_id : str
            The handle id of the parent record

        Returns
        -------
         : prov.ProvAgent
            The python prov agent

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return prov_document.agent(
        identifier=organisation_resource,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.AGENT,
            item_subtype=ItemSubType.ORGANISATION,
            id=record_id
        )
    )


def produce_prov_document_existing_handle(model_record: ModelRunRecord, record_id: str, workflow_template: ItemModelRunWorkflowTemplate) -> prov.ProvDocument:
    """    produce_prov_document
        Given the model record inputted by user and the handle ID for the
        record, will produce a python-prov prov-o document.

        This document can then be serialised for inclusion in the registry, and
        saved into the graph store.

        Arguments
        ----------
        model_record : ModelRunRecord
            The model run record provided by user which has had the IDs
            validated.
        record_id: str 
            The handle ID for the model run
        workflow_template: ItemModelRunWorkflowTemplate
            The resolved workflow definition

        Returns
        -------
         : prov.ProvDocument
            The python-prov document.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    document = prov.ProvDocument()

    # add default Provena namespace
    # if no namespace provided, this will be used
    # TODO consider namespace for identities
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
    input_dataset_template_object_map: Dict[str, List[prov.ProvEntity]] = {}
    output_dataset_template_object_map: Dict[str, List[prov.ProvEntity]] = {}

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

    # Add modeller
    modeller_id = model_record.associations.modeller_id
    modeller: prov.ProvAgent = produce_modeller(
        prov_document=document,
        modeller_resource=modeller_id,
        record_id=record_id
    )
    # add to agent map
    universal_agent_map[modeller_id] = modeller

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

    # model run used input datasets
    for dataset_list in input_dataset_template_object_map.values():
        for dataset in dataset_list:
            model_run_activity.used(
                entity=dataset
            )

    # output datasets --wasGeneratedBy--> model run activity
    for dataset_list in output_dataset_template_object_map.values():
        for dataset in dataset_list:
            # this may be a duplicate but should not matter TODO validate that a
            # dataset which fulfils multiple templates doesn't have the used
            # relation multiple times
            dataset.wasGeneratedBy(
                activity=model_run_activity
            )

    # model run --used--> model
    model_run_activity.used(
        entity=model
    )

    # mark the model run as using the workflow definition
    model_run_activity.used(
        entity=workflow_template_entity
    )

    # explicit association additionally
    # model run --wasAssociatedWith--> modeller
    model_run_activity.wasAssociatedWith(
        agent=modeller
    )

    # model run --wasAssociatedWith--> requesting_organisation
    # TODO redirect through 'on behalf of qualified association'
    if requesting_organisation:
        model_run_activity.wasAssociatedWith(
            agent=requesting_organisation
        )

    # output datasets --wasAttributedTo--> modeller
    for dataset_list in output_dataset_template_object_map.values():
        for dataset in dataset_list:
            dataset.wasAttributedTo(
                agent=modeller
            )

    # add relation between datasets and their dataset template
    for template_id, template_entity in template_id_object_map.items():
        # link the template into the workflow definition
        workflow_template_entity.hadMember(
            entity=template_entity
        )

        if template_id in input_dataset_template_object_map:
            # there was an input(s) which fulfilled this template
            input_dataset_entities = input_dataset_template_object_map[template_id]
            for input_dataset_entity in input_dataset_entities:
                document.influence(
                    influencee=input_dataset_entity,
                    influencer=template_entity
                )

        if template_id in output_dataset_template_object_map:
            # there was an output(s) which fulfilled this template
            output_dataset_entities = output_dataset_template_object_map[template_id]
            for output_dataset_entity in output_dataset_entities:
                document.influence(
                    influencee=output_dataset_entity,
                    influencer=template_entity
                )

    # link the model/software entity as a member of the workflow definition
    workflow_template_entity.hadMember(
        entity=model
    )

    return document


def produce_prov_document(model_record: ModelRunRecord, seed_item: SeededItem, workflow_template: ItemModelRunWorkflowTemplate) -> prov.ProvDocument:
    """    produce_prov_document
        Given the model record inputted by user and the newly seeded model run
        item, will produce a python-prov prov-o document.

        This document can then be serialised for inclusion in the registry, and
        saved into the graph store.

        Arguments
        ----------
        model_record : ModelRunRecord
            The model run record provided by user which has had the IDs
            validated.
        seed_item : SeededItem
            The fresh seed item which includes the handle ID to embed into record.

        Returns
        -------
         : prov.ProvDocument
            The python-prov document.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return produce_prov_document_existing_handle(model_record=model_record, record_id=seed_item.id, workflow_template=workflow_template)


def produce_create_prov_document(created_item_id: str, created_item_subtype: ItemSubType, create_activity_id: str, agent_id: str) -> prov.ProvDocument:
    """
    Generates a prov document representation of a creation activity.

    Ready to be lodged into graph DB

    Args:
        created_item_id (str): The ID of the created item

        created_item_subtype (ItemSubType): The subtype of the created item
        (currently assumed to be Entity category)

        create_activity_id (str): The creation activity ID

        agent_id (str): The agent to link to

    Returns:
        prov.ProvDocument: The realised prov document
    """
    document = prov.ProvDocument()

    # add default Provena namespace
    # if no namespace provided, this will be used
    # TODO consider namespace for identities
    document.set_default_namespace('http://hdl.handle.net/')

    """
    ==============
    CREATE OBJECTS
    ==============
    """
    # Create model run activity
    create_activity: prov.ProvActivity = document.activity(
        identifier=create_activity_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ACTIVITY,
            item_subtype=ItemSubType.CREATE,
            id=create_activity_id
        )
    )

    # Add Agent
    person: prov.ProvAgent = produce_modeller(
        prov_document=document,
        modeller_resource=agent_id,
        record_id=create_activity_id
    )

    # Create the correct item created
    # TODO validate that the item is an entity
    created: prov.ProvEntity = document.entity(
        identifier=created_item_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ENTITY,
            item_subtype=created_item_subtype,
            id=create_activity_id
        )
    )

    """
    ================
    CREATE RELATIONS
    ================
    """

    # mark that the created item was generated by the create activity
    created.wasGeneratedBy(
        activity=create_activity
    )

    # activity was associated with agent
    create_activity.wasAssociatedWith(
        agent=person
    )

    # created was attributed to agent
    created.wasAttributedTo(
        agent=person
    )

    return document


def produce_version_prov_document(
    from_version_id: str,
    to_version_id: str,
    version_activity_id: str,
    item_subtype: ItemSubType,
    agent_id: str
) -> prov.ProvDocument:
    document = prov.ProvDocument()

    # add default Provena namespace
    # if no namespace provided, this will be used
    document.set_default_namespace('http://hdl.handle.net/')

    """
    ==============
    CREATE OBJECTS
    ==============
    """
    # Create model run activity
    create_activity: prov.ProvActivity = document.activity(
        identifier=version_activity_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ACTIVITY,
            item_subtype=ItemSubType.VERSION,
            id=version_activity_id
        )
    )

    # Add Agent
    person: prov.ProvAgent = produce_modeller(
        prov_document=document,
        modeller_resource=agent_id,
        record_id=version_activity_id
    )

    # From Entity
    from_entity: prov.ProvEntity = document.entity(
        identifier=from_version_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ENTITY,
            item_subtype=item_subtype,
            id=version_activity_id
        )
    )

    # To Entity
    to_entity: prov.ProvEntity = document.entity(
        identifier=to_version_id,
        other_attributes=produce_attribute_set(
            item_category=ItemCategory.ENTITY,
            item_subtype=item_subtype,
            id=version_activity_id
        )
    )

    """
    ================
    CREATE RELATIONS
    ================
    """

    # mark that the created item was generated by the create activity
    to_entity.wasGeneratedBy(
        activity=create_activity
    )

    # activity was associated with agent
    create_activity.wasAssociatedWith(
        agent=person
    )

    # created was attributed to agent
    to_entity.wasAttributedTo(
        agent=person
    )

    # create activity used from
    create_activity.used(
        entity=from_entity
    )

    return document
