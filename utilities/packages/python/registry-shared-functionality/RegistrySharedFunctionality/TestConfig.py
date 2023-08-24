from typing import TypeVar, Generic, Type
from SharedInterfaces.RegistryAPI import *
from SharedInterfaces.ProvenanceModels import *
from dataclasses import dataclass
from datetime import datetime

# Type variables to describe generic parent classes
SeedResponseTypeVar = TypeVar(
    'SeedResponseTypeVar', bound=Union[None, GenericSeedResponse])
FetchResponseTypeVar = TypeVar(
    'FetchResponseTypeVar', bound=GenericFetchResponse)
ListResponseTypeVar = TypeVar(
    'ListResponseTypeVar', bound=GenericListResponse)
CreateResponseTypeVar = TypeVar(
    'CreateResponseTypeVar', bound=Union[None, GenericCreateResponse])
ItemModelTypeVar = TypeVar('ItemModelTypeVar', bound=ItemBase)
ItemDomainInfoTypeVar = TypeVar('ItemDomainInfoTypeVar', bound=DomainInfoBase)

# Generic based data class for containing
# typing classes


@dataclass
class TypeParameters(Generic[
    ItemDomainInfoTypeVar,
    ItemModelTypeVar,
    SeedResponseTypeVar,
    FetchResponseTypeVar,
    ListResponseTypeVar,
    CreateResponseTypeVar
]):
    domain_info: Type[ItemDomainInfoTypeVar]
    item_model: Type[ItemModelTypeVar]
    seed_response: Optional[Type[SeedResponseTypeVar]]
    fetch_response: Type[FetchResponseTypeVar]
    list_response: Type[ListResponseTypeVar]
    create_response: Optional[Type[CreateResponseTypeVar]]

# Class containing example models for each required type
# e.g. create requires example domain info types


@dataclass
class ModelExamples(Generic[ItemDomainInfoTypeVar]):
    domain_info: List[ItemDomainInfoTypeVar]

# Collection of parameters for each test


@dataclass
class RouteParameters(Generic[
    ItemDomainInfoTypeVar,
    ItemModelTypeVar,
    SeedResponseTypeVar,
    FetchResponseTypeVar,
    ListResponseTypeVar,
    CreateResponseTypeVar
]):
    route: str
    name: str

    # this is required for dataset/model run which only have proxy variant of
    # seed/create/update routes and require the special roles
    category: ItemCategory
    subtype: ItemSubType

    typing_information: TypeParameters[
        ItemDomainInfoTypeVar,
        ItemModelTypeVar,
        SeedResponseTypeVar,
        FetchResponseTypeVar,
        ListResponseTypeVar,
        CreateResponseTypeVar
    ]
    model_examples: ModelExamples[
        ItemDomainInfoTypeVar
    ]

    use_special_proxy_modify_routes: bool = False


