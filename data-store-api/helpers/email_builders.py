from interfaces.EmailClient import EmailContent
from ProvenaInterfaces.RegistryModels import ReleaseAction
from config import HDL_PREFIX


def build_review_request_email(
    dataset_id: str,
    requester_id: str,
    dataset_url: str,
    reason: str
) -> EmailContent:
    subject = f"Provena Dataset release review request {dataset_id} by person {requester_id}"
    body = f"""
    This email is to inform you of a request made by another user ({HDL_PREFIX}{requester_id}) to review their dataset.
    
    The ID of the dataset is {dataset_id}.
    
    You can view the dataset at this URL: {dataset_url}

    The requester specified the following notes for this review: 
    \"{reason}\"
    """

    return EmailContent(
        subject=subject,
        body=body
    )


def build_review_actioned_email(
    dataset_id: str,
    reviewer_id: str,
    dataset_url: str,
    action: ReleaseAction,
    notes: str
) -> EmailContent:
    # TODO improve email content
    subject = f"Provena Dataset release review actioned id: {dataset_id} action: {action.value}"
    body = f"""
    This email is to inform you of an update in the dataset release process for id {dataset_id}.
    
    The reviewer ({HDL_PREFIX}{reviewer_id}) took the following action: {action.value}.
    
    You can view the dataset at this URL: {dataset_url}

    The reviewer included the following notes for this review: 
    \"{notes}\"
    """

    return EmailContent(
        subject=subject,
        body=body
    )
