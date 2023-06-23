
from aws_cdk import(
    aws_iam as iam,
    CfnOutput,
    Duration
)
from constructs import Construct, IDependable

from typing import List, Any, Optional


class KeycloakOIDCProvider(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 entity_id_url_qualified: str,
                 entity_id_url_unqualified: str,
                 client_ids: List[str],
                 await_dependency: IDependable,
                 **kwargs: Any) -> None:
        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # Create the saml provider
        self.provider = iam.OpenIdConnectProvider(
            self, construct_id + "oidc_provider",
            url=entity_id_url_qualified,
            client_ids=client_ids
        )

        # Don't try and produce the provider until the
        # record is ready and the URL is resolvable
        self.provider.node.add_dependency(await_dependency)

        # Remember entity id
        self.entity_id = entity_id_url_unqualified

    def add_role(self, id: str, client_id: str, role_name: Optional[str] = None, max_session_duration: Optional[Duration] = Duration.hours(1)) -> iam.Role:
        # Create the role for the provider
        role = iam.Role(self, id,
                        assumed_by=iam.OpenIdConnectPrincipal(
                            self.provider,
                            # Ensure the client id matches
                            conditions={
                                "StringEquals": {
                                    f"{self.entity_id}:aud": client_id
                                }}),
                            role_name=role_name,
                            max_session_duration=max_session_duration
                        )
        return role
