from typing import List, Dict, Any, cast
from custom_types import *
from helpers.aws_helpers import *
from helpers.github_helpers import *
from helpers.query_helpers import *



def get_status_infos() -> Dict[int, TotalStatus]:
    # Two sources of relevant information

    # 1) Github pull requests
    # 2) AWS Cloudformation stacks

    # demo list of PRS
    prs = list_prs()

    # get the status of the PRs - NOTE this only includes PR which have target ticket regex
    pr_infos = cast(List[PRInfo], list(
        filter(lambda x: x is not None, map(parse_pr_info, prs))))

    pr_info_dict: Dict[int, PRInfo] = {}
    for pr in pr_infos:
        ticket = pr.ticket_num
        if ticket in pr_info_dict:
            print(
                f"Warning: found two PRs which target the ticket {ticket}. Using latest.")
        else:
            pr_info_dict[ticket] = pr

    # get the list of current cloudformation stacks
    stacks = list_cfn_stacks()

    # parse stack info
    app_stack_infos: Dict[int, StackInfo] = {}
    pipeline_stack_infos: Dict[int, StackInfo] = {}
    for stack in stacks:
        type_num = find_ticket_number_and_type_stack(stack)
        if type_num is not None:
            type, num = type_num
            info = parse_stack_info(
                ticket_num=num,
                stack_type=type,
                stack_data=stack
            )
            if type == StackType.APP:
                app_stack_infos[num] = info
            if type == StackType.PIPELINE:
                pipeline_stack_infos[num] = info

    # merge stack and PR states
    statuses: Dict[int, TotalStatus] = {}

    all_tickets = set(pr_info_dict.keys()).union(
        set(app_stack_infos.keys()).union(pipeline_stack_infos.keys())
    )

    for ticket in all_tickets:
        # pull out various infos and combine
        pr_info = pr_info_dict.get(ticket)
        app_info = app_stack_infos.get(ticket)
        pipeline_info = pipeline_stack_infos.get(ticket)
        statuses[ticket] = TotalStatus(
            ticket_num=ticket,
            pr_status=pr_info,
            app_stack=app_info,
            pipeline_stack=pipeline_info
        )

    return statuses


def is_stale(status: TotalStatus) -> bool:
    # stale is defined as a feature branch with a MERGED PR with a deployment

    # is there a PR?
    if status.pr_status is None:
        return False

    # is PR merged?
    merged = is_merged(status.pr_status)

    if not merged:
        return False

    # non merged PR - is there deployments?
    return status.app_stack is not None or status.pipeline_stack is not None


def is_merged(pr_info: PRInfo) -> bool:
    return pr_info.pr_status == PRStatus.MERGED