import checksumdir
from functools import cache
import os

# wrap the checksumdir function in a cache to avoid repeatedly walking the same
# path


@cache
def hash_dir(dir: str) -> str:
    return checksumdir.dirhash(
        dirname=os.path.abspath(dir),
        hashfunc='md5',
        ignore_hidden=True)
