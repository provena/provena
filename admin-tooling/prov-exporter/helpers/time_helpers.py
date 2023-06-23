from datetime import datetime
from pytz import timezone, common_timezones
from helpers.generator_types import Timezone

RECOMMENDED_TIMEZONES = list(
    filter(lambda x: x.startswith('Australia'), common_timezones))


def validate_timezone(tz: Timezone) -> None:
    # throws an error if timezone is invalid
    try:
        zone = timezone(tz)
    except Exception as e:
        raise ValueError(
            f"Timezone {tz} was invalid. Recommended: {', '.join(RECOMMENDED_TIMEZONES)}.")


def timestamp_to_string(timestamp: int, desired_tz: Timezone) -> str:
    # Convert Unix timestamp to datetime object
    dt = datetime.fromtimestamp(timestamp)
    # Get the desired timezone
    try:
        tz = timezone(desired_tz)
    except Exception as e:
        raise ValueError(f"Timezone {desired_tz} was invalid.")
    # Convert datetime object to timezone
    aedt_dt = tz.localize(dt)
    # Format datetime string as desired
    formatted_str = aedt_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    return formatted_str
