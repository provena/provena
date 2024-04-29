from ProvenaInterfaces.RegistryModels import *
from tests.helpers.helpers import *
from ProvenaSharedFunctionality.Registry.TestConfig import route_params, RouteParameters
import pytest
# Ignore mypy errors as we are testing invalid models here and mypy
# doesn't know to look up and see "with self.assertRaises(ValueError):"
# The correct models will still fail if they aren't actually correct in the success case test
# mypy: ignore-errors


def test_spatial_info() -> None:
    spatial_info = CollectionFormatSpatialInfo(resolution="1.23")
    # With validation error:
    with pytest.raises(ValueError):
        spatial_info = CollectionFormatSpatialInfo(resolution="1.23abcd")
        
def test_temporal_info() -> None:
    # Test success cases
    temporal_info = CollectionFormatTemporalInfo(
        duration=TemporalDurationInfo(
            begin_date="2019-01-01",
            end_date="2019-01-02"
        ),
        resolution="P1Y2M10DT2H30M"
    )

    # ensure failure with missing begin or end date
    with pytest.raises(ValueError):
        temporal_info = CollectionFormatTemporalInfo(
            duration=TemporalDurationInfo(
                begin_date="2019-01-01"
            ),
            resolution="P1Y2M10DT2H30M"
        )

    with pytest.raises(ValueError):
        temporal_info = CollectionFormatTemporalInfo(
            duration=TemporalDurationInfo(
                end_date="2019-01-01"
            ),
            resolution="P1Y2M10DT2H30M"
        )

    # ensure failure with invalid resolution
    with pytest.raises(ValueError):
        temporal_info = CollectionFormatTemporalInfo(
            duration=TemporalDurationInfo(
                begin_date="2019-01-01",
                end_date="2019-01-02"
            ),
            resolution="P1Y2M10DT2H30Mabcd"
        )
    
    # ensure failure with invalid order of start and end date
    with pytest.raises(ValueError):
        temporal_info = CollectionFormatTemporalInfo(
            duration=TemporalDurationInfo(
                begin_date="2019-01-02",
                end_date="2019-01-01"
            ),
            resolution="P1Y2M10DT2H30M"
        )

    # ensure success with None for temporal resolution
    temporal_info = CollectionFormatTemporalInfo(
        duration=TemporalDurationInfo(
            begin_date="2019-01-01",
            end_date="2019-01-02"
        ),
        resolution=None
    )


def test_dataset_access_info_uri_set() -> None:
    # Test that access_info_uri is set correctly
    dataset: DatasetDomainInfo = get_model_example(item_subtype=ItemSubType.DATASET)
    assert dataset.access_info_uri == None # check the same for the None case
    assert dataset.access_info_uri == dataset.collection_format.dataset_info.access_info.uri
    
    dataset.access_info_uri="https://example.com"
    dataset.collection_format.dataset_info.access_info.uri="https://example.com"
    dataset.collection_format.dataset_info.access_info.reposited=False
    dataset.collection_format.dataset_info.access_info.description='Test'
    # re parse to run validators
    dataset = DatasetDomainInfo.parse_obj(dataset.dict())


    # Test that ValueError is raised when access_info_uri is not set
    dataset.access_info_uri = None
    assert dataset.collection_format.dataset_info.access_info.uri
    with pytest.raises(ValueError):
        dataset = DatasetDomainInfo.parse_obj(dataset.dict())
    
    # Test if dataset.access_info_uri is set but collection_format.dataset_info.access_info.uri is not
    with pytest.raises(ValueError):
        dataset.access_info_uri = "https://example.com"
        dataset.collection_format.dataset_info.access_info.uri = None
        dataset = DatasetDomainInfo.parse_obj(dataset.dict())

    # Test that ValueError is raised when access_info_uri does not match collection_format.access_info.uri
    with pytest.raises(ValueError):
        dataset.collection_format.dataset_info.access_info.uri = dataset.access_info_uri + "/abcd"
        dataset = DatasetDomainInfo.parse_obj(dataset.dict())