import tests.env_setup
from tests.helpers import *
from helpers.neo4j_helpers import run_query
import networkx  # type: ignore
from enum import Enum
from prov.model import ProvDocument  # type: ignore
import requests
import pytest
from typing import Tuple, Generator, Any
from fastapi.testclient import TestClient
from main import app
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency
import json
from helpers.entity_validators import RequestStyle
from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.ProvenanceAPI import *
from ProvenaInterfaces.ProvenanceModels import *
from ProvenaInterfaces.DataStoreAPI import *
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from config import Config, get_settings, base_config
from tests.test_config import *


def is_responsive(url: str) -> bool:
    """    is_responsive
        Used for pytest-docker to wait for HTTP receptiveness at a
        specified URL

        Arguments
        ----------
        url : str
            endpoint to get request

        Returns
        -------
         : bool
            true/false - true iff 200 OK

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except ConnectionError:
        return False
    except Exception:
        return False


@pytest.fixture(scope="session")
def bolt_service_host(docker_services: Any) -> str:
    """    bolt_service_host
        Gets the neo4j docker compose pytest bolt host.
        This also waits until the docker compose command
        successfully spins up the neo4j instance. There is
        a bug in the pytest-docker which means that we have
        to manually specify the docker ip rather than
        using the fixture. If it is not localhost in
        some context then we will need to work around this
        properly.

        Arguments
        ----------
        docker_services : Any
            The docker services fixture

        Returns
        -------
         : str
            The host for the bolt endpoint

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # this should use docker_ip pytest fixture but it is buggy - assume localhost
    host = "localhost"
    # get the host port for the db container port
    http_port = docker_services.port_for("db", 7474)
    # specify the wait endpoint
    test_endpoint = f"http://{host}:{http_port}"
    # fire off gets at http endpoint of neo4j browser
    docker_services.wait_until_responsive(
        timeout=60.0, pause=0.1, check=lambda: is_responsive(test_endpoint)
    )
    # return host now that it is ready
    return host


@pytest.fixture(scope="session")
def bolt_service_port(docker_services: Any, bolt_service_host: str) -> int:
    """    bolt_service_port
        This depends on the bolt service host fixture (which waits for service)
        and then gets the corresponding host port for the neo4j bolt protocol
        port 7687.

        Arguments
        ----------
        docker_services : Any
            The docker services fixture
        bolt_service_host : str
            The existing bolt service host fixture

        Returns
        -------
         : int
            The port for bolt traffic

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    port = docker_services.port_for("db", 7687)
    return port


@pytest.fixture(scope="function")
def client() -> TestClient:
    # sets up an app test client for use in
    # tests
    return TestClient(app)


@pytest.fixture(scope="function")
def service_config(
    bolt_service_port: int,
    bolt_service_host: str
) -> Config:
    """    service_config

        Returns a customised config object which
        is injected into app dependencies
        this is required to dynamically resolve
        the docker host/port for neo4j backend

        Arguments
        ----------
        bolt_service_port : int
            The neo4j bolt service port
        bolt_service_host : str
            The neo4j bolt service host

        Returns
        -------
         : Config
            The customised Config object

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    config = Config(
        stage=stage,
        keycloak_endpoint=base_config.keycloak_endpoint,
        # This should not be used
        job_api_endpoint="",
        service_account_secret_arn="",
        registry_api_endpoint="",
        mock_graph_db=False,
        neo4j_host=bolt_service_host,
        neo4j_port=bolt_service_port,
        neo4j_test_username=neo4j_username,
        neo4j_test_password=neo4j_password,
        depth_default_limit=30,
        depth_upper_limit=100
    )
    app.dependency_overrides[get_settings] = lambda: config
    return config