route_params: List[RouteParameters] = [
    # ACTIVITY - MODEL RUN
    RouteParameters(
        use_special_proxy_modify_routes=True,
        route="/activity/model_run",
        name="Activity - Model Run",
        category=ItemCategory.ACTIVITY,
        subtype=ItemSubType.MODEL_RUN,
        typing_information=TypeParameters[
            ModelRunDomainInfo,
            ItemModelRun,
            ModelRunSeedResponse,
            ModelRunFetchResponse,
            ModelRunListResponse,
            ModelRunCreateResponse
        ](
            domain_info=ModelRunDomainInfo,
            item_model=ItemModelRun,
            seed_response=ModelRunSeedResponse,
            fetch_response=ModelRunFetchResponse,
            list_response=ModelRunListResponse,
            create_response=ModelRunCreateResponse
        ),
        model_examples=ModelExamples[ModelRunDomainInfo](
            domain_info=[
                ModelRunDomainInfo(
                    display_name="Example model run",
                    prov_serialisation="Blank prov document",
                    record_status=WorkflowRunCompletionStatus.COMPLETE,
                    record=ModelRunRecord(
                        workflow_template_id="1234",
                        inputs=[TemplatedDataset(
                            dataset_template_id="1234",
                            dataset_id="1234",
                            dataset_type=DatasetType.DATA_STORE,
                            resources={
                                '1234': '/path/to/resource.csv'
                            }
                        )],
                        outputs=[TemplatedDataset(
                            dataset_template_id="1234",
                            dataset_id="1234",
                            dataset_type=DatasetType.DATA_STORE,
                            resources={
                                '1234': '/path/to/resource.csv'
                            }
                        )],
                        associations=AssociationInfo(
                            modeller_id="3247uy82",
                            requesting_organisation_id="58493058"
                        ),
                        start_time=(datetime.now().timestamp()),
                        end_time=(datetime.now().timestamp()),
                        display_name="Example model run",
                        description="This is a fake model run",
                        annotations={
                            'somekey': 'somevalue'
                        }
                    )
                ),
                ModelRunDomainInfo(
                    display_name="Example model run 2",
                    prov_serialisation="Blank prov document 2",
                    record_status=WorkflowRunCompletionStatus.COMPLETE,
                    record=ModelRunRecord(
                        workflow_template_id="12345",
                        inputs=[TemplatedDataset(
                            dataset_template_id="12354",
                            dataset_id="15234",
                            dataset_type=DatasetType.DATA_STORE,
                            resources={
                                '12534': '/path/to/resource.csv'
                            }
                        )],
                        outputs=[],
                        associations=AssociationInfo(
                            modeller_id="324dsjfilks7uy82",
                            requesting_organisation_id="584jdlsf93058"
                        ),
                        display_name="Example model run 2",
                        description="This is a fake model run 2",
                        start_time=(datetime.now().timestamp()),
                        end_time=(datetime.now().timestamp()),
                    )
                )
            ]

        )
    ),
    # ENTITY - DATASET
    RouteParameters(
        use_special_proxy_modify_routes=True,
        route="/entity/dataset",
        name="Entity - Dataset",
        category=ItemCategory.ENTITY,
        subtype=ItemSubType.DATASET,
        typing_information=TypeParameters[
            DatasetDomainInfo,
            ItemDataset,
            DatasetSeedResponse,
            DatasetFetchResponse,
            DatasetListResponse,
            DatasetCreateResponse
        ](
            domain_info=DatasetDomainInfo,
            item_model=ItemDataset,
            seed_response=DatasetSeedResponse,
            fetch_response=DatasetFetchResponse,
            list_response=DatasetListResponse,
            create_response=DatasetCreateResponse
        ),
        model_examples=ModelExamples[DatasetDomainInfo](
            domain_info=[
                DatasetDomainInfo(
                    display_name="example dataset 1",
                    collection_format=CollectionFormat(
                        associations=CollectionFormatAssociations(
                            organisation_id="1234"
                        ),
                        approvals=CollectionFormatApprovals(
                            ethics_registration=DatasetEthicsRegistrationCheck(),
                            ethics_access=DatasetEthicsAccessCheck(),
                            indigenous_knowledge=IndigenousKnowledgeCheck(
                            ),
                            export_controls=ExportControls(
                            )
                        ),
                        dataset_info=CollectionFormatDatasetInfo(
                            name='test dataset 1',
                            description='test dataset 1',
                            access_info=AccessInfo(reposited=True),
                            publisher_id="1234",
                            created_date=date.today(),
                            published_date=date.today(),
                            license="https://example.com",
                            keywords=["a", "b"]
                        )
                    ),
                    s3=S3Location(
                        bucket_name="example",
                        path="example",
                        s3_uri="example"
                    )
                ),
                DatasetDomainInfo(
                    display_name="example dataset 2",
                    collection_format=CollectionFormat(
                        associations=CollectionFormatAssociations(
                            organisation_id="12345"
                        ),
                        approvals=CollectionFormatApprovals(
                            ethics_registration=DatasetEthicsRegistrationCheck(),
                            ethics_access=DatasetEthicsAccessCheck(),
                            indigenous_knowledge=IndigenousKnowledgeCheck(
                            ),
                            export_controls=ExportControls(
                            )
                        ),
                        dataset_info=CollectionFormatDatasetInfo(
                            name='test dataset 2',
                            description='test dataset 2',
                            access_info=AccessInfo(
                                reposited=False,
                                uri="https://fake.url.com/resource",
                                description="You can access this fake dataset by doing nothing at all!"
                            ),
                            publisher_id="1234",
                            created_date=date.today(),
                            published_date=date.today(),
                            license="https://example.com",
                        )
                    ),
                    s3=S3Location(
                        bucket_name="example",
                        path="example",
                        s3_uri="example"
                    )
                ),
            ]

        )
    ),
    # AGENT - ORGANISATION
    RouteParameters(
        route="/agent/organisation",
        name="Agent - Organisation",
        category=ItemCategory.AGENT,
        subtype=ItemSubType.ORGANISATION,
        typing_information=TypeParameters[
            OrganisationDomainInfo,
            ItemOrganisation,
            OrganisationSeedResponse,
            OrganisationFetchResponse,
            OrganisationListResponse,
            OrganisationCreateResponse
        ](
            domain_info=OrganisationDomainInfo,
            item_model=ItemOrganisation,
            seed_response=OrganisationSeedResponse,
            fetch_response=OrganisationFetchResponse,
            list_response=OrganisationListResponse,
            create_response=OrganisationCreateResponse
        ),
        model_examples=ModelExamples[OrganisationDomainInfo](
            domain_info=[
                OrganisationDomainInfo(
                    display_name="Test org",
                    name="Test org",
                    ror="http://example.org/test-org"
                ),
                OrganisationDomainInfo(
                    display_name="Test org updated",
                    name="Test org updated",
                    ror="http://example.org/test-org"
                )
            ]
        )
    ),

    # AGENT - PERSON
    RouteParameters(
        route="/agent/person",
        name="Agent - Person",
        category=ItemCategory.AGENT,
        subtype=ItemSubType.PERSON,
        typing_information=TypeParameters[
            PersonDomainInfo,
            ItemPerson,
            PersonSeedResponse,
            PersonFetchResponse,
            PersonListResponse,
            PersonCreateResponse
        ](
            domain_info=PersonDomainInfo,
            item_model=ItemPerson,
            seed_response=PersonSeedResponse,
            fetch_response=PersonFetchResponse,
            list_response=PersonListResponse,
            create_response=PersonCreateResponse
        ),
        model_examples=ModelExamples[PersonDomainInfo](
            domain_info=[
                PersonDomainInfo(
                    display_name="Le Test bot",
                    first_name="Test",
                    last_name="Boy",
                    email="test@example.com",
                    orcid="https://orcid.org/0000-1234-1234-1234",
                    ethics_approved=True
                ),
                PersonDomainInfo(
                    display_name="Le Test bot updated",
                    first_name="Test",
                    last_name="Man",
                    email="test@example.com",
                    orcid="https://orcid.org/0000-1234-1234-1234",
                    ethics_approved=True
                )
            ]
        )
    ),
    # ENTITY - MODEL
    RouteParameters(
        route="/entity/model",
        name="Entity - Model",
        category=ItemCategory.ENTITY,
        subtype=ItemSubType.MODEL,
        typing_information=TypeParameters[
            ModelDomainInfo,
            ItemModel,
            ModelSeedResponse,
            ModelFetchResponse,
            ModelListResponse,
            ModelCreateResponse
        ](
            domain_info=ModelDomainInfo,
            item_model=ItemModel,
            seed_response=ModelSeedResponse,
            fetch_response=ModelFetchResponse,
            list_response=ModelListResponse,
            create_response=ModelCreateResponse
        ),
        model_examples=ModelExamples[ModelDomainInfo](
            domain_info=[
                ModelDomainInfo(
                    display_name="Example model",
                    name="Example model",
                    description="This is a fake model",
                    documentation_url="https://example_model.org",
                    source_url="https://example_model.org"
                ),
                ModelDomainInfo(
                    display_name="Example model updated",
                    name="Example model updated",
                    description="This is a fake updated model",
                    documentation_url="https://example_model.org",
                    source_url="https://example_model.org"
                )
            ]
        )
    ),

    # ENTITY - MODEL RUN WORKFLOW DEF'N
    RouteParameters(
        route="/entity/model_run_workflow",
        name="Entity - Model Run Workflow Def'n",
        category=ItemCategory.ENTITY,
        subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,
        typing_information=TypeParameters[
            ModelRunWorkflowTemplateDomainInfo,
            ItemModelRunWorkflowTemplate,
            ModelRunWorkflowTemplateSeedResponse,
            ModelRunWorkflowTemplateFetchResponse,
            ModelRunWorkflowTemplateListResponse,
            ModelRunWorkflowTemplateCreateResponse
        ](
            domain_info=ModelRunWorkflowTemplateDomainInfo,
            item_model=ItemModelRunWorkflowTemplate,
            seed_response=ModelRunWorkflowTemplateSeedResponse,
            fetch_response=ModelRunWorkflowTemplateFetchResponse,
            list_response=ModelRunWorkflowTemplateListResponse,
            create_response=ModelRunWorkflowTemplateCreateResponse
        ),
        model_examples=ModelExamples[ModelRunWorkflowTemplateDomainInfo](
            domain_info=[
                ModelRunWorkflowTemplateDomainInfo(
                    display_name="This is an example workflow def'n for a model run",
                    software_id="1234",
                    software_version="v1.3",
                    input_templates=[
                        TemplateResource(template_id='1234', optional=False)
                    ],
                    output_templates=[
                        TemplateResource(template_id='123456')
                    ],
                    annotations=WorkflowTemplateAnnotations(
                        required=["annotation_key1"],
                        optional=["annotation_key2"]
                    )
                ),
                ModelRunWorkflowTemplateDomainInfo(
                    display_name="This is an example workflow def'n for a model run",
                    software_id="1234",
                    software_version="v1.3",
                    annotations=WorkflowTemplateAnnotations(
                        required=["annotation_key1"],
                        optional=["annotation_key2"]
                    )
                ),
                ModelRunWorkflowTemplateDomainInfo(
                    display_name="This is an updated example workflow def'n for a model run",
                    software_id="1234",
                    software_version="v1.3.3",
                    input_templates=[
                        TemplateResource(template_id='12345', optional=False)
                    ],
                    output_templates=[
                        TemplateResource(template_id='123456')
                    ],
                    annotations=WorkflowTemplateAnnotations(
                        required=["annotation_key3"],
                        optional=["annotation_key4"]
                    )
                ),
            ]
        )
    ),

    # ENTITY - DATASET TEMPLATE
    RouteParameters(
        route="/entity/dataset_template",
        name="Entity - Dataset Template",
        category=ItemCategory.ENTITY,
        subtype=ItemSubType.DATASET_TEMPLATE,
        typing_information=TypeParameters[
            DatasetTemplateDomainInfo,
            ItemDatasetTemplate,
            DatasetTemplateSeedResponse,
            DatasetTemplateFetchResponse,
            DatasetTemplateListResponse,
            DatasetTemplateCreateResponse
        ](
            domain_info=DatasetTemplateDomainInfo,
            item_model=ItemDatasetTemplate,
            seed_response=DatasetTemplateSeedResponse,
            fetch_response=DatasetTemplateFetchResponse,
            list_response=DatasetTemplateListResponse,
            create_response=DatasetTemplateCreateResponse
        ),
        model_examples=ModelExamples[DatasetTemplateDomainInfo](
            domain_info=[
                DatasetTemplateDomainInfo(
                    description="This is an example dataset template",
                    display_name="Example template",
                    defined_resources=[
                        DefinedResource(
                            usage_type=ResourceUsageType.GENERAL_DATA,
                            description="Used for connectivities",
                            path="forcing/",
                        )
                    ],
                    deferred_resources=[
                        DeferredResource(
                            usage_type=ResourceUsageType.GENERAL_DATA,
                            description="Used for connectivities",
                            key="item_key",
                        )
                    ],
                ),
                DatasetTemplateDomainInfo(
                    description="This is an example dataset template",
                    display_name="Example template",
                ),
                DatasetTemplateDomainInfo(
                    description="This is an example of an updated dataset template",
                    display_name="Example template updated",
                    defined_resources=[
                        DefinedResource(
                            usage_type=ResourceUsageType.GENERAL_DATA,
                            description="Used for connectivities",
                            path="forcing/newpath",
                        )
                    ],
                    deferred_resources=[
                        DeferredResource(
                            usage_type=ResourceUsageType.GENERAL_DATA,
                            description="Used for connectivities",
                            key="item_key",
                        )
                    ],
                ),
            ]
        )
    ),
]

