import re
from typing import Optional, Dict, Any, Tuple
import github
from custom_types import *
from config import config



def find_ticket_number_pr(pr: github.PullRequest.PullRequest) -> Optional[int]:
    # Try searching the title for target regex 
    title = pr.title

    match = re.search(config.ticket_pattern, title)
    if match:
        return int(match.group(1))

    # Try searching the description for feat -  ticket num

    # get the first comment
    description: str = str(pr.body)

    match = re.search(config.feat_md_pattern, description)
    if match:
        return int(match.group(1))

    # couldn't find any match
    return None


def find_ticket_number_and_type_stack(stack: Dict[str, Any]) -> Optional[Tuple[StackType, int]]:
    # look for the pipeline/deploy stack
    stack_name = stack['StackName']
    
    # try using the pipeline pattern 
    match = re.search(config.pipeline_stack_pattern, stack_name)
    if match:
        return (StackType.PIPELINE, int(match.group(1)))
    
    # try using the app pattern 
    match = re.search(config.deploy_stack_pattern, stack_name)
    if match:
        return (StackType.APP, int(match.group(1)))
    
    # couldn't find any match
    return None