@pytest.fixture(scope="function")
def general_config() -> Config:
    """    general_config

        Returns a fake neo4j and other config so as to enforce no communication
        with a graph DB for non graph related tests.

        Arguments 
        ----------

        Returns
        -------
         : Config
            The customised Config object

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    config = Config(
        stage=stage,
        keycloak_endpoint=base_config.keycloak_endpoint,
        # This should not be used
        job_api_endpoint="",
        service_account_secret_arn="",
        registry_api_endpoint="",
        mock_graph_db=True,
        neo4j_host="",
        neo4j_port=0,
        neo4j_test_username="",
        neo4j_test_password="",
        depth_default_limit=30,
        depth_upper_limit=100,
    )
    app.dependency_overrides[get_settings] = lambda: config
    return config


@pytest.fixture(scope="function", autouse=True)
def override_cleanup() -> Generator:
    """    override_cleanup
        Cleans up pytest runs by overriding the dependency
        overrides back to nothing (cleans up)

        Yields
        -------
        Generator
            Yields to suggest pytest should run test
            at given point

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # run test
    yield
    # clean up overrides
    app.dependency_overrides = {}


@pytest.fixture(scope="function", autouse=True)
def db_cleanup(service_config: Config) -> Generator:
    yield
    run_query(
        query="MATCH (n) DETACH DELETE n",
        config=service_config
    )


def test_health_check(client: TestClient, service_config: Config) -> None:
    # Checks that the health check endpoint responds
    response = client.get("/")
    check_status_code(response)
    assert response.json() == {"message": "Health check successful."}


async def user_general_dependency_override() -> User:
    # Creates an override for user dependency
    return User(username=test_email, roles=['test-role'], access_token="faketoken1234", email=test_email)


async def user_protected_dependency_override() -> ProtectedRole:
    # Creates override for the role protected user dependency
    return ProtectedRole(
        access_roles=['test-role'],
        user=User(
            username=test_email,
            roles=['test-role'],
            access_token="faketoken1234",
            email=test_email
        )
    )


async def fake_seed(config: Config) -> SeededItem:
    return SeededItem(
        id=seed_id_base,
        owner_username="1234",
        created_timestamp=int(datetime.now().timestamp()),
        updated_timestamp=int(datetime.now().timestamp()),
        item_category=ItemCategory.ACTIVITY,
        item_subtype=ItemSubType.MODEL_RUN,
        record_type=RecordType.SEED_ITEM
    )


def id_fake_seed(id: str) -> Any:
    async def fake_seed(config: Config, proxy_username: Optional[str] = None) -> SeededItem:
        return SeededItem(
            id=id,
            owner_username="1234",
            created_timestamp=int(datetime.now().timestamp()),
            updated_timestamp=int(datetime.now().timestamp()),
            item_category=ItemCategory.ACTIVITY,
            item_subtype=ItemSubType.MODEL_RUN,
            record_type=RecordType.SEED_ITEM
        )
    return fake_seed


async def fake_update_model_run(
    model_run_id: str,
    model_run_domain_info: ModelRunDomainInfo,
    config: Config,
    proxy_username: Optional[str] = None,
    reason: Optional[str] = None,
) -> ItemModelRun:
    record_info = RecordInfo(
        id=model_run_id,
        owner_username="1234",
        created_timestamp=int(datetime.now().timestamp()),
        updated_timestamp=int(datetime.now().timestamp()),
        item_category=ItemCategory.ACTIVITY,
        item_subtype=ItemSubType.MODEL_RUN,
        record_type=RecordType.COMPLETE_ITEM
    )
    return ItemModelRun(
        **record_info.dict(),
        **model_run_domain_info.dict(),
        history=[]
    )


def produce_mocked_validate_workflow(postfix: str) -> Any:
    async def mocked_validate_workflow_template(id: str, config: Config, request_style: RequestStyle) -> Union[ItemModelRunWorkflowTemplate, SeededItem, str]:
        return ItemModelRunWorkflowTemplate(
            owner_username="1234",
            display_name="fake",
            software_id=model_id_base + postfix,
            input_templates=[
                TemplateResource(template_id=input_template_id_base + postfix)
            ],
            output_templates=[
                TemplateResource(template_id=output_template_id_base + postfix)
            ],
            id=workflow_defn_id_base + postfix,
            created_timestamp=int(datetime.now().timestamp()),
            updated_timestamp=int(datetime.now().timestamp()),
            record_type=RecordType.COMPLETE_ITEM,
            history=[]
        )
    return mocked_validate_workflow_template


async def fake_validator(
    id: str,
    config: Config,
    request_style: RequestStyle
) -> None:
    None


