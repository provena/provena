import checksumdir
from functools import cache
import os
from typing import List

# wrap the checksumdir function in a cache to avoid repeatedly walking the same
# path


@cache
def hash_dir(dir: str) -> str:
    return checksumdir.dirhash(
        dirname=os.path.abspath(dir),
        hashfunc='md5',
        ignore_hidden=True)

def hash_dir_list(dirs: List[str]) -> str:
    return " ".join([hash_dir(
        os.path.abspath(dir)
    ) for dir in dirs])
