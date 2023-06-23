import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
    Button,
    FormGroup,
    FormControlLabel,
    Grid,
    Box,
    Typography,
    Table,
    TableHead,
    TableBody,
    TableCell,
    Backdrop,
    TableRow,
    Switch,
    Dialog,
    CircularProgress,
    DialogContent,
    DialogActions,
    DialogTitle,
} from "@mui/material";
import { observer } from "mobx-react-lite";
import accessStore from "../stores/accessStore";
import {
    IntendedUserType,
    ReportAuthorisationComponent,
    RequestAccessTableItem,
} from "../shared-interfaces/AuthAPI";
import { DOCUMENTATION_BASE_URL } from "react-libs";

const showRequestInTable = (
    accessRequestItems: Array<RequestAccessTableItem>
) => (
    <Box marginTop={6} marginBottom={2}>
        <Typography variant="h5">Existing Access Requests</Typography>
        <Table>
            <TableHead>
                <TableRow key="header">
                    <TableCell key="Request ID">Request ID</TableCell>
                    <TableCell key="User">User</TableCell>
                    <TableCell key="Status">Status</TableCell>
                    <TableCell key="Create Time">Created</TableCell>
                    <TableCell key="Expire Time">Wait time</TableCell>
                    <TableCell key="Request items">Requested items</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {accessRequestItems.map((req) => (
                    <TableRow key={req.request_id}>
                        <TableCell key={req.request_id}>
                            {req.request_id}
                        </TableCell>
                        <TableCell key={req.username}>{req.username}</TableCell>
                        <TableCell key={req.status}>
                            {req.ui_friendly_status ?? req.status}
                        </TableCell>
                        <TableCell key={req.created_timestamp}>
                            {new Date(
                                req.created_timestamp * 1000
                            ).toLocaleString()}{" "}
                        </TableCell>
                        <TableCell key={req.expiry}>
                            {Math.ceil(
                                (new Date().getTime() -
                                    new Date(
                                        req.created_timestamp * 1000
                                    ).getTime()) /
                                    (1000 * 60 * 60)
                            )}{" "}
                            Hours
                        </TableCell>
                        <TableCell>
                            {JSON.parse(req.request_diff_contents)[
                                "components"
                            ].map(
                                // @ts-ignore
                                (roleComponent) =>
                                    showRoleInTable(roleComponent, true, true)
                            )}
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    </Box>
);

const showRoleInTable = (
    roleComponent: ReportAuthorisationComponent,
    includeAdmin: boolean,
    dense: boolean = false
) => {
    var relevantCount = 0;

    const possibleContent = (
        <Box marginTop={2} marginBottom={2}>
            {!dense && (
                <Typography variant="h6">
                    Component: {roleComponent.component_name}
                </Typography>
            )}
            <Table size={dense ? "small" : "medium"}>
                {dense ? (
                    <TableHead>
                        <TableRow key="header">
                            <TableCell key="Role name">Role name</TableCell>
                            <TableCell key="Access level">
                                Access level
                            </TableCell>
                            <TableCell key="Access granted">
                                Access granted
                            </TableCell>
                        </TableRow>
                    </TableHead>
                ) : (
                    <TableHead>
                        <TableRow key="header">
                            <TableCell key="Role name">Role name</TableCell>
                            <TableCell key="Access level">
                                Access level
                            </TableCell>
                            <TableCell key="description">Description</TableCell>
                            <TableCell key="Access granted">
                                Access granted
                            </TableCell>
                        </TableRow>
                    </TableHead>
                )}
                <TableBody>
                    {roleComponent.component_roles.map((accessRole) => {
                        var show: boolean = false;
                        if (!includeAdmin) {
                            if (
                                accessRole.intended_users.includes(
                                    "GENERAL" as IntendedUserType
                                )
                            ) {
                                show = true;
                            }
                        } else {
                            show = true;
                        }
                        if (show) {
                            relevantCount += 1;
                            return (
                                <TableRow key={accessRole.role_name}>
                                    <TableCell
                                        key={accessRole.role_display_name}
                                    >
                                        {accessRole.role_display_name}
                                    </TableCell>
                                    <TableCell
                                        key={
                                            accessRole.role_name +
                                            accessRole.role_level
                                        }
                                    >
                                        {accessRole.role_level}
                                    </TableCell>
                                    {dense ? null : (
                                        <TableCell key={accessRole.description}>
                                            {accessRole.description}
                                        </TableCell>
                                    )}
                                    <TableCell
                                        key={
                                            accessRole.role_name +
                                            accessRole.access_granted
                                        }
                                    >
                                        {dense ? (
                                            accessRole.access_granted ? (
                                                "true"
                                            ) : (
                                                "false"
                                            )
                                        ) : (
                                            <Switch
                                                checked={
                                                    accessRole.access_granted
                                                }
                                                onChange={() =>
                                                    accessStore.updateRoles(
                                                        accessRole.role_name,
                                                        !accessRole.access_granted
                                                    )
                                                }
                                            />
                                        )}
                                    </TableCell>
                                </TableRow>
                            );
                        } else {
                            return null;
                        }
                    })}
                </TableBody>
            </Table>
        </Box>
    );
    if (relevantCount >= 1) {
        return possibleContent;
    } else {
        return null;
    }
};

interface IncludeAdminControlsProps {
    includeAdmin: boolean;
    setIncludeAdmin: (include: boolean) => void;
}

export const IncludeAdminControls = observer(
    (props: IncludeAdminControlsProps) => {
        return (
            <React.Fragment>
                <FormGroup>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={props.includeAdmin}
                                onChange={() =>
                                    props.setIncludeAdmin(!props.includeAdmin)
                                }
                            />
                        }
                        label={"Include admin-only roles?"}
                    ></FormControlLabel>
                </FormGroup>
            </React.Fragment>
        );
    }
);

interface RoleRequestsProps {}

export const RoleRequests = observer((props: RoleRequestsProps) => {
    // Setup preferences
    const [includeAdmin, setIncludeAdmin] = useState<boolean>(false);

    return (
        <React.Fragment>
            <Typography variant="h5">Roles</Typography>
            Use the toggle slider in the <i>on</i> position to request access
            for a role. Once you have made a change, use the{" "}
            <i>Request Roles Update</i> button. For more information, visit{" "}
            <a
                href={
                    DOCUMENTATION_BASE_URL +
                    "/information-system/getting-started-is/requesting-access-is.html"
                }
                target="_blank"
            >
                our documentation
            </a>
            .
            <IncludeAdminControls
                includeAdmin={includeAdmin}
                setIncludeAdmin={setIncludeAdmin}
            ></IncludeAdminControls>
            {/**
             * If the roles have changed, then display a message in a bordered
             * box which gives the request access change button.
             * If the roles have not changed, check if there has been a previous
             * successful request made, in which case a message thanking the user
             * and prompting them to return home will be displayed.
             */}
            {accessStore.rolesChanged() ? (
                <Grid
                    container
                    justifyContent="center"
                    style={{
                        padding: 25,
                    }}
                    sx={{
                        border: 5,
                        borderColor: "primary.main",
                    }}
                >
                    <Grid
                        xs={12}
                        sx={{
                            marginBottom: 3,
                        }}
                    >
                        <Typography variant="h5" align="center">
                            Submit your changes by pressing the button below
                        </Typography>
                    </Grid>
                    <Grid>
                        <Button
                            variant="contained"
                            onClick={() => accessStore.requestRolesUpdate()}
                        >
                            Request Roles Update
                        </Button>
                    </Grid>
                </Grid>
            ) : accessStore.successfulReportMade ? (
                <Grid
                    container
                    justifyContent="center"
                    style={{
                        padding: 25,
                    }}
                    sx={{
                        border: 5,
                        borderColor: "primary.main",
                    }}
                >
                    <Grid
                        xs={12}
                        sx={{
                            marginBottom: 3,
                        }}
                    >
                        <Typography variant="h5" align="center">
                            Your access request has been received
                        </Typography>
                    </Grid>
                    <Grid
                        xs={12}
                        sx={{
                            marginBottom: 3,
                        }}
                    >
                        <Typography variant="body1" align="left">
                            Thank you for making an access request. We will
                            apply these changes as soon as possible. In the
                            meantime, you might like to return to the home page.
                            You can do so using the button below.
                        </Typography>
                    </Grid>
                    <Grid>
                        <Button component={Link} to={"/"} variant="contained">
                            Return Home
                        </Button>
                    </Grid>
                </Grid>
            ) : null}
            {/**
             * Display the access report based on the 'proposed' access
             * i.e. what the user has selected - defaulting to the actual
             * current access as per the access report from the auth
             * API.
             */}
            {accessStore.proposedAccessReport?.components.map((component) =>
                showRoleInTable(component, includeAdmin)
            )}
            {showRequestInTable(accessStore.accessRequestedItems || [])}
            {/**
             * The remaining sections are backdrops/dialogues for loading,
             * response, and error dialogues/conditions.
             */}
            <Backdrop open={accessStore.accessRolesRequesting}>
                <CircularProgress />
            </Backdrop>
            <Dialog
                open={accessStore.accessRolesRequestingDialog}
                onClose={() => accessStore.closeDialog()}
            >
                <DialogTitle>Update Roles</DialogTitle>
                <DialogContent>
                    {accessStore.accessRequestResponseMessage ??
                        "Message loading..."}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => accessStore.closeDialog()}>
                        Confirm
                    </Button>
                </DialogActions>
            </Dialog>
        </React.Fragment>
    );
});
