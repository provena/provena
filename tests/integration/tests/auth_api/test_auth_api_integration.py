from tests.helpers.auth_helpers import *
from tests.helpers.link_helpers import *
from tests.config import config, Tokens
from typing import Generator, Tuple
from tests.helpers.fixtures import *

test_group_id = "integration_test_group_id"


def test_groups(group_cleanup_fixture: Generator) -> None:
    # create group
    # add users
    # checked added
    # delete of group handled by fixture. Seperate test for removing group below

    group_metadata = {
        "id": test_group_id,
        "display_name": "integration_test_group",
        "description": "A test group for auth api integration tests",
    }

    cleanup_group_ids.append(test_group_id)
    add_group_resp = add_group_successfully(
        group_metadata=group_metadata, token=Tokens.admin())

    group_user = GroupUser(
        username=config.SYSTEM_WRITE_USERNAME,
        email="FakeEmail123@gmail.com",
        first_name="Bob",
        last_name="TheBuilder",
    )

    add_member_resp = add_member_to_group_successfully(
        user=group_user, group_id=test_group_id, token=Tokens.admin())

    # check user is added via check membership route
    assert user_is_member(username=group_user.username, group_id=test_group_id,
                          token=Tokens.admin()), "Failed to assert user is a member of group supposedly added to."

    # check user is added via group members list route
    members_list = get_group_membership_list(
        group_id=test_group_id, token=Tokens.admin())
    assert members_list.group, f"No group members returned despite member supposedly being added."

    assert group_user in members_list.group.users, "Failed to return group user was supposedly added to."

    # check user added by checking groups theyre in
    user_groups = get_user_groups(
        username=group_user.username, token=Tokens.admin())
    assert user_groups.groups, f"Failed to source user's groups despite supposedly adding them to a group earlier."
    assert test_group_id in [
        group.id for group in user_groups.groups], "Failed to return group user was supposedly added to."

    # try a remove member and check theyre removed
    remove_member_resp = remove_member_successfully(
        username=group_user.username, group_id=test_group_id, token=Tokens.admin())
    assert not user_is_member(username=group_user.username, group_id=test_group_id,
                              token=Tokens.admin()), "User is still in group despite being removed!"

    # try update group
    updated_group_metadata = group_metadata.copy()
    updated_group_metadata['display_name'] = updated_group_metadata['display_name'] + " Version 2.0"
    update_group_successfully(
        group_metadata=updated_group_metadata, token=Tokens.admin())

    # fetch group metadata using describe endpoint and ensure update happened
    describe_resp = describe_group(
        group_id=test_group_id, token=Tokens.admin())
    assert describe_resp.group, "Failed to return group metadata despite supposedly updating it earlier."
    assert describe_resp.group.display_name == updated_group_metadata[
        'display_name'], "Failed to update group display name."


def test_group_removal() -> None:
    # seperate test that doesnt call the cleanup which would fail since
    # this test is going to "clean itself up"

    group_metadata = {
        "id": test_group_id,
        "display_name": "integration_test_group",
        "description": "A test group for auth api integration tests",
    }
    add_group_resp = add_group_successfully(
        group_metadata=group_metadata, token=Tokens.admin())
    remove_group_resp = remove_group_successfully(
        id=test_group_id, token=Tokens.admin())


def test_user_lookup(two_person_fixture: Tuple[str, str], manual_link_test_cleanup: None) -> None:
    person_1_id, person_2_id = two_person_fixture

    # lookup with no entry (no username)
    lookup_user_user_assert_missing(token=Tokens.user1())

    # lookup with no entry (specify username)
    lookup_user_user_assert_missing(
        token=Tokens.user1(), username=Tokens.user1_username)

    # assign entry successfully
    assign_user_user_assert_success(
        token=Tokens.user1(), person_id=person_1_id)
    cleanup_links.append(Tokens.user1_username)

    # lookup with successful entry (no username)
    lookup_user_user_assert_success(token=Tokens.user1(), check_id=person_1_id)

    # lookup with successful entry (specify username)
    lookup_user_user_assert_success(
        token=Tokens.user1(), check_id=person_1_id, username=Tokens.user1_username)

    # make sure that user 2 fails from user 1

    # lookup with no entry (specify username)
    lookup_user_user_assert_missing(
        token=Tokens.user1(), username=Tokens.user2_username)

    # lookup with no entry (no username)
    lookup_user_user_assert_missing(token=Tokens.user2())

    # lookup with no entry (specify username)
    lookup_user_user_assert_missing(
        token=Tokens.user2(), username=Tokens.user2_username)

    # make sure user 2 can see user 1
    lookup_user_user_assert_success(
        token=Tokens.user2(), check_id=person_1_id, username=Tokens.user1_username)

    # assign entry successfully
    assign_user_user_assert_success(
        token=Tokens.user2(), person_id=person_2_id)
    cleanup_links.append(Tokens.user2_username)

    # lookup other username and ensure succeeds (no username)
    lookup_user_user_assert_success(token=Tokens.user2(), check_id=person_2_id)

    # lookup other username and ensure succeeds (specify username)
    lookup_user_user_assert_success(
        token=Tokens.user2(), check_id=person_2_id, username=Tokens.user2_username)


def test_user_assign(two_person_fixture: Tuple[str, str], manual_link_test_cleanup: None) -> None:
    person_1_id, _ = two_person_fixture
    # lookup with no entry
    lookup_user_user_assert_missing(token=Tokens.user1())

    # assign entry - empty string
    assign_user_user_assert_parse_error(
        token=Tokens.user1(), person_id="")

    # assign successfully
    assign_user_user_assert_success(
        token=Tokens.user1(), person_id=person_1_id)
    cleanup_links.append(Tokens.user1_username)

    # assign same payload - should fail
    assign_user_user_assert_fail(token=Tokens.user1(), person_id=person_1_id)

    # assign different payload - should fail
    new_id = person_1_id + "1"
    assign_user_user_assert_fail(token=Tokens.user1(), person_id=new_id)

    # lookup with successful entry (no username)
    lookup_user_user_assert_success(token=Tokens.user1(), check_id=person_1_id)


def test_admin_assign_and_clear(two_person_fixture: Tuple[str, str], manual_link_test_cleanup: None) -> None:
    person_1_id, person_2_id = two_person_fixture

    # lookup with no entry
    lookup_user_user_assert_missing(token=Tokens.user1())

    # assign entry - empty string

    # setup to clear username 1 and 2
    username_1 = Tokens.user1_username
    username_2 = Tokens.user2_username
    cleanup_links.extend([username_1, username_2])

    assign_user_admin_assert_parse_error(
        username=username_1, force=False, token=Tokens.admin(), person_id="")

    # assign successfully
    assign_user_admin_assert_success(
        username=username_1, force=False, token=Tokens.admin(), person_id=person_1_id)

    # assign same payload - should fail (force= False)
    assign_user_admin_assert_fail(
        username=username_1, force=False, token=Tokens.admin(), person_id=person_1_id)

    # assign same payload - should succeed (force= True)
    assign_user_admin_assert_success(
        username=username_1, force=True, token=Tokens.admin(), person_id=person_1_id)

    # assign new payload - should fail (force= False)
    assign_user_admin_assert_fail(
        username=username_1, force=False, token=Tokens.admin(), person_id=person_2_id)

    # assign new payload - should succeed (force= True)
    assign_user_admin_assert_success(
        username=username_1, force=True, token=Tokens.admin(), person_id=person_2_id)

    # now run on person 2 from person 1

    # lookup with no entry
    lookup_user_user_assert_missing(token=Tokens.user1(), username=username_2)

    # assign entry - empty string
    assign_user_admin_assert_parse_error(
        username=username_2, force=False, token=Tokens.admin(), person_id="")

    # assign successfully
    assign_user_admin_assert_success(
        username=username_2, force=False, token=Tokens.admin(), person_id=person_2_id)

    # assign same payload - should fail (force= False)
    assign_user_admin_assert_fail(
        username=username_2, force=False, token=Tokens.admin(), person_id=person_2_id)

    # assign same payload - should succeed (force= True)
    assign_user_admin_assert_success(
        username=username_2, force=True, token=Tokens.admin(), person_id=person_2_id)

    # assign new payload - should fail (force= False)
    assign_user_admin_assert_fail(
        username=username_2, force=False, token=Tokens.admin(), person_id=person_1_id)

    # assign new payload - should succeed (force= True)
    assign_user_admin_assert_success(
        username=username_2, force=True, token=Tokens.admin(), person_id=person_1_id)

    # now lookup from person 2
    lookup_user_user_assert_success(token=Tokens.user2(), check_id=person_1_id)

    # check back out to 'admin'

    # clear person 2 item
    clear_user_admin(token=Tokens.admin(), username=username_2)

    # go back to person 2

    # make sure gone
    lookup_user_user_assert_missing(token=Tokens.user2())


def test_reverse_lookup(two_person_fixture: Tuple[str, str], manual_link_test_cleanup: None) -> None:
    person_1_id, person_2_id = two_person_fixture

    usernames = [
        "1@gmail.com",
        "2@gmail.com",
        "3@gmail.com",
        "4@gmail.com",
    ]
    persons = [
        person_1_id,
        person_2_id,
    ]

    # setup to clear users
    cleanup_links.extend(usernames)

    # do reverse lookup with empty result
    reverse_lookup_assert_list(
        token=Tokens.admin(), person_id=persons[0], usernames=[])

    # do reverse lookup with single result
    # assign 0 -> 0
    assign_user_admin_assert_success(
        token=Tokens.admin(),
        username=usernames[0],
        person_id=persons[0],
        force=False
    )
    reverse_lookup_assert_list(
        token=Tokens.admin(), person_id=persons[0], usernames=usernames[:0])

    # do reverse lookup with multiple results
    # assign 1 -> 0
    assign_user_admin_assert_success(
        token=Tokens.admin(),
        username=usernames[1],
        person_id=persons[0],
        force=False
    )
    # assign 2 -> 0
    assign_user_admin_assert_success(
        token=Tokens.admin(),
        username=usernames[2],
        person_id=persons[0],
        force=False
    )
    reverse_lookup_assert_list(
        token=Tokens.admin(), person_id=persons[0], usernames=usernames[:2])

    # add other ids and make sure no change
    # assign 3 -> 1
    assign_user_admin_assert_success(
        token=Tokens.admin(),
        username=usernames[3],
        person_id=persons[1],
        force=False
    )
    # should be the same
    reverse_lookup_assert_list(
        token=Tokens.admin(), person_id=persons[0], usernames=usernames[:2])

    # remove relevant ids and make sure shrinks
    # clear 2
    clear_user_admin(token=Tokens.admin(), username=usernames[2])
    reverse_lookup_assert_list(
        token=Tokens.admin(), person_id=persons[0], usernames=usernames[:1])
    # clear 1
    clear_user_admin(token=Tokens.admin(), username=usernames[1])
    reverse_lookup_assert_list(
        token=Tokens.admin(), person_id=persons[0], usernames=usernames[:0])

    # clear completely and make sure empty
    # clear 0
    clear_user_admin(token=Tokens.admin(), username=usernames[0])
    reverse_lookup_assert_list(
        token=Tokens.admin(), person_id=persons[0], usernames=[])
