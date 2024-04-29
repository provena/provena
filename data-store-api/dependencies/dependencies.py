from ProvenaInterfaces.AuthAPI import ENTITY_REGISTRY_COMPONENT, SYS_ADMIN_COMPONENT, AccessLevel
from ProvenaInterfaces.AsyncJobModels import EmailSendEmailPayload
from KeycloakFastAPI.Dependencies import User, build_keycloak_auth, build_test_keycloak_auth
from config import base_config, Config, get_settings
from interfaces.EmailClient import EmailClient, EmailContent
from fastapi import Depends
from typing import List, Tuple
from helpers.job_api_helpers import submit_send_email_job

# Setup auth -> test mode means no sig enforcement on validation
kc_auth = build_keycloak_auth(
    keycloak_endpoint=base_config.keycloak_endpoint) if not base_config.test_mode else build_test_keycloak_auth()


auth_component = ENTITY_REGISTRY_COMPONENT

# Create dependencies
# This is from the shared authorisation model
read_usage_role = auth_component.get_role_at_level(
    AccessLevel.READ).role_name
write_usage_role = auth_component.get_role_at_level(
    AccessLevel.WRITE).role_name
admin_usage_role = auth_component.get_role_at_level(
    AccessLevel.ADMIN).role_name

user_general_dependency = kc_auth.get_user_dependency()
read_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role]
)
read_write_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role, write_usage_role]
)
admin_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role, write_usage_role, admin_usage_role]
)

sys_admin_auth_component = SYS_ADMIN_COMPONENT

# Create dependencies
# This is from the shared authorisation model
sys_admin_read_usage_role = sys_admin_auth_component.get_role_at_level(
    AccessLevel.READ).role_name
sys_admin_write_usage_role = sys_admin_auth_component.get_role_at_level(
    AccessLevel.WRITE).role_name
sys_admin_admin_usage_role = sys_admin_auth_component.get_role_at_level(
    AccessLevel.ADMIN).role_name

sys_admin_read_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [sys_admin_read_usage_role]
)
sys_admin_read_write_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [sys_admin_read_usage_role, sys_admin_write_usage_role]
)
sys_admin_admin_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [sys_admin_read_usage_role, sys_admin_write_usage_role, sys_admin_admin_usage_role]
)


def user_is_admin(user: User) -> bool:
    return admin_usage_role in user.roles


# EMAIL SETUP
class JobEmailClient(EmailClient):
    def __init__(self, config: Config) -> None:
        # Super constructor
        super().__init__()

        # Include config
        self.config = config

    async def send_email(self, reason: str, email_to: str, email_content: EmailContent) -> None:  # type: ignore
        await submit_send_email_job(
            # use service account username
            username=None,
            payload=EmailSendEmailPayload(
                email_to=email_to,
                subject=email_content.subject,
                body=email_content.body,
                reason=reason
            ),
            config=self.config
        )

    # type: ignore
    async def send_emails(self, reason: str, emails: List[Tuple[str, EmailContent]]) -> None:
        # TODO make this more efficient by caching service tokens between job
        # lodges
        for email_to, email_content in emails:
            await submit_send_email_job(
                # use service account username
                username=None,
                payload=EmailSendEmailPayload(
                    email_to=email_to,
                    subject=email_content.subject,
                    body=email_content.body,
                    reason=reason
                ),
                config=self.config
            )


# Build the email dependency using config
def email_dependency(config: Config = Depends(get_settings)) -> EmailClient:
    return JobEmailClient(config=config)
