import hashlib
from functools import cache
import os
from typing import List


def _dirhash(dirname: str) -> str:
    """Compute an MD5 hash of all non-hidden file contents in a directory tree."""
    hasher = hashlib.md5()
    for root, dirs, files in sorted(os.walk(dirname)):
        # skip hidden directories
        dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
        for fname in sorted(files):
            if fname.startswith('.'):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
    return hasher.hexdigest()


@cache
def hash_dir(dir: str) -> str:
    return _dirhash(os.path.abspath(dir))

def hash_dir_list(dirs: List[str]) -> str:
    return " ".join([hash_dir(
        os.path.abspath(dir)
    ) for dir in dirs])
