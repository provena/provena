from typing import Dict
from config import *
import typer
from github import Github, Auth, Tag
#import os
from config import base_config

app = typer.Typer()


@app.command()
def get_version_info(
        repo_string: str = typer.Argument(...,
            help="The repo string (owner/name) of the repo to get the version info for."
        ),
        git_commit_id: str = typer.Argument(...,
            help="The git commit id to get the version info for."
        ),
        export: bool = typer.Option(False, "--export", "-e",
            help="Whether to expose the version info to a file."
        ),

)-> None:
    """
    Get version information for a repo and commit ID. If anything is not available, it will be set to N/A.

    USAGE: python get_version_info.py get_version_info "owner/name" "commit_id" --export


    Parameters
    ----------
    repo_string : str, optional
        _description_, by default typer.Argument(..., help="The repo string (owner/name) of the repo to get the version info for." )
    git_commit_id : str, optional
        _description_, by default typer.Argument(..., help="The git commit id to get the version info for." )
    export : bool, optional
        _description_, by default typer.Option(False, "--export", "-e", help="Whether to expose the version info to a file." )
    """

    auth = Auth.Token(base_config.github_oauth_token)
    g = Github(auth=auth)

    version_info: Dict[str, str] = {}

    # https://pygithub.readthedocs.io/en/stable/apis.html

    try: # source the repo
        repo = g.get_repo(f"{repo_string}")
    except Exception as e:
        print(f"Error: unable to get repo. Details {e}")
        return

    try: # get commit URL from commit ID
        commit = repo.get_commit(git_commit_id)
        version_info["commit_url"] = commit.commit.html_url
    except Exception as e:
        print(f"Error: unable to get commit URL. Details {e}")

    try: # get tags in repo
        tags = repo.get_tags()
    except Exception as e:
        print(f"Error: unable to get tags. Details: {e}")

    try:
        if tags.totalCount > 0:
            for tag in tags:
                if tag.commit.sha == git_commit_id:
                    version_info["tag_name"] = tag.name
                    break

            if 'tag_name' not in version_info:
                print(f"Error: commit ID {git_commit_id} is not tagged.")
    except Exception as e:
        print(f"Error: unable to get tags associated with commit repo tags. Details: {e}")
    try:
        if 'tag_name' in version_info:
        # try get release associated with tag

            release = repo.get_release(version_info['tag_name'])
            if release:
                version_info["release_title"] = release.title
                version_info["release_url"] = release.html_url
        else:
            print("Error: No tag was found, so no release was either.")
    except Exception as e:
        print(f"Error: unable to get release from tag. Details: {e}")

    print("--------- Printing obtained version information ---------")
    for k,v in version_info.items():
        print(f"{k}: {v}")

    if export:
        # write version_info to json file
        print("Writing version info to file.")
        import json
        with open("version_info.json", "w") as f:
            json.dump(version_info, f)

if __name__ == "__main__":
        app()