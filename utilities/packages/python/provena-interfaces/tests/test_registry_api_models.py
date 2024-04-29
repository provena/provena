from ProvenaInterfaces.RegistryAPI import *
import pytest

# Ignore mypy errors as we are testing invalid models here and mypy
# doesn't know to look up and see "with self.assertRaises(ValueError):"
# The correct models will still fail if they aren't actually correct in the success case test
# mypy: ignore-errors


import pytest
from ProvenaInterfaces.RegistryAPI import SortOptions, SortType

def test_sort_options() -> None:
    # Test that begins_with can be used with valid sort types
    sort_options = SortOptions(sort_type=SortType.ACCESS_INFO_URI_BEGINS_WITH, begins_with="https://example.com")
    assert sort_options.sort_type == SortType.ACCESS_INFO_URI_BEGINS_WITH
    assert sort_options.begins_with == "https://example.com"

    # Test that begins_with cannot be used without specifying sort_type
    with pytest.raises(ValueError):
        SortOptions(begins_with="https://example.com")

    # Test that begins_with cannot be omitted when sort_type is ACCESS_INFO_URI_BEGINS_WITH
    with pytest.raises(ValueError):
        SortOptions(sort_type=SortType.ACCESS_INFO_URI_BEGINS_WITH)

    # Test that begins_with cannot be used with sort_type not in _valid_begins_with_sort_types
    with pytest.raises(ValueError):
        SortOptions(sort_type=SortType.CREATED_TIME, begins_with="https://example.com")