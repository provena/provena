import { Button, ButtonGroup } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import React, { useState } from "react";
import {
    CopyFloatingButton,
    CopyableLinkedHandleComponent,
    useTypedLoadedItem,
    useUserLinkServiceLookup,
} from "react-libs";
import {
    ItemOrganisation,
    ItemPerson,
} from "react-libs/shared-interfaces/RegistryModels";
import { DatedCredentials } from "../types/types";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        creds: {
            backgroundColor: theme.palette.grey[300],
            padding: theme.spacing(2),
            wordWrap: "break-word",
            whiteSpace: "pre-line",
            fontSize: "small",
        },
    })
);

export interface AuthorCompactDisplayComponentProps {
    username: string;
}
export const AuthorCompactDisplayComponent = (
    props: AuthorCompactDisplayComponentProps
) => {
    /**
    Component: AuthorCompactDisplayComponent

    Manages the resolving and display of the author ItemPerson.

    Just shows a suitable message when errored/loading - or shows the email when
    loaded successfully.

    Returns a fragment - no other styling - this is compact view for the summary.
    */

    // Resolve the username's person ID using the link service
    const authorLink = useUserLinkServiceLookup({
        username: props.username,
    });
    const authorId = authorLink.data;

    // Load the specified Person ID from the registry
    const loadedAuthor = useTypedLoadedItem({
        id: authorId,
        subtype: "PERSON",
    });

    // Pull out the author data typed as a Person
    const typedAuthorData =
        loadedAuthor.data?.item !== undefined
            ? (loadedAuthor.data?.item as ItemPerson)
            : undefined;

    // States

    // Loading author link
    const loadingAuthorLink = authorLink.loading && !authorLink.data;

    // Author link error
    const authorLinkError = authorLink.error;

    // Author link missing
    const authorLinkMissing = !authorLink.loading && !authorLink.data;

    // Loading details
    const loadingAuthorDetails = loadedAuthor.loading && !loadedAuthor.data;

    // Error loading details
    const authorDetailsError = loadedAuthor.error;

    // Successful
    const successful = loadedAuthor.data !== undefined;

    const emailContents =
        loadingAuthorLink || loadingAuthorDetails
            ? "Loading ..."
            : authorLinkError || authorLinkMissing || authorDetailsError
            ? "Error..."
            : successful && typedAuthorData
            ? typedAuthorData.email ?? "Unknown"
            : "";

    return (
        <React.Fragment>
            Username: {props.username} | Email: {emailContents}
        </React.Fragment>
    );
};

export interface AuthorDetailsDisplayComponentProps {
    username: string;
}
export const AuthorDetailsDisplayComponent = (
    props: AuthorDetailsDisplayComponentProps
) => {
    /**
    Component: AuthorDetailsDisplayComponent

    Manages the resolving and display of the author ItemPerson 
    */

    // Resolve the username's person ID using the link service
    const authorLink = useUserLinkServiceLookup({
        username: props.username,
    });
    const authorId = authorLink.data;

    // Load the specified Person ID from the registry
    const loadedAuthor = useTypedLoadedItem({
        id: authorId,
        subtype: "PERSON",
    });

    // Pull out the author data typed as a Person
    const typedAuthorData =
        loadedAuthor.data?.item !== undefined
            ? (loadedAuthor.data?.item as ItemPerson)
            : undefined;

    // Establish author orcid optionally provided
    const orcidLink: JSX.Element | undefined = !!typedAuthorData?.orcid ? (
        <a href={typedAuthorData.orcid} target="_blank" rel="noreferrer">
            {" "}
            {typedAuthorData.orcid}
        </a>
    ) : undefined;

    // Add mailto to email link
    const emailLink = (email: string) => (
        <React.Fragment>
            {" <"}
            <a href={`mailto:${email}`}>{email}</a>
            {">"}
        </React.Fragment>
    );

    // States

    // Loading author link
    const loadingAuthorLink = authorLink.loading && !authorLink.data;

    // Author link error
    const authorLinkError = authorLink.error;

    // Author link missing
    const authorLinkMissing = !authorLink.loading && !authorLink.data;

    // Loading details
    const loadingAuthorDetails = loadedAuthor.loading && !loadedAuthor.data;

    // Error loading details
    const authorDetailsError = loadedAuthor.error;

    // Successful
    const successful = loadedAuthor.data !== undefined;

    return (
        <div>
            {
                // Show username if person ID is not loaded, else show personID
            }
            {!authorLink.data ? (
                <>
                    <h3>Username:</h3>
                    {props.username}
                </>
            ) : (
                <>
                    <h3>Linked Registry Identity:</h3>
                    <CopyableLinkedHandleComponent handleId={authorLink.data} />
                </>
            )}
            {loadingAuthorLink ? (
                <p>Loading author ID, please wait ...</p>
            ) : authorLinkError ? (
                <p>
                    The user's linked Person ID could not be retrieved. Error:{" "}
                    {authorLink.errorMessage ?? "Unknown"}
                </p>
            ) : authorLinkMissing ? (
                <p>
                    The user does not have a linked Person ID. No details
                    available.
                </p>
            ) : loadingAuthorDetails ? (
                <p>Loading author details, please wait ...</p>
            ) : authorDetailsError ? (
                <p>
                    The user's details could not be fetched from the registry.
                    Error: {loadedAuthor.errorMessage ?? "Unknown"}
                </p>
            ) : (
                successful &&
                typedAuthorData && (
                    <React.Fragment>
                        <h3>Author:</h3>
                        {`${typedAuthorData.first_name ?? ""} ${
                            typedAuthorData.last_name ?? ""
                        }`}
                        {typedAuthorData.email
                            ? emailLink(typedAuthorData.email)
                            : ""}
                        {!!orcidLink && (
                            <>
                                <h3>ORCID:</h3>
                                {orcidLink}
                            </>
                        )}
                    </React.Fragment>
                )
            )}
        </div>
    );
};