# E.g. Create, Version
non_test_route_params: List[RouteParameters] = [
    # ACTIVITY - REGISTRY CREATE
    RouteParameters(
        # This is read only so not really applicable
        use_special_proxy_modify_routes=False,
        route="/activity/create",
        name="Activity - Registry Create",
        category=ItemCategory.ACTIVITY,
        subtype=ItemSubType.CREATE,
        typing_information=TypeParameters[
            CreateDomainInfo,
            ItemCreate,
            None,  # no seed response
            CreateFetchResponse,
            CreateListResponse,
            None,  # no create response
        ](
            domain_info=CreateDomainInfo,
            item_model=ItemCreate,
            seed_response=None,
            fetch_response=CreateFetchResponse,
            list_response=CreateListResponse,
            create_response=None
        ),
        model_examples=ModelExamples[CreateDomainInfo](
            domain_info=[
                CreateDomainInfo(
                    display_name="Example Registry Create Activity Entity",
                    created_item_id="1234",
                ),
                CreateDomainInfo(
                    display_name="Example Registry Create Activity Entity 2 ",
                    created_item_id="5678",
                )
            ]

        )
    ),

    # ACTIVITY - REGISTRY VERSION
    RouteParameters(
        # This is read only so not really applicable
        use_special_proxy_modify_routes=False,
        route="/activity/version",
        name="Activity - Registry Version",
        category=ItemCategory.ACTIVITY,
        subtype=ItemSubType.VERSION,
        typing_information=TypeParameters[
            VersionDomainInfo,
            ItemVersion,
            None,  # no seed response
            VersionFetchResponse,
            VersionListResponse,
            None,  # no create response
        ](
            domain_info=VersionDomainInfo,
            item_model=ItemVersion,
            seed_response=None,
            fetch_response=VersionFetchResponse,
            list_response=VersionListResponse,
            create_response=None
        ),
        model_examples=ModelExamples[VersionDomainInfo](
            domain_info=[
                VersionDomainInfo(
                    display_name="Example Registry Version Activity Entity 1",
                    from_item_id="123",
                    to_item_id="1234",
                    new_version_number=2,
                    reason="test"
                ),
                VersionDomainInfo(
                    display_name="Example Registry Version Activity Entity 2",
                    from_item_id="1234",
                    to_item_id="12345",
                    new_version_number=3,
                    reason="test 2"
                )
            ]

        )
    ),
]
