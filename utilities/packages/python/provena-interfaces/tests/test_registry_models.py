from ProvenaInterfaces.RegistryModels import *
from tests.helpers.helpers import *
from ProvenaInterfaces.TestConfig import route_params, RouteParameters
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
    dataset: DatasetDomainInfo = get_model_example(
        item_subtype=ItemSubType.DATASET)
    assert dataset.access_info_uri == None  # check the same for the None case
    assert dataset.access_info_uri == dataset.collection_format.dataset_info.access_info.uri

    dataset.access_info_uri = "https://example.com"
    dataset.collection_format.dataset_info.access_info.uri = "https://example.com"
    dataset.collection_format.dataset_info.access_info.reposited = False
    dataset.collection_format.dataset_info.access_info.description = 'Test'
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


# Test for PublicationDate
def test_publication_date_validation():
    # Test case where relevant is True and a date is provided
    pub_date = PublishedDate(relevant=True, value=date(2020, 1, 1))
    assert pub_date.value == date(2020, 1, 1)

    # Test case where relevant is True but no date is provided
    with pytest.raises(ValueError) as excinfo:
        PublishedDate(relevant=True)
    assert "Must provide a date if the relevant field is set to True" in str(
        excinfo.value)

    # Test case where relevant is False and no date is provided
    pub_date = PublishedDate(relevant=False)
    assert pub_date.value is None

    # Test case where relevant is False but a date is provided
    with pytest.raises(ValueError) as excinfo:
        PublishedDate(relevant=False, value=date(2020, 1, 1))
    assert "Cannot provide a date if the relevant field is set to False" in str(
        excinfo.value)

# Test for CreatedDate


def test_creation_date_validation():
    # Test case where relevant is True and a date is provided
    creation_date = CreatedDate(relevant=True, value=date(2020, 1, 1))
    assert creation_date.value == date(2020, 1, 1)

    # Test case where relevant is True but no date is provided
    with pytest.raises(ValueError) as excinfo:
        CreatedDate(relevant=True)
    assert "Must provide a date if the relevant field is set to True" in str(
        excinfo.value)

    # Test case where relevant is False and no date is provided
    creation_date = CreatedDate(relevant=False)
    assert creation_date.value is None

    # Test case where relevant is False but a date is provided
    with pytest.raises(ValueError) as excinfo:
        CreatedDate(relevant=False, value=date(2020, 1, 1))
    assert "Cannot provide a date if the relevant field is set to False" in str(
        excinfo.value)