export interface OrganisationDetailsDisplayComponentProps {
    organisationId: string;
}
export const OrganisationDetailsDisplayComponent = (
    props: OrganisationDetailsDisplayComponentProps
) => {
    /**
    Component: PublisherDetailsDisplayComponent
    
    Displays the dataset details publisher details section

    Basic div containing headings.

    manages fetching the ID from the registry and displays any errors.
    */

    const orgId = props.organisationId;

    // dataset info - publisher
    const loadedOrg = useTypedLoadedItem({
        id: orgId,
        subtype: "ORGANISATION",
    });
    const typedOrgData =
        loadedOrg.data?.item !== undefined
            ? (loadedOrg.data?.item as ItemOrganisation)
            : undefined;

    // Establish ROR optionally provided
    var datasetRorLink;

    if (typedOrgData?.ror) {
        datasetRorLink = (
            <a href={typedOrgData.ror} target="_blank">
                {" "}
                {typedOrgData.ror}
            </a>
        );
    } else {
        datasetRorLink = "Unspecified";
    }

    // Loading details
    const loadingOrgDetails = loadedOrg.loading && !loadedOrg.data;

    // Error loading details
    const orgDetailsError = loadedOrg.error;

    // Successful
    const successful = loadedOrg.data !== undefined;

    return (
        <div>
            <h3>Organisation ID:</h3>
            {<CopyableLinkedHandleComponent handleId={props.organisationId} />}
            {loadingOrgDetails ? (
                <p>Loading organisation details... please wait</p>
            ) : orgDetailsError ? (
                <p>
                    The Organisation's details could not be fetched from the
                    registry. Error: {loadedOrg.errorMessage ?? "Unknown"}
                </p>
            ) : (
                successful &&
                typedOrgData && (
                    <React.Fragment>
                        <h3>Organisation name:</h3>
                        {typedOrgData.name ?? "Unknown"}
                        <h3>Organisation ROR:</h3>
                        {datasetRorLink}
                    </React.Fragment>
                )
            )}
        </div>
    );
};

export type CredentialProps = {
    credentials: DatedCredentials;
};

export const AWSCredentialDisplay = (props: CredentialProps) => {
    /**
     * Displays the AWS credentials - this is just the raw copyable display
     */

    const classes = useStyles();
    const bashFormat = `export AWS_ACCESS_KEY_ID="${props.credentials.aws_access_key_id}"
export AWS_SECRET_ACCESS_KEY="${props.credentials.aws_secret_access_key}"
export AWS_SESSION_TOKEN="${props.credentials.aws_session_token}"
`;
    const windowsCmdFormat = `SET AWS_ACCESS_KEY_ID=${props.credentials.aws_access_key_id}
SET AWS_SECRET_ACCESS_KEY=${props.credentials.aws_secret_access_key}
SET AWS_SESSION_TOKEN=${props.credentials.aws_session_token}
`;
    const windowsPowershellFormat = `$Env:AWS_ACCESS_KEY_ID="${props.credentials.aws_access_key_id}"
$Env:AWS_SECRET_ACCESS_KEY="${props.credentials.aws_secret_access_key}"
$Env:AWS_SESSION_TOKEN="${props.credentials.aws_session_token}"
`;

    const [useBashFormat, setUseBashFormat] = useState(true);
    const [useWindowsCmdFormat, setUseWindowsCmdFormat] = useState(false);
    const [useWindowsPowershellFormat, setUseWindowsPowershellFormat] =
        useState(false);

    var formattedCreds = "";
    if (useBashFormat) {
        formattedCreds = bashFormat;
    } else if (useWindowsCmdFormat) {
        formattedCreds = windowsCmdFormat;
    } else if (useWindowsPowershellFormat) {
        formattedCreds = windowsPowershellFormat;
    }

    return (
        <div>
            <div>
                <ButtonGroup variant="outlined">
                    <Button
                        color={useBashFormat ? "success" : "secondary"}
                        onClick={() => {
                            setUseBashFormat(true);
                            setUseWindowsCmdFormat(false);
                            setUseWindowsPowershellFormat(false);
                        }}
                    >
                        Linux Bash format
                    </Button>
                    <Button
                        color={useWindowsCmdFormat ? "success" : "secondary"}
                        onClick={() => {
                            setUseBashFormat(false);
                            setUseWindowsCmdFormat(true);
                            setUseWindowsPowershellFormat(false);
                        }}
                    >
                        Windows CMD format
                    </Button>
                    <Button
                        color={
                            useWindowsPowershellFormat ? "success" : "secondary"
                        }
                        onClick={() => {
                            setUseBashFormat(false);
                            setUseWindowsCmdFormat(false);
                            setUseWindowsPowershellFormat(true);
                        }}
                    >
                        Windows Powershell format
                    </Button>
                </ButtonGroup>
            </div>
            <div className={classes.creds}>
                <CopyFloatingButton clipboardText={formattedCreds} />
                {formattedCreds}
            </div>
            <i>Expires on {"" + props.credentials.expiry}</i>
        </div>
    );
};
