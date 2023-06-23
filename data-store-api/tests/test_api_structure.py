import tests.env_setup
from main import app
import re
import pytest
from typing import Set
from fastapi.routing import APIRoute

# Regex pattern for snake case sourced from
# https://gist.github.com/SuppieRK/a6fb471cf600271230c8c7e532bdae4b
snake_case_regex = r"[a-z0-9]+(?:_[a-z0-9]+)*"
snake_case_pattern = re.compile(snake_case_regex)


def test_operation_ids_present() -> None:
    # Ensures that all routes have a specified operation id
    # This guarantees that auto generated client libs will have
    # reasonable function names

    # app is imported from main and defines the full
    # structure of the api, including all routes
    for route in app.routes:
        if isinstance(route, APIRoute):
            assert route.operation_id, f"No operation id for route! Route {route.path}."


@pytest.mark.depends(on=['test_operation_ids_present'])
def test_operation_ids_unique() -> None:
    # Ensure that operation IDs are unique

    op_ids: Set[str] = set()
    for route in app.routes:
        if isinstance(route, APIRoute):
            assert route.operation_id, f"No operation id for route! Route {route.path}."
            assert route.operation_id not in op_ids, f"Operation id {route.operation_id} for {route.path} was not unique!"
            op_ids.add(route.operation_id)


def check_snake_case(input: str) -> bool:
    """Given a string input, will ensure the string 
    as a whole matches the snake case regex supplied
    at the top of this file.

    Parameters
    ----------
    input : str
        The input string to test

    Returns
    -------
    bool
        Is the string valid snake case?
    """
    matches = snake_case_pattern.fullmatch(input)
    return bool(matches)


def test_snake_case_checker() -> None:
    assert check_snake_case("this_is_snake_case")
    assert check_snake_case("so_is_this_and_this")
    assert check_snake_case("thisalsois")
    assert not check_snake_case("this_Isnt")
    assert not check_snake_case("neither Is_this")
    assert not check_snake_case("NeitherIsThis")
    assert not check_snake_case("Neither_Is_This")
    assert not check_snake_case("neither_ is_this")


@pytest.mark.depends(on=['test_operation_ids_present', 'test_snake_case_checker'])
def test_operation_ids_snake_case() -> None:
    # Ensure that operation IDs are snake case

    for route in app.routes:
        if isinstance(route, APIRoute):
            assert route.operation_id, f"No operation id for route! Route {route.path}."
            assert check_snake_case(
                route.operation_id), f"Operation ID {route.operation_id} for route {route.path} is not valid snake case."
