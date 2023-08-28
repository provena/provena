from datetime import datetime


def get_timestamp() -> int:
    return int(datetime.now().timestamp())