def make_exploration_request(client: TestClient, method: str, id: str, depth: Optional[int] = None) -> networkx.Graph:
    # ensure upstream is working as expected with single record
    # start at output dataset
    endpoint = f"/explore/{method}"

    params: Dict[str, Union[str, int]] = {
        'starting_id': id,
    }

    if depth is not None:
        params['depth'] = depth

    # make req
    response = client.get(endpoint, params=params)
    # check status
    check_status_code(response)

    # parse as upstream response
    response_json = response.json()
    upstream_response: LineageResponse = LineageResponse.parse_obj(
        response_json)

    # check successful
    assert upstream_response.status.success

    # get the networkx graph
    graph_serialisation = upstream_response.graph
    assert graph_serialisation

    # deserialize using networkx
    nx_graph: networkx.Graph = networkx.readwrite.json_graph.node_link_graph(
        graph_serialisation)

    # assert properties of graph
    assert nx_graph.is_directed()
    assert not nx_graph.is_multigraph()

    return nx_graph


def generate_model_run_record(postfix: str, input_override: Optional[str] = None) -> ModelRunRecord:
    return ModelRunRecord(
        workflow_template_id=workflow_defn_id_base + postfix,
        model_version="1.2",
        inputs=[
            TemplatedDataset(
                dataset_template_id=input_template_id_base + postfix,
                dataset_type=DatasetType.DATA_STORE,
                dataset_id=(input_dataset_id_base + '1' +
                            postfix) if not input_override else (input_override),
            )
        ],
        outputs=[
            TemplatedDataset(
                dataset_template_id=output_template_id_base + postfix,
                dataset_type=DatasetType.DATA_STORE,
                dataset_id=output_dataset_id_base + '0' + postfix,
            )
        ],
        associations=AssociationInfo(
            modeller_id=modeller_id_base + postfix,
            requesting_organisation_id=organisation_id_base + postfix
        ),
        display_name=display_name_id_base + postfix,
        description=description_id_base + postfix,
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp())
    )


def mocked_get_service_token(secret_cache: Any, config: Config) -> str:
    return "faketoken"


def test_upload_model_run(client: TestClient, service_config: Config, monkeypatch: Any) -> None:
    # path record_identities function
    async def mocked_validate(
        *args: Any,
        **kwargs: Any
    ) -> Tuple[bool, Optional[str]]:
        return (True, None)

    import helpers.workflows as workflow_register
    import routes.model_run.model_run as model_run_route
    import helpers.registry_helpers as registry_helpers
    import helpers.entity_validators as entity_validators
    import routes.explore.explore as explore

    monkeypatch.setattr(
        model_run_route,
        'validate_model_run_record',
        mocked_validate
    )

    monkeypatch.setattr(
        workflow_register,
        'validate_model_run_workflow_template',
        produce_mocked_validate_workflow(postfix="")
    )

    # mock the get service token function
    monkeypatch.setattr(
        registry_helpers,
        'get_service_token',
        mocked_get_service_token
    )
    monkeypatch.setattr(
        entity_validators,
        'get_service_token',
        mocked_get_service_token
    )

    # mock seed
    monkeypatch.setattr(
        workflow_register,
        'seed_model_run',
        id_fake_seed(seed_id_base)
    )

    # mock update of model run
    monkeypatch.setattr(
        workflow_register,
        'update_model_run_in_registry',
        fake_update_model_run
    )

    # patch unknown validator
    monkeypatch.setattr(
        explore,
        'unknown_validator',
        fake_validator
    )

    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    input_record: ModelRunRecord = generate_model_run_record(postfix='')

    # upload the fake model run record
    safe_serialisation = json.loads(input_record.json())
    response = client.post('/model_run/register_sync',
                           json=safe_serialisation)
    check_status_code(response)

    # parse the response
    json_content = response.json()
    response_model: SyncRegisterModelRunResponse = SyncRegisterModelRunResponse.parse_obj(
        json_content)

    # check successful
    assert response_model.status.success

    # check record is present
    record = response_model.record_info
    assert record

    # check properties seem valid

    # record id should be the seed ID
    assert record.id == seed_id_base

    # make sure record wasn't permuted
    assert record.record == input_record

    # make sure serialised prov document can be deserialised
    prov_doc: ProvDocument = ProvDocument.deserialize(
        None, content=record.prov_json, format="json")

    # make a lineage query downstream from an input file and make
    # sure expected nodes are present
    first_input_dataset_id = list(
        input_record.inputs)[0].dataset_id
    assert isinstance(first_input_dataset_id, DataStoreDatasetResource)
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='downstream',
        id=first_input_dataset_id
    )

    # check node count which should have been found
    start = 1
    activity = 1
    outputs = len(input_record.outputs)

    # should be starting, activity, and all outputs
    assert nx_graph.number_of_nodes() == (start + activity + outputs)

    # make a lineage query upstream from an output file and make
    # sure expected nodes are present
    # start at output dataset
    first_output_dataset_id = list(
        input_record.outputs)[0].dataset_id
    assert isinstance(first_output_dataset_id, DataStoreDatasetResource)
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='upstream',
        id=first_output_dataset_id
    )

    # check node count which should have been found
    start = 1 * 2  # each input has a template
    activity = 1
    model = 1
    workflow_template = 1
    associations = (
        1 + (1 if input_record.associations.requesting_organisation_id else 0))
    inputs = len(input_record.inputs) * 2  # each input has a template

    # should be starting, activity, and all outputs
    assert nx_graph.number_of_nodes() == (start + activity + model +
                                          workflow_template + associations + inputs)


