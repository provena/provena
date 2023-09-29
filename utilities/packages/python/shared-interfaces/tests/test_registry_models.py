from SharedInterfaces.RegistryModels import *
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