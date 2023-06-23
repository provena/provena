import React, { useState } from "react";
import {
    Button,
    Grid,
    Box,
    Typography,
    Checkbox,
    Table,
    TableRow,
    TableCell,
    TableHead,
    TableBody,
    IconButton,
    Collapse,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    MenuItem,
    FormGroup,
    FormControlLabel,
    TextField,
    FormControl,
    InputLabel,
    Input,
} from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import { Theme } from "@mui/material/styles";
import makeStyles from "@mui/styles/makeStyles";
import createStyles from "@mui/styles/createStyles";
import { observer } from "mobx-react-lite";
import adminStore from "../stores/adminStore";
import {
    ReportAuthorisationComponent,
    RequestAccessTableItem,
    RequestStatus,
} from "../shared-interfaces/AuthAPI";

interface StatusSelectorFormProps {
    handleStatusChoice: (value: RequestStatus) => void;
    disabled: boolean;
    selectorLabel: string;
}

const StatusSelectorForm = observer((props: StatusSelectorFormProps) => {
    const pendingApproval: RequestStatus = "PENDING_APPROVAL";
    const approvedPendingAction: RequestStatus = "APPROVED_PENDING_ACTION";
    const deniedPendingDeletion: RequestStatus = "DENIED_PENDING_DELETION";
    const actionedPendingDeletion: RequestStatus = "ACTIONED_PENDING_DELETION";

    return (
        <FormControl variant="standard" size="small" disabled={props.disabled}>
            <TextField
                onChange={(event) => {
                    const status: RequestStatus = event.target
                        .value as RequestStatus;
                    props.handleStatusChoice(status);
                }}
                label={props.selectorLabel}
                variant="outlined"
                color="primary"
                disabled={props.disabled}
                select
            >
                <MenuItem value={pendingApproval}>Pending Approval</MenuItem>
                <MenuItem value={approvedPendingAction}>
                    Approved Pending Action
                </MenuItem>
                <MenuItem value={deniedPendingDeletion}>
                    Denied Pending Deletion
                </MenuItem>
                <MenuItem value={actionedPendingDeletion}>
                    Actioned Pending Deletion
                </MenuItem>
            </TextField>
        </FormControl>
    );
});
interface UpdateStatusProps {
    username: string;
    requestID: number;
    email: string;
    currentStatus: RequestStatus;
}

const UpdateStatusButtonDialog = observer((props: UpdateStatusProps) => {
    const [open, setOpen] = React.useState(false);
    const [failureState, setFailureState] = React.useState(false);
    const [failureReason, setFailureReason] = React.useState("");
    const [sendEmailAlert, setSendEmailAlert] = React.useState(true);
    const [desiredStatus, setDesiredStatus] = React.useState(
        props.currentStatus
    );
    const [busy, setBusy] = React.useState(false);

    const handleClickOpen = () => {
        setOpen(true);
    };

    const handleCancel = () => {
        setOpen(false);
        setFailureState(false);
        setFailureReason("");
    };

    const handleFailCancel = () => {
        setOpen(true);
        setFailureState(false);
        setFailureReason("");
    };

    const handleUpdate = (desired_status: RequestStatus) => {
        setBusy(true);
        adminStore.updateStatus(
            props.username,
            props.requestID,
            sendEmailAlert,
            desired_status,
            () => {
                setBusy(false);
                handleCancel();
                adminStore.getAllRequests();
            },
            (reason) => {
                setBusy(false);
                setFailureState(true);
                setFailureReason(reason);
            }
        );
    };

    return (
        <div>
            <Button variant="outlined" onClick={handleClickOpen}>
                Change Status
            </Button>
            <Dialog open={open} onClose={handleCancel}>
                {busy ? (
                    <React.Fragment>
                        <DialogTitle>Please wait...loading</DialogTitle>
                    </React.Fragment>
                ) : failureState ? (
                    <React.Fragment>
                        <DialogTitle>Update Failed!</DialogTitle>
                        <DialogContent>
                            <DialogContentText>
                                Something went wrong when modifying the record!{" "}
                                {failureReason}
                            </DialogContentText>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleFailCancel}>Cancel</Button>
                        </DialogActions>
                    </React.Fragment>
                ) : (
                    <React.Fragment>
                        <DialogTitle>Update entry status</DialogTitle>
                        <DialogContent>
                            <DialogContentText>
                                Please confirm the new status of this record.{" "}
                                <br />
                                Username: {props.username} <br />
                                request_id: {props.requestID}
                            </DialogContentText>
                            <br />
                            <FormGroup>
                                <FormControl variant="outlined" size="small">
                                    <FormControlLabel
                                        control={
                                            <Checkbox
                                                checked={sendEmailAlert}
                                                onChange={(e) =>
                                                    setSendEmailAlert(
                                                        e.target.checked
                                                    )
                                                }
                                            />
                                        }
                                        label={
                                            "Send email alert to " +
                                            props.email +
                                            "?"
                                        }
                                    ></FormControlLabel>
                                </FormControl>
                                <StatusSelectorForm
                                    handleStatusChoice={(status) =>
                                        setDesiredStatus(status)
                                    }
                                    disabled={false}
                                    selectorLabel="Desired Status"
                                ></StatusSelectorForm>
                            </FormGroup>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleCancel}>Cancel</Button>
                            <Button
                                color="success"
                                onClick={() => handleUpdate(desiredStatus)}
                            >
                                Submit
                            </Button>
                        </DialogActions>
                    </React.Fragment>
                )}
            </Dialog>
        </div>
    );
});

interface DeleteProps {
    username: string;
    request_id: number;
}

const DeleteButtonDialog = observer((props: DeleteProps) => {
    const [open, setOpen] = React.useState(false);
    const [failureState, setFailureState] = React.useState(false);
    const [failureReason, setFailureReason] = React.useState("");

    const handleClickOpen = () => {
        setOpen(true);
    };

    const handleCancel = () => {
        setOpen(false);
        setFailureState(false);
        setFailureReason("");
    };

    const handleFailureCancel = () => {
        setOpen(true);
        setFailureState(false);
        setFailureReason("");
    };

    const handleDelete = () => {
        adminStore.deleteRequest(
            props.username,
            props.request_id,
            () => {
                handleCancel();
                adminStore.getAllRequests();
            },
            (reason) => {
                setFailureState(true);
                setFailureReason(reason);
            }
        );
    };

    return (
        <div>
            <IconButton
                aria-label="delete item"
                size="small"
                onClick={handleClickOpen}
            >
                <DeleteIcon />
            </IconButton>
            <Dialog open={open} onClose={handleCancel}>
                {failureState ? (
                    <React.Fragment>
                        <DialogTitle>Delete Failed!</DialogTitle>
                        <DialogContent>
                            <DialogContentText>
                                Something went wrong when deleting the record!{" "}
                                {failureReason}
                            </DialogContentText>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleFailureCancel}>
                                Cancel
                            </Button>
                        </DialogActions>
                    </React.Fragment>
                ) : (
                    <React.Fragment>
                        <DialogTitle>Delete Entry</DialogTitle>
                        <DialogContent>
                            <DialogContentText>
                                Please confirm deletion of this record. <br />
                                Username: {props.username} <br />
                                request_id: {props.request_id}
                            </DialogContentText>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleCancel}>Cancel</Button>
                            <Button color="error" onClick={handleDelete}>
                                Delete
                            </Button>
                        </DialogActions>
                    </React.Fragment>
                )}
            </Dialog>
        </div>
    );
});

const showRoleInTable = (
    roleComponent: ReportAuthorisationComponent,
    dense: boolean = false
) => (
    <Box marginTop={2} marginBottom={2}>
        {!dense && (
            <Typography variant="h6">
                Group: {roleComponent.component_name}
            </Typography>
        )}
        <Table size={dense ? "small" : "medium"}>
            {!dense && (
                <TableHead>
                    <TableRow key="header">
                        <TableCell key="Role display name">
                            Role display name
                        </TableCell>
                        <TableCell key="Role name">Role name</TableCell>
                        <TableCell key="Access granted">
                            Access granted
                        </TableCell>
                    </TableRow>
                </TableHead>
            )}
            <TableBody>
                {roleComponent.component_roles.map((accessRole) => (
                    <TableRow key={accessRole.role_name}>
                        <TableCell key={accessRole.role_display_name}>
                            {accessRole.role_display_name}
                        </TableCell>
                        <TableCell key={accessRole.role_name}>
                            {accessRole.role_name}
                        </TableCell>
                        <TableCell
                            key={
                                accessRole.role_name + accessRole.access_granted
                            }
                        >
                            {accessRole.access_granted ? "true" : "false"}
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    </Box>
);

interface AddNoteDialogButtonProps {
    username: string;
    requestId: number;
    request: RequestAccessTableItem;
}

const AddNoteDialogButton = observer((props: AddNoteDialogButtonProps) => {
    const [open, setOpen] = React.useState(false);
    const [failureState, setFailureState] = React.useState(false);
    const [failureReason, setFailureReason] = React.useState("");
    const [noteContent, setNoteContent] = React.useState("");
    const [includeTimestamp, setIncludeTimestamp] = React.useState(true);

    const handleClickOpen = () => {
        setOpen(true);
    };

    const handleCancel = () => {
        setOpen(false);
        setFailureState(false);
        setFailureReason("");
    };

    const handleFailureCancel = () => {
        setOpen(true);
        setFailureState(false);
        setFailureReason("");
    };

    const handleAddNote = () => {
        if (noteContent === "") {
            setFailureState(true);
            setFailureReason("You can't add an empty note!");
        } else {
            // Include optional timestamp
            var timestamp = "";
            if (includeTimestamp) {
                timestamp +=
                    " (at " +
                    new Date().toLocaleString().replaceAll(",", " -") +
                    ")";
            }

            const desiredContent = noteContent + timestamp;
            adminStore.addNote(
                props.username,
                props.requestId,
                desiredContent,
                () => {
                    handleCancel();

                    // Add new note to list - no need to refresh full menu
                    const currentNotes = props.request.notes.split(",");
                    currentNotes.push(desiredContent);
                    props.request.notes = currentNotes.join(",");
                },
                (reason) => {
                    setFailureState(true);
                    setFailureReason(reason);
                }
            );
        }
    };

    const handleNoteUpdate = (event: React.ChangeEvent<HTMLInputElement>) => {
        setNoteContent(event.target.value);
    };

    const handleTimestampIncludeCheckbox = (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        setIncludeTimestamp(event.target.checked);
    };

    return (
        <div>
            <IconButton
                aria-label="add note"
                size="medium"
                onClick={handleClickOpen}
                color="success"
            >
                <AddIcon />
            </IconButton>
            <Dialog open={open} onClose={handleCancel}>
                {failureState ? (
                    <React.Fragment>
                        <DialogTitle>Add note failed!</DialogTitle>
                        <DialogContent>
                            <DialogContentText>
                                Something went wrong when adding note!{" "}
                                {failureReason}
                            </DialogContentText>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleFailureCancel}>
                                Cancel
                            </Button>
                        </DialogActions>
                    </React.Fragment>
                ) : (
                    <React.Fragment>
                        <DialogTitle>Add Note</DialogTitle>
                        <DialogContent>
                            <DialogContentText>
                                Please specify note you want to add for this
                                request. <br />
                            </DialogContentText>
                            <FormGroup>
                                <FormControl variant="outlined" size="small">
                                    <FormControlLabel
                                        control={
                                            <Checkbox
                                                checked={includeTimestamp}
                                                onChange={
                                                    handleTimestampIncludeCheckbox
                                                }
                                            />
                                        }
                                        label={"Include note timestamp?"}
                                    ></FormControlLabel>
                                </FormControl>
                                <FormControl variant="outlined" size="small">
                                    <InputLabel>New note</InputLabel>
                                    <Input
                                        id="new note entry"
                                        onChange={handleNoteUpdate}
                                    />
                                </FormControl>
                            </FormGroup>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleCancel}>Cancel</Button>
                            <Button color="success" onClick={handleAddNote}>
                                Submit
                            </Button>
                        </DialogActions>
                    </React.Fragment>
                )}
            </Dialog>
        </div>
    );
});

interface DisplayNotesProp {
    item: RequestAccessTableItem;
}

const DisplayNotes = observer((props: DisplayNotesProp) => {
    // Get list of notes from the note field
    const noteList: Array<string> = props.item.notes.split(",");

    // Return note rows and
    // add note button
    return (
        <Table>
            <TableHead>
                <TableRow key="header">
                    <TableCell key="Note">Note</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {noteList.map((note, index) => (
                    <TableRow>
                        <TableCell key={index}>{note}</TableCell>
                    </TableRow>
                ))}
                <TableRow>
                    <TableCell>
                        Add note:
                        <AddNoteDialogButton
                            username={props.item.username}
                            requestId={props.item.request_id}
                            request={props.item}
                        ></AddNoteDialogButton>
                    </TableCell>
                </TableRow>
            </TableBody>
        </Table>
    );
});

interface RequestTableItem {
    item: RequestAccessTableItem;
}

const RequestTableRow = observer((props: RequestTableItem) => {
    const [expanded, setExpanded] = useState(false);
    return (
        <React.Fragment>
            <TableRow
                key={"" + props.item.request_id + props.item.username}
                hover={true}
            >
                <TableCell>
                    <IconButton
                        aria-label="expand row"
                        size="small"
                        onClick={() => setExpanded(!expanded)}
                    >
                        {expanded ? (
                            <KeyboardArrowDownIcon />
                        ) : (
                            <KeyboardArrowRightIcon />
                        )}
                    </IconButton>
                </TableCell>
                <TableCell key={props.item.request_id}>
                    {props.item.request_id}
                </TableCell>
                <TableCell key={props.item.username}>
                    {props.item.username}
                </TableCell>
                <TableCell key={props.item.status}>
                    {props.item.status}
                </TableCell>
                <TableCell key={props.item.created_timestamp}>
                    {new Date(
                        props.item.created_timestamp * 1000
                    ).toLocaleString()}{" "}
                </TableCell>
                <TableCell key={props.item.expiry}>
                    {Math.ceil(
                        (new Date().getTime() -
                            new Date(
                                props.item.created_timestamp * 1000
                            ).getTime()) /
                            (1000 * 60 * 60)
                    )}{" "}
                    Hours
                </TableCell>
                <TableCell key={"update state" + props.item.request_id}>
                    <UpdateStatusButtonDialog
                        username={props.item.username}
                        requestID={props.item.request_id}
                        currentStatus={props.item.status}
                        email={props.item.email}
                    ></UpdateStatusButtonDialog>
                </TableCell>
                <TableCell key={"delete" + props.item.request_id}>
                    <DeleteButtonDialog
                        username={props.item.username}
                        request_id={props.item.request_id}
                    ></DeleteButtonDialog>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell
                    style={{ paddingBottom: 0, paddingTop: 0 }}
                    colSpan={8}
                >
                    <Collapse in={expanded} timeout="auto" unmountOnExit>
                        <br />
                        <Typography variant="h5" align="center">
                            Request Details
                        </Typography>

                        <Typography variant="h6" align="left">
                            Notes
                        </Typography>

                        <DisplayNotes item={props.item}></DisplayNotes>

                        <br />

                        <Typography variant="h6" align="left">
                            Requested Access Changes
                        </Typography>

                        {JSON.parse(props.item.request_diff_contents)[
                            "components"
                        ].map(
                            // @ts-ignore
                            (roleComponent) =>
                                showRoleInTable(roleComponent, false)
                        )}
                    </Collapse>
                </TableCell>
            </TableRow>
        </React.Fragment>
    );
});

const RefreshButton = observer(() => {
    return (
        <Button
            onClick={() => adminStore.getAllRequests()}
            variant="outlined"
            color="secondary"
        >
            Refresh request list
        </Button>
    );
});

interface RequestItemTableProps {
    items: Array<RequestAccessTableItem>;
    statusFilter: RequestStatus | undefined;
    usernameFilter: string | undefined;
}

const RequestItemTable = observer((props: RequestItemTableProps) => {
    return (
        <Table>
            <TableHead>
                <TableRow key="header">
                    <TableCell key="Expand"></TableCell>
                    <TableCell key="Request ID">Request ID</TableCell>
                    <TableCell key="User">User</TableCell>
                    <TableCell key="Status">Status</TableCell>
                    <TableCell key="Create Time">Created</TableCell>
                    <TableCell key="Expire Time">Wait time</TableCell>
                    <TableCell key="Change State">Update state</TableCell>
                    <TableCell key="Delete">Delete</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {props.items.map((req) => {
                    // Check if we need to apply filter and if so
                    // Return null if filter fails
                    if (props.statusFilter || props.usernameFilter) {
                        if (
                            props.statusFilter &&
                            !(
                                req.status.valueOf() ===
                                props.statusFilter.valueOf()
                            )
                        ) {
                            return null;
                        }
                        if (
                            props.usernameFilter &&
                            !req.username
                                .toUpperCase()
                                .trim()
                                .includes(
                                    props.usernameFilter.toUpperCase().trim()
                                )
                        ) {
                            return null;
                        }
                    }
                    // In all other cases, return the row item
                    return <RequestTableRow item={req}></RequestTableRow>;
                })}
            </TableBody>
        </Table>
    );
});

interface RequestTableFilterProps {
    setStatusFilter: (value: RequestStatus) => void;
    setUsernameFilter: (value: string) => void;
    setStatusFilterActive: (value: boolean) => void;
    setUsernameFilterActive: (value: boolean) => void;
    usernameFilterActive: boolean;
    statusFilterActive: boolean;
}

const RequestTableFilters = observer((props: RequestTableFilterProps) => {
    const handleStatusFilterCheckbox = (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        props.setStatusFilterActive(event.target.checked);
    };

    const handleUsernameFilterCheckbox = (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        props.setUsernameFilterActive(event.target.checked);
    };

    const handleUsernameFilterUpdate = (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        props.setUsernameFilter(event.target.value);
    };

    return (
        <React.Fragment>
            <FormGroup>
                <FormControlLabel
                    control={<Checkbox onChange={handleStatusFilterCheckbox} />}
                    label={"Filter request status?"}
                ></FormControlLabel>

                <StatusSelectorForm
                    handleStatusChoice={props.setStatusFilter}
                    selectorLabel="Desired status"
                    disabled={!props.statusFilterActive}
                ></StatusSelectorForm>

                <FormControlLabel
                    control={
                        <Checkbox onChange={handleUsernameFilterCheckbox} />
                    }
                    label={"Filter username?"}
                ></FormControlLabel>

                <FormControl
                    disabled={!props.usernameFilterActive}
                    variant="outlined"
                    size="small"
                >
                    <InputLabel>Username query</InputLabel>
                    <Input
                        id="username-query"
                        onChange={handleUsernameFilterUpdate}
                    />
                </FormControl>
            </FormGroup>
        </React.Fragment>
    );
});

export const ManageAccessRequests = observer(() => {
    // Are filters active?
    const [statusFilterActive, setStatusFilterActive] = useState(false);
    const [usernameFilterActive, setUsernameFilterActive] = useState(false);

    // Default inactive values
    const [statusFilter, setStatusFilter] = useState(
        "PENDING_APPROVAL" as RequestStatus
    );
    const [usernameFilter, setUsernameFilter] = useState("");

    !adminStore.requests && adminStore.getAllRequests();

    if (!adminStore.requests || adminStore.retrievingRequests) {
        return <div>Retrieving requests...</div>;
    }

    if (adminStore.requestFailure) {
        return (
            <div>
                <RefreshButton /> <br />
                Something went wrong retrieving requests - check console.
            </div>
        );
    }
    return (
        <div>
            <Grid container xs={12} rowGap={1.5}>
                <Grid item xs={12}>
                    <Typography variant="h5" align="left">
                        Access Control
                    </Typography>
                </Grid>
                <Grid xs={6}>
                    <RequestTableFilters
                        setStatusFilter={(val) => setStatusFilter(val)}
                        setStatusFilterActive={(b) => setStatusFilterActive(b)}
                        setUsernameFilter={(val) => setUsernameFilter(val)}
                        setUsernameFilterActive={(b) =>
                            setUsernameFilterActive(b)
                        }
                        usernameFilterActive={usernameFilterActive}
                        statusFilterActive={statusFilterActive}
                    ></RequestTableFilters>

                    <br />
                    <RefreshButton />
                </Grid>

                <Grid xs={12}>
                    <RequestItemTable
                        items={adminStore.requests}
                        statusFilter={
                            statusFilterActive ? statusFilter : undefined
                        }
                        usernameFilter={
                            usernameFilterActive ? usernameFilter : undefined
                        }
                    ></RequestItemTable>
                </Grid>
            </Grid>
        </div>
    );
});