class ChainPosition(str, Enum):
    CHAINED_INPUT = "CHAINED_INPUT"
    ACTIVITY = "ACTIVITY"
    OUTPUT = "OUTPUT"


def calculate_upstream_node_cardinality(chain: List[ModelRunRecord], position_in_chain: int, position_in_record: ChainPosition) -> int:
    count = 0
    # loop through indexes up to and including the given position
    for index in range(position_in_chain + 1):
        model = chain[index]
        if index != position_in_chain:
            # normal case where we aren't at end yet
            # activity (model run)
            count += 1

            # inputs
            # input datasets (count all inputs including chain - it's excluded on output side)
            count += len(model.inputs) * 2  # dataset + template

            # associations
            count += 1  # model
            count += 1  # modeller
            count += 1 if model.associations.requesting_organisation_id else 0

            # workflow definition
            count += 1

            # template for each output ds
            count += len(model.outputs) * 1

            # outputs
            # no count for output since they won't be reached
            # and we don't double count the chained output

        else:
            # we are at the terminal position
            # check the type of positional stop
            if position_in_record == ChainPosition.CHAINED_INPUT:
                # only need chained input
                # and it's template
                count += 2  # for the input chained element
            elif position_in_record == ChainPosition.ACTIVITY:
                # everything but the actual output dataset

                # normal case where we aren't at end yet
                # activity (model run)
                count += 1

                # inputs
                # input datasets (count all inputs including chain - it's excluded on output side)
                count += len(model.inputs) * 2  # dataset + template

                # associations
                count += 1  # model
                count += 1  # modeller
                count += 1 if model.associations.requesting_organisation_id else 0

                # workflow definition
                count += 1

                # template for each output ds
                count += len(model.outputs) * 1
            else:
                # OUTPUT position
                # counts everything and doesn't deduct double
                # count on output
                # everything but the actual output dataset

                # normal case where we aren't at end yet
                # activity (model run)
                count += 1

                # inputs
                # input datasets (count all inputs including chain - it's excluded on output side)
                count += len(model.inputs) * 2  # dataset + template

                # associations
                count += 1  # model
                count += 1  # modeller
                count += 1 if model.associations.requesting_organisation_id else 0

                # workflow definition
                count += 1

                # template for each output ds and the one actual ds
                count += len(model.outputs) * 1 + 1
                # add one count for the next in chain's template which is currently reached
                # TODO change relationship structure so this doesn't happen
                # only happens if not at end of chain
                if index != len(chain) - 1:
                    count += 1
    return count


