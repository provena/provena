from datetime import datetime
from random import randint
def get_timestamp() -> int:
    return int(datetime.now().timestamp())
