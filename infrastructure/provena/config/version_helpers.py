import os
from typing import Optional

def get_commit_id_from_env() -> Optional[str]:
    """
    Get the git commit ID from the environment.
    """
    commit_id = os.getenv("GIT_COMMIT_ID")
    return commit_id

def get_commit_url_from_env() -> Optional[str]:
    """
    Get the git commit URL from the environment.
    """
    commit_url = os.getenv("GIT_COMMIT_URL")
    return commit_url

def get_tag_name_from_env() -> Optional[str]:
    """
    Get the git tag name from the environment.
    """
    tag_name = os.getenv("GIT_TAG_NAME")
    return tag_name

def get_release_title_from_env() -> Optional[str]:
    """
    Get the release title from the environment.
    """
    release_title = os.getenv("GIT_RELEASE_TITLE")
    return release_title

def get_release_url_from_env() -> Optional[str]:
    """
    Get the release URL from the environment.
    """
    release_url = os.getenv("GIT_RELEASE_URL")
    return release_url