def calculate_downstream_node_cardinality(chain: List[ModelRunRecord], position_in_chain: int, position_in_record: ChainPosition) -> int:
    count = 0
    # loop through indexes up to and including the given position
    for index in range(position_in_chain, len(chain)):
        model = chain[index]
        if index != position_in_chain:
            # normal case where we aren't at end yet
            # activity (model run)
            count += 1

            # outputs
            # count all outputs
            count += len(model.outputs)

        else:
            # we are at the starting position
            # check the type of positional start
            if position_in_record == ChainPosition.CHAINED_INPUT:
                # chained input
                count += 1  # for the input chained element
                # activity
                count += 1
                # count outputs
                count += len(model.outputs)

            elif position_in_record == ChainPosition.ACTIVITY:
                # activity
                count += 1
                # count outputs
                count += len(model.outputs)

            else:
                # count only single starting output
                count += 1
    return count


def test_lineage_upstream(client: TestClient, service_config: Config, monkeypatch: Any) -> None:
    # path record_identities function
    async def mocked_validate(
        *args: Any,
        **kwargs: Any
    ) -> Tuple[bool, Optional[str]]:
        return (True, None)

    import helpers.workflows as register_workflow
    import routes.model_run.model_run as model_run_route
    import helpers.registry_helpers as registry_helpers
    import helpers.entity_validators as entity_validators
    import routes.explore.explore as explore

    monkeypatch.setattr(
        model_run_route,
        'validate_model_run_record',
        mocked_validate
    )

    # mock the get service token function
    monkeypatch.setattr(
        registry_helpers,
        'get_service_token',
        mocked_get_service_token
    )
    monkeypatch.setattr(
        entity_validators,
        'get_service_token',
        mocked_get_service_token
    )

    # mock update of model run
    monkeypatch.setattr(
        register_workflow,
        'update_model_run_in_registry',
        fake_update_model_run
    )

    # patch unknown validator
    monkeypatch.setattr(
        explore,
        'unknown_validator',
        fake_validator
    )

    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    created_models: List[ModelRunRecord] = []

    # start by uploading single record

    # mock seed
    monkeypatch.setattr(
        register_workflow,
        'seed_model_run',
        id_fake_seed(seed_id_base + '0')
    )

    created_models.append(generate_model_run_record(postfix='0'))
    monkeypatch.setattr(
        register_workflow,
        'validate_model_run_workflow_template',
        produce_mocked_validate_workflow(postfix="0")
    )

    # upload the fake model run record
    safe_serialisation = json.loads(created_models[0].json())
    response = client.post('/model_run/register_sync',
                           json=safe_serialisation)
    check_status_code(response)

    first_output_dataset_id = created_models[0].outputs[0].dataset_id

    # explore upstream
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='upstream',
        id=first_output_dataset_id
    )

    # check node count which should have been found
    start = 1  # ds
    templates = len(created_models[0].outputs)  # templates
    activity = 1
    workflow_template = 1
    associations = (
        2 + (1 if created_models[0].associations.requesting_organisation_id else 0))
    inputs = len(created_models[0].inputs) * 2  # and template for each
    total = sum([start, templates, activity,
                workflow_template, associations, inputs])
    assert nx_graph.number_of_nodes() == total

    # create a connected chain of records
    modelRuns: List[Tuple[ModelRunRecord, str]] = []
    prev: Optional[ModelRunRecord] = None

    for index in range(chain_size):
        id_postfix = 'chain' + str(index)
        id_override: Optional[str] = None

        # make the chain
        if prev:
            id_override = (list(prev.outputs)[0]).dataset_id

        # create record
        new_record = generate_model_run_record(
            postfix=id_postfix,
            input_override=id_override
        )

        # override the response from workflow definition
        # resolution to use specified postfix so that
        # everything lines up
        monkeypatch.setattr(
            register_workflow,
            'validate_model_run_workflow_template',
            produce_mocked_validate_workflow(postfix=id_postfix)
        )

        # override the seed mock to add unique
        # model run id
        # mock seed
        monkeypatch.setattr(
            register_workflow,
            'seed_model_run',
            id_fake_seed(seed_id_base + 'chain' + str(index))
        )

        # upload the fake model run record
        safe_serialisation = json.loads(new_record.json())
        response = client.post('/model_run/register_sync',
                               json=safe_serialisation)
        check_status_code(response)
        parsed_response: SyncRegisterModelRunResponse = SyncRegisterModelRunResponse.parse_obj(
            response.json())
        assert parsed_response.status.success
        assert parsed_response.record_info
        model_run_id: str = parsed_response.record_info.id

        # add to chain
        modelRuns.append((new_record, model_run_id))

        # update previous to enable chaining
        prev = new_record

    # get just chain
    model_chain: List[ModelRunRecord] = [model_and_id[0]
                                         for model_and_id in modelRuns]

    for index in range(chain_size):
        model: ModelRunRecord = modelRuns[index][0]
        model_run_record_id: str = modelRuns[index][1]

        for starting_position in ChainPosition:
            # work out correct count
            correct_count = calculate_upstream_node_cardinality(
                chain=model_chain,
                position_in_chain=index,
                position_in_record=starting_position
            )

            graph: networkx.Graph

            if starting_position == ChainPosition.CHAINED_INPUT:
                desired_id = model.inputs[0].dataset_id
                # Make the query
                graph = make_exploration_request(
                    client=client,
                    method='upstream',
                    # override is always first in datasets
                    id=desired_id
                )
            elif starting_position == ChainPosition.ACTIVITY:
                graph = make_exploration_request(
                    client=client,
                    method='upstream',
                    # start at activity
                    id=model_run_record_id
                )
            else:
                desired_id = model.outputs[0].dataset_id
                graph = make_exploration_request(
                    client=client,
                    method='upstream',
                    # start at only output dataset
                    id=desired_id
                )

            actual_count = graph.number_of_nodes()
            assert actual_count == correct_count, f"Received graph with nodes: {actual_count} \
                   did not match expected count of {correct_count} for index {index} and chain\
                   position {starting_position.value}."

    # explore upstream - contributing datasets
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='special/contributing_datasets',
        id=first_output_dataset_id,
        depth=3
    )

    assert nx_graph.number_of_nodes(
    ) == 3

    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='special/contributing_datasets',
        # Starting at 3rd entry in chain output
        id=model_chain[2].outputs[0].dataset_id,
        depth=6
    )

    assert nx_graph.number_of_nodes() == 7

    # explore downstream - effected datasets
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='special/effected_datasets',
        id=model_chain[0].inputs[0].dataset_id,
        depth=2
    )

    assert nx_graph.number_of_nodes(
    ) == 3

    # explore downstream - effected datasets
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='special/effected_datasets',
        id=model_chain[2].inputs[0].dataset_id,
        depth=6
    )

    assert nx_graph.number_of_nodes(
    ) == 7

    # explore upstream - contributing agents
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='special/contributing_agents',
        id=model_chain[0].outputs[0].dataset_id,
        depth=2
    )

    # two nodes, two agents
    assert nx_graph.number_of_nodes(
    ) == 4

    # explore upstream - contributing agents
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='special/contributing_agents',
        id=model_chain[2].outputs[0].dataset_id,
        depth=6
    )

    # 6 agents, 6 nodes
    assert nx_graph.number_of_nodes(
    ) == 12

    # explore downstream - effected agents
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='special/effected_agents',
        id=model_chain[0].inputs[0].dataset_id,
        depth=2
    )

    # three nodes, 2 agents
    assert nx_graph.number_of_nodes(
    ) == 5

    # explore downstream - effected agents
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='special/effected_agents',
        id=model_chain[2].inputs[0].dataset_id,
        depth=6
    )

    # 6 agents, 6 nodes
    assert nx_graph.number_of_nodes(
    ) == 14


