from config import Config
from SharedInterfaces.AuthAPI import *
from KeycloakFastAPI.Dependencies import *
from dataclasses import dataclass 

@dataclass
class EmailContent():
    subject: str
    body: str

def generate_email_text_from_diff(difference_report: AccessReport, user: User, request_entry: RequestAccessTableItem, config: Config) -> EmailContent:
    """    generate_email_text_from_diff
        Given the difference access report will generate a formatted email string
        which describes the changes in access required to the sys admin

        Arguments
        ----------
        difference_report : AccessReport
            The difference in access required

        user: User
            The user information

        request_entry: RequestAccessTableItem
            The table entry to enable linking to 
            id and other request info

        Returns
        -------
         : str
            The email string 

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    header = f"Access request username: {user.username} id: {request_entry.request_id}"
    body = f"""Request for access change for username: {user.username} request_id: {request_entry.request_id}.
    Request made on auth server: {config.keycloak_endpoint} (stage: {config.stage})
    Admin console: {config.admin_console_endpoint}
    Changes required:
    """

    component_list = []
    for component in difference_report.components:
        component_string_rows = []
        for role in component.component_roles:
            component_string_rows.append(
                f"Role name: {role.role_name}, desired access: {'Granted' if role.access_granted else 'Denied'}")
        component_list.append(
            f"Component: {component.component_name}\n" + '\n'.join(component_string_rows))
    component_body = '\n'.join(component_list)
    full_body = body + "\n" + component_body
    
    return EmailContent(
        subject=header,
        body=full_body
    )

def generate_report_from_user(user: User) -> AccessReport:
    """    generate_report_from_user
        Generate an access report from user (token)

        Arguments
        ----------
        user : User
            The user which includes role list

        Returns
        -------
         : AccessReport
            The AccessReport

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # We know that the token is valid, and therefore we can pull roles
    roles = user.roles

    # Generate the report based on the knowledge map
    components: Dict[str, ReportAuthorisationComponent] = {}

    for authorisation_component in AUTHORISATION_MODEL.components:
        component_name = authorisation_component.component_name
        for component_role in authorisation_component.component_roles:
            role_name = component_role.role_name
            role = ReportComponentRole(
                **component_role.dict(),
                access_granted=False,
            )
            if role_name in roles:
                role.access_granted = True

            # Create if it doesn't exist in map
            access_component = components.get(
                component_name, ReportAuthorisationComponent(component_name=component_name, component_roles=[]))
            access_component.component_roles.append(role)
            # update the mapping
            components[component_name] = access_component

    return AccessReport(components=list(components.values()))


def find_access_report_changes(existing_access: AccessReport, desired_access: AccessReport) -> AccessReport:
    """    find_access_report_changes
        Given the existing access and desired access reports, will return an access report
        which only includes components which have at least one change in access. Components
        which have a change in access will only include roles which have changed access. 

        I.e. every item in this access report is 'changed' from the previous access.

        Arguments
        ----------
        existing_access : AccessReport
            The existing access from the token
        desired_access : AccessReport
            The desired access from the request

        Returns
        -------
         : AccessReport
            The access difference (every element is different)

        Raises
        ------
        Exception
            Raises an exception if a role in the desired access doesn't exist in existing access
        Exception
            Raises an exception if a component in the desired access doesn't exist in existing access

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    diff_components = []
    for desired_component in desired_access.components:
        # Mark the name of the component
        component_name = desired_component.component_name

        # Try and find the component in existing access report
        found = False
        existing_component = None
        for comp in existing_access.components:
            if comp.component_name == component_name:
                found = True
                existing_component = comp
                break
        # If failed, return an exception
        if not found:
            raise Exception(
                f'Component {component_name} is in desired access but is not a valid component.')

        # establish existing component as not none for mypy
        assert existing_component

        changed_roles = []
        # We have a component to compare
        for desired_role in desired_component.component_roles:
            desired_role_name = desired_role.role_name

            # Try and find the role name in the existing access report
            found = False
            existing_role = None

            for role in existing_component.component_roles:
                if role.role_name == desired_role_name:
                    found = True
                    existing_role = role
                    break

            # couldn't find a matching role name
            # throw exception
            if not found:
                raise Exception(
                    f'Role name {desired_role_name} in component {desired_component} does not exist.')

            # establish existing component as not none for mypy
            assert existing_role

            if existing_role.access_granted != desired_role.access_granted:
                # Since the roles have different access, add to the roles
                changed_roles.append(desired_role)

        # only add component if there is at least one different role access level
        if len(changed_roles) > 0:
            diff_components.append(
                ReportAuthorisationComponent(
                    component_name=component_name,
                    component_roles=changed_roles
                )
            )

    # Produce the access report from the components which differ, could be an empty list if no differences
    return AccessReport(components=diff_components)
