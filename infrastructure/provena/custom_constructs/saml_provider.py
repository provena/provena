
from aws_cdk import(
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct
from typing import Any


class KeycloakSAMLProvider(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 stage: str,
                 provider_name: str,
                 **kwargs: Any) -> None:
        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # work out the metadata path based on stage
        saml_metadata_path = f"provena/auth_metadata/xml_saml_descriptor/{stage}-SAML-Metadata-IDPSSODescriptor.xml"

        # Create the saml provider
        self.provider = iam.SamlProvider(
            scope=self,
            id="provider",
            name=provider_name,
            metadata_document=iam.SamlMetadataDocument.from_file(
                saml_metadata_path
            )
        )

        # Create some ARN outputs so updating keycloak is easier
        CfnOutput(self, "keycloak-provider-arn",
                  value=self.provider.saml_provider_arn)

    def add_role(self, role_name: str) -> iam.Role:
        # Create the role for the provider
        role = iam.Role(self, f"{role_name}-idprole",
                        assumed_by=iam.SamlConsolePrincipal(self.provider),
                        role_name=role_name)

        # The user needs to update permissions for this role outside
        # of this function - the role is returned and they may need to update
        # relationship on KeyCloak to include this arn/prov combination in the
        # client
        CfnOutput(self, f"{role_name}-role-arn",
                  value=role.role_arn)

        return role
