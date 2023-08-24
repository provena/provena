from tests.helpers.registry_helpers import *
from tests.helpers.datastore_helpers import *
from tests.helpers.prov_helpers import *
from tests.helpers.link_helpers import *
from resources.example_models import *
from tests.config import config, Tokens
from tests.helpers.fixtures import *
import pytest  # type: ignore
from typing import Generator, cast
from tests.helpers.auth_helpers import perform_group_cleanup
from tests.helpers.async_job_helpers import *
from tests.helpers.shared_lists import *


@pytest.fixture(scope='session', autouse=False)
def person_fixture() -> Generator[ItemPerson, None, None]:
    # create person 1 and 2  (user 1 and 2)
    person = create_item_successfully(
        item_subtype=ItemSubType.PERSON,
        token=Tokens.user1()
    )

    # provide to any test that uses them
    yield cast(ItemPerson, person)

    # clean up
    perform_entity_cleanup([
        (person.item_subtype, person.id),
    ], token=Tokens.admin())

# Only run this at the module scope - this is used for the auth api tests
# because they rely on having non setup links


@pytest.fixture(scope='module', autouse=False)
def manual_link_test_cleanup(person_fixture: ItemPerson) -> Generator[None, None, None]:
    # Retain current state of links
    # Delete links
    perform_link_cleanup([
        Tokens.user1_username,
        Tokens.user2_username,
        Tokens.admin_username,
    ], token=Tokens.admin())
    yield
    person = person_fixture

    # link this person to person1, person2 and admin - need to perform as admin
    # to overcome ownership issue
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.user1_username, force=True)
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.user2_username, force=True)
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.admin_username, force=True)


@pytest.fixture(scope='session', autouse=True)
def linked_person_fixture(person_fixture: ItemPerson) -> Generator[ItemPerson, None, None]:
    person = person_fixture

    # link this person to person1, person2 and admin - need to perform as admin
    # to overcome ownership issue
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.user1_username, force=True)
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.user2_username, force=True)
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.admin_username, force=True)

    # provide to any test that uses them
    yield person

    # clean up links
    perform_link_cleanup([
        Tokens.user1_username,
        Tokens.user2_username,
        Tokens.admin_username,
    ], token=Tokens.admin())


@pytest.fixture(scope='session', autouse=False)
def organisation_fixture() -> Generator[ItemOrganisation, None, None]:
    # create person 1 and 2  (user 1 and 2)
    org = create_item_successfully(
        item_subtype=ItemSubType.ORGANISATION,
        token=Tokens.user1()
    )

    # provide to any test that uses them
    yield cast(ItemOrganisation, org)

    # clean up
    perform_entity_cleanup([
        (org.item_subtype, org.id),
    ], token=Tokens.admin())


@pytest.fixture(scope='session', autouse=True)
def two_person_fixture() -> Generator[Tuple[str, str], None, None]:
    # create person 1 and 2  (user 1 and 2)
    person_1 = create_item_successfully(
        item_subtype=ItemSubType.PERSON,
        token=Tokens.user1()
    )
    person_1_id = person_1.id

    person_2 = create_item_successfully(
        item_subtype=ItemSubType.PERSON,
        token=Tokens.user2()
    )
    person_2_id = person_2.id

    # provide to any test that uses them
    yield (person_1_id, person_2_id)

    # clean up
    perform_entity_cleanup([
        (person_1.item_subtype, person_1.id),
        (person_2.item_subtype, person_2.id),
    ], token=Tokens.admin())


@pytest.fixture(scope='function', autouse=True)
def link_cleanup_fixture() -> Generator:
    # runs after each function to clean up any links created
    # function scope required because tests depend on fresh start with no links
    yield
    perform_link_cleanup(cleanup_links, token=Tokens.admin())


@pytest.fixture(scope='function', autouse=False)
def group_cleanup_fixture() -> Generator:
    # start up code here:
    yield
    # clean up code here:
    perform_group_cleanup(
        cleanup_group_ids=cleanup_group_ids, token=Tokens.admin())

# fixture to clean up items


@pytest.fixture(scope='session', autouse=True)
def entity_cleanup_fixture() -> Generator:
    yield
    if config.LEAVE_ITEMS_FOR_INITIALISATION:
        print('Skipping entity cleanup for workflow tests - Leaving Items for intialisation of deployment.')
    else:
        print("Performing entity cleanup in workflow tests.")
        perform_entity_cleanup(cleanup_items, token=Tokens.admin())


@pytest.fixture(scope='session', autouse=False)
def dataset_io_fixture(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> Generator[Tuple[str, str], None, None]:
    # pull out prebuilt references from the fixture
    person = linked_person_fixture
    organisation = organisation_fixture

    # models to test
    cf_1 = valid_collection_format1
    cf_2 = valid_collection_format2

    # create person 1 and 2
    datasets = cast(Tuple[MintResponse, MintResponse], (
        mint_basic_dataset_successfully(
            token=Tokens.user1(),
            author_organisation_id=organisation.id,
            publisher_organisation_id=organisation.id,
            model=DatasetDomainInfo(
                collection_format=cf_1,
                display_name=cf_1.dataset_info.name,
                s3=S3Location(
                    bucket_name="", path="", s3_uri="")
            )
        ),
        mint_basic_dataset_successfully(
            token=Tokens.user1(),
            author_organisation_id=organisation.id,
            publisher_organisation_id=organisation.id,
            model=DatasetDomainInfo(
                collection_format=cf_2,
                display_name=cf_2.dataset_info.name,
                s3=S3Location(
                    bucket_name="", path="", s3_uri="")
            )


        )))

    dataset_ids = cast(
        Tuple[str, str], (datasets[0].handle, datasets[1].handle))
    cleanup_items.extend([
        (ItemSubType.DATASET, dataset_ids[0]),
        (ItemSubType.DATASET, dataset_ids[1]),
    ])

    # Await completion of CreateActivity lodge to clean these up too
    for ds in list(datasets):
        cleanup_create_activity_from_dataset_mint(
            mint_response=ds,
            get_token=Tokens.user1
        )

    # provide to any test that uses them
    yield dataset_ids
