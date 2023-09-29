import { Alert, AlertTitle } from "@mui/material";
import { useUserLinkServiceLookup } from "./useUserLinkServiceLookup";
import {
    DOCUMENTATION_BASE_URL,
    LANDING_PAGE_LINK,
} from "../queries/endpoints";

export const userLinkEnforcerDocumentationLink =
    DOCUMENTATION_BASE_URL + "/getting-started-is/linking-identity.html";
export const userLinkEnforcerProfileLink =
    LANDING_PAGE_LINK + "/profile?function=identity";

const defaultMissingLinkMessage = (
    <p>
        You cannot perform this operation without linking your user account to a
        registered Person in the Registry. For more information, visit{" "}
        <a
            href={userLinkEnforcerDocumentationLink}
            target="_blank"
            rel="noreferrer"
        >
            our documentation
        </a>
        . You can link your user account to a Person by visiting your{" "}
        <a href={userLinkEnforcerProfileLink} target="_blank" rel="noreferrer">
            user profile
        </a>
        .
    </p>
);
const defaultMissingLinkTitle =
    "This operation is not permitted without linking your account to a Person in the Registry";

export interface UseUserLinkEnforcerProps {
    blockEnabled: boolean;
    blockOnError: boolean;

    // override default message/title
    missingLinkMessage?: JSX.Element;
    missingLinkTitle?: JSX.Element;
}
export interface UseUserLinkEnforcerOutput {
    blocked: boolean;
    render: JSX.Element | null;

    // T/F once loaded, undefined otherwise or in error case
    validLink: boolean | undefined;
}
export const useUserLinkEnforcer = (
    props: UseUserLinkEnforcerProps
): UseUserLinkEnforcerOutput => {
    /**
    Hook: useUserLinkEnforcer

    Handles three things
    1) Fetches the users link status
    2) Returns whether the action should be blocked
    3) Returns a render function which shows an error alert where blocking is
       specified
    */

    // Need to check user is linked as above
    const link = useUserLinkServiceLookup({});
    const validLink = !link.loading && !link.error ? !!link.data : undefined;
    const missingLink = !link.loading && !link.data;
    const error = link.error;

    var render: JSX.Element | null = null;

    if (missingLink) {
        render = (
            <Alert variant="outlined" severity="warning">
                <AlertTitle>
                    {props.missingLinkTitle ?? defaultMissingLinkTitle}
                </AlertTitle>
                {props.missingLinkMessage ?? defaultMissingLinkMessage}
            </Alert>
        );
    }
    if (error) {
        render = (
            <Alert variant="outlined" severity="error">
                <AlertTitle>
                    An unexpected error occurred while fetching linked Person
                    identity
                </AlertTitle>
                The system failed to determine if your user account is linked to
                a Person. Try refreshing. If the error persists, contact an
                administrator. Error: {link.errorMessage ?? "Unknown"}.
            </Alert>
        );
    }

    return {
        blocked:
            props.blockEnabled &&
            (missingLink || (props.blockOnError && error)),
        render,
        validLink,
    };
};