def test_lineage_downstream(client: TestClient, service_config: Config, monkeypatch: Any) -> None:
    # path record_identities function
    async def mocked_validate(
        *args: Any,
        **kwargs: Any
    ) -> Tuple[bool, Optional[str]]:
        return (True, None)

    import helpers.workflows as register_workflow
    import helpers.registry_helpers as registry_helpers
    import routes.model_run.model_run as model_run_route
    import helpers.entity_validators as entity_validators
    import routes.explore.explore as explore

    monkeypatch.setattr(
        model_run_route,
        'validate_model_run_record',
        mocked_validate
    )

    # mock the get service token function
    monkeypatch.setattr(
        registry_helpers,
        'get_service_token',
        mocked_get_service_token
    )
    monkeypatch.setattr(
        entity_validators,
        'get_service_token',
        mocked_get_service_token
    )

    # mock update of model run
    monkeypatch.setattr(
        register_workflow,
        'update_model_run_in_registry',
        fake_update_model_run
    )

    # patch unknown validator
    monkeypatch.setattr(
        explore,
        'unknown_validator',
        fake_validator
    )

    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    created_models: List[ModelRunRecord] = []

    # start by uploading single record

    # mock seed
    monkeypatch.setattr(
        register_workflow,
        'seed_model_run',
        id_fake_seed(seed_id_base + '0')
    )

    monkeypatch.setattr(
        register_workflow,
        'validate_model_run_workflow_template',
        produce_mocked_validate_workflow(postfix="0")
    )
    created_models.append(generate_model_run_record(postfix='0'))

    # upload the fake model run record
    safe_serialisation = json.loads(created_models[0].json())
    response = client.post('/model_run/register_sync',
                           json=safe_serialisation)
    check_status_code(response)

    # explore downstream
    first_input_dataset = created_models[0].inputs[0].dataset_id
    nx_graph: networkx.Graph = make_exploration_request(
        client=client,
        method='downstream',
        id=first_input_dataset
    )

    # check node count which should have been found
    input_dataset = 1
    activity = 1
    outputs = len(created_models[0].outputs)
    assert nx_graph.number_of_nodes() == input_dataset + activity + outputs

    # create a connected chain of records
    models: List[Tuple[ModelRunRecord, str]] = []
    prev: Optional[ModelRunRecord] = None

    for index in range(chain_size):
        id_postfix = 'chain' + str(index)
        id_override: Optional[str] = None

        # make the chain
        if prev:
            id_override = prev.outputs[0].dataset_id

        # create record
        new_record = generate_model_run_record(
            postfix=id_postfix,
            input_override=id_override
        )

        # override the seed mock to add unique
        # model run id
        # mock seed
        monkeypatch.setattr(
            register_workflow,
            'seed_model_run',
            id_fake_seed(seed_id_base + 'chain' + str(index))
        )

        monkeypatch.setattr(
            register_workflow,
            'validate_model_run_workflow_template',
            produce_mocked_validate_workflow(postfix=id_postfix)
        )

        # upload the fake model run record
        safe_serialisation = json.loads(new_record.json())
        response = client.post('/model_run/register_sync',
                               json=safe_serialisation)
        check_status_code(response)
        parsed_response: SyncRegisterModelRunResponse = SyncRegisterModelRunResponse.parse_obj(
            response.json())
        assert parsed_response.status.success
        assert parsed_response.record_info
        model_run_id: str = parsed_response.record_info.id

        # add to chain
        models.append((new_record, model_run_id))

        # update previous to enable chaining
        prev = new_record

    # get just chain
    model_chain: List[ModelRunRecord] = [model_and_id[0]
                                         for model_and_id in models]

    for index in range(chain_size):
        model: ModelRunRecord = models[index][0]
        model_run_record_id: str = models[index][1]

        for starting_position in ChainPosition:
            # work out correct count
            correct_count = calculate_downstream_node_cardinality(
                chain=model_chain,
                position_in_chain=index,
                position_in_record=starting_position
            )

            graph: networkx.Graph

            if starting_position == ChainPosition.CHAINED_INPUT:
                relevant_dataset = model.inputs[0].dataset_id

                # Make the query
                graph = make_exploration_request(
                    client=client,
                    method='downstream',
                    # override is always first in datasets
                    id=relevant_dataset
                )
            elif starting_position == ChainPosition.ACTIVITY:
                graph = make_exploration_request(
                    client=client,
                    method='downstream',
                    # start at activity
                    id=model_run_record_id
                )
            else:
                relevant_dataset = model.outputs[0].dataset_id
                graph = make_exploration_request(
                    client=client,
                    method='downstream',
                    # start at only output dataset
                    id=relevant_dataset
                )

            actual_count = graph.number_of_nodes()

            if index == chain_size - 1 and starting_position == ChainPosition.OUTPUT:
                # fetching downstream from output returns zero instead of
                # 1
                # TODO change this behaviour
                assert actual_count == 0
            else:
                assert actual_count == correct_count, f"Received graph with nodes: {actual_count} \
                    did not match expected count of {correct_count} for index {index} and chain\
                    position {starting_position.value}."
