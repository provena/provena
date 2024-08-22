from typing import List, Any
from custom_types import *
# github instance
from config import g, config
import github
from helpers.query_helpers import *
from rich import print

DEFAULT_LIMIT = 150


def list_prs(limit: int = DEFAULT_LIMIT) -> List[github.PullRequest.PullRequest]:
    print(f"Fetching up to {limit} PRs.")
    # get the repo
    repo = g.get_repo(config.repo_name)
    # get PRs on the repo
    prs = list(repo.get_pulls(state="all")[:DEFAULT_LIMIT])
    print(f"Completed fetch - retrieved {len(prs)} PRs.")

    return list(prs)


def parse_pr_info(pr: github.PullRequest.PullRequest) -> Optional[PRInfo]:
    # If the feat number cannot be found - returns None

    # work out the feature number from title
    ticket_num = find_ticket_number_pr(pr)

    if ticket_num is None:
        return None

    # get pr number
    pr_num = pr.number
    # status
    status: PRStatus = PRStatus.NONE
    if pr.merged:
        # this PR has been merged
        status = PRStatus.MERGED
    elif pr.closed_at:
        status = PRStatus.CLOSED_NOT_MERGED
    else:
        status = PRStatus.PENDING

    return PRInfo(pr_status=status, ticket_num=ticket_num, pr_num=pr_num)
