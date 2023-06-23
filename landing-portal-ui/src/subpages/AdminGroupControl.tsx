import { observer } from "mobx-react-lite";
import { action } from "mobx";
import {
    Box,
    CircularProgress,
    Divider,
    Grid,
    Button,
    IconButton,
    Typography,
    Table,
    TableCell,
    Collapse,
    Alert,
    AlertTitle,
    TableRow,
    TableBody,
    TextField,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogContentText,
    DialogActions,
    FormGroup,
    FormControlLabel,
    TableHead,
    Switch,
    Checkbox,
} from "@mui/material";
import groupStore, { GroupStore } from "../stores/groupStore";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import AddIcon from "@mui/icons-material/Add";
import React, { useEffect, useState } from "react";
import {
    UserGroupMetadata,
    UserGroup,
    GroupUser,
    RemoveGroupResponse,
    AddMemberResponse,
    RemoveMemberResponse,
    UpdateGroupResponse,
    DescribeGroupResponse,
    AddGroupResponse,
} from "../shared-interfaces/AuthAPI";
import makeStyles from "@mui/styles/makeStyles";
import createStyles from "@mui/styles/createStyles";
import { Theme } from "@mui/material/styles";
import {
    DataGrid,
    GridToolbar,
    GridRowsProp,
    GridColDef,
    GridSelectionModel,
} from "@mui/x-data-grid";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        GroupItem: {
            border: "2px solid grey",
            borderRadius: "5px",
            margin: "5px",
            padding: "10px",
        },
        PropertyTableRow: {},
        PropertyTable: {
            borderSpacing: "0 20px !important",
            borderCollapse: "separate",
        },
        PropertyTableCell: {
            borderBottom: "none",
        },
        FormTextFields: {
            padding: "10px",
        },
    })
);

interface GroupItemProps {
    group: UserGroupMetadata;
    onMetadataChange: () => void;
    onGroupRemoved: () => void;
}
const GroupItem = observer((props: GroupItemProps) => {
    /**
     * Component: GroupItem
     *
     */
    const classes = useStyles();

    // Expandable section
    const [expanded, setExpanded] = useState(false);

    // This needs to be observable
    const [localGroupStore] = useState(() => new GroupStore());
    const listAction = localGroupStore.listMembersAction;

    // Some state to contain the selected members for actions like remove
    // members
    const [selectedMembers, setSelectedMembers] = useState<Array<string>>([]);

    var content: JSX.Element = <React.Fragment></React.Fragment>;

    // Load members list
    useEffect(() => {
        if (expanded && listAction.awaitingLoad()) {
            console.log("Loading group list");
            localGroupStore.listMembers(props.group.id);
        }
    }, [expanded]);

    if (listAction.failed()) {
        content = (
            <p>
                There was an error loading the dataset metadata. Error:{" "}
                {listAction.errorMessage ?? "Unknown"}
            </p>
        );
    }
    if (listAction.loading || !listAction.content?.group) {
        content = (
            <Grid container xs={12} justifyContent={"center"}>
                <Grid item>
                    <CircularProgress />
                </Grid>
            </Grid>
        );
    } else {
        content = (
            <React.Fragment>
                <Grid item xs={12}>
                    <Divider />
                </Grid>
                <Grid
                    container
                    xs={12}
                    spacing={2}
                    justifyContent="left"
                    flexWrap={"nowrap"}
                >
                    <Grid item xs={7}>
                        <GroupMembersList
                            populatedGroup={listAction.content.group}
                            setSelectedMembers={setSelectedMembers}
                        ></GroupMembersList>
                    </Grid>
                    <Grid item xs={5}>
                        <Grid container xs={12} rowGap={1}>
                            <Grid item xs={12}>
                                <GroupMetadataColumn
                                    populatedGroup={listAction.content.group}
                                ></GroupMetadataColumn>
                            </Grid>
                            <Grid item xs={12}>
                                <Divider />
                            </Grid>
                            <Grid item xs={12}>
                                <GroupActionsPanel
                                    populatedGroup={listAction.content.group}
                                    onGroupRemoved={props.onGroupRemoved}
                                    selectedMembers={selectedMembers}
                                    onGroupMetadataChange={
                                        props.onMetadataChange
                                    }
                                    onUserListChange={() => {
                                        // Clear any selections when the user list is refreshed
                                        setSelectedMembers([]);
                                        // Force a reload of user list
                                        localGroupStore.listMembers(
                                            props.group.id
                                        );
                                    }}
                                ></GroupActionsPanel>
                            </Grid>
                        </Grid>
                    </Grid>
                </Grid>
            </React.Fragment>
        );
    }

    return (
        <Grid item xs={12}>
            <Box className={classes.GroupItem}>
                <Grid container xs={12} rowGap={1.5}>
                    {
                        // Header
                    }
                    <Grid
                        container
                        xs={12}
                        alignItems="center"
                        justifyContent="space-between"
                        padding={1}
                    >
                        <Grid item>
                            <b>{props.group.display_name}</b>
                        </Grid>
                        <Grid item>
                            <IconButton
                                size="small"
                                onClick={() => setExpanded(!expanded)}
                            >
                                {expanded ? (
                                    <React.Fragment>
                                        <KeyboardArrowDownIcon /> Collapse
                                    </React.Fragment>
                                ) : (
                                    <React.Fragment>
                                        <KeyboardArrowRightIcon /> Expand
                                    </React.Fragment>
                                )}
                            </IconButton>
                        </Grid>{" "}
                    </Grid>
                    {
                        // Expanded content
                    }
                    {expanded && content}
                </Grid>
            </Box>
        </Grid>
    );
});

interface GroupMetadataColumnProps {
    populatedGroup: UserGroup;
}
const GroupMetadataColumn = observer((props: GroupMetadataColumnProps) => {
    /**
     * Component: GroupMetadataColumn
     *
     *
     */
    const classes = useStyles();
    return (
        <Table padding={"checkbox"} className={classes.PropertyTable}>
            <TableBody>
                <TableRow className={classes.PropertyTableRow}>
                    <TableCell className={classes.PropertyTableCell}>
                        {
                            //key
                        }
                        <b>Id:</b>
                    </TableCell>
                    <TableCell
                        className={classes.PropertyTableCell}
                        align={"right"}
                    >
                        {
                            //value
                        }

                        {props.populatedGroup.id}
                    </TableCell>
                </TableRow>
                <TableRow className={classes.PropertyTableRow}>
                    <TableCell className={classes.PropertyTableCell}>
                        {
                            //key
                        }
                        <b>Group name:</b>
                    </TableCell>
                    <TableCell
                        className={classes.PropertyTableCell}
                        align="right"
                    >
                        {
                            //value
                        }
                        {props.populatedGroup.display_name}
                    </TableCell>
                </TableRow>
                <TableRow className={classes.PropertyTableRow}>
                    <TableCell className={classes.PropertyTableCell}>
                        {
                            //key
                        }
                        <b>Description: </b>
                    </TableCell>
                    <TableCell
                        className={classes.PropertyTableCell}
                        align="right"
                    >
                        {
                            //value
                        }
                        {props.populatedGroup.description}
                    </TableCell>
                </TableRow>
                <TableRow className={classes.PropertyTableRow}>
                    <TableCell className={classes.PropertyTableCell}>
                        {
                            //key
                        }
                        <b>Members:</b>
                    </TableCell>
                    <TableCell
                        className={classes.PropertyTableCell}
                        align="right"
                    >
                        {
                            //value
                        }
                        {props.populatedGroup.users.length}
                    </TableCell>
                </TableRow>
            </TableBody>
        </Table>
    );
});

interface MemberListGridRow {
    id: string;
    usernameEmail: string;
}

interface GroupMembersListProps {
    populatedGroup: UserGroup;
    setSelectedMembers: (members: Array<string>) => void;
}
const GroupMembersList = observer((props: GroupMembersListProps) => {
    /**
     * Component: GroupMembersList
     *
     */
    const defaultRowsPerPage = 10;
    const tableHeight = 600;
    const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);

    // data grid multi user selection
    const [selectionModel, setSelectionModel] = useState<GridSelectionModel>(
        []
    );

    const rows: GridRowsProp = props.populatedGroup.users
        // Make a standard interface from group items and pull out
        // membership
        .map((member) => {
            return {
                // create unique string id combination
                id: member.username,
                usernameEmail: member.email
                    ? `${member.username} (${member.email})`
                    : member.username,
            } as MemberListGridRow;
        });
    const columns: GridColDef[] = [
        { field: "usernameEmail", headerName: "User", flex: 1 },
    ];

    // This shouldn't occur since we don't run the dialog unless there is
    // history, but here as a catch all
    if (rows.length === 0) {
        return (
            <Grid container xs={12} alignContent="left" padding={1}>
                <Grid item>This group has no members.</Grid>
            </Grid>
        );
    }

    return (
        <Grid container xs={12} rowGap={1}>
            <Grid item xs={12}>
                <div style={{ height: tableHeight, width: "100%" }}>
                    <DataGrid
                        pageSize={pageSize}
                        disableColumnFilter
                        disableColumnSelector
                        disableDensitySelector
                        rowsPerPageOptions={[5, 10, 20]}
                        onPageSizeChange={(size) => {
                            setPageSize(size);
                        }}
                        checkboxSelection
                        onSelectionModelChange={(newSelectionModel) => {
                            setSelectionModel(newSelectionModel);
                            props.setSelectedMembers(
                                newSelectionModel as Array<string>
                            );
                        }}
                        components={{ Toolbar: GridToolbar }}
                        componentsProps={{
                            toolbar: {
                                showQuickFilter: true,
                                quickFilterProps: { debounceMs: 500 },
                            },
                        }}
                        selectionModel={selectionModel}
                        columns={columns}
                        rows={rows}
                    ></DataGrid>
                </div>
            </Grid>
        </Grid>
    );
});

interface GroupMetadataDialogProps {
    // Dialog title - this might be different as we could either be
    // adding/updating a group
    dialogTitle: string;
    // Is this a new dataset or updating?
    new: boolean;
    // Existing group metadata? Use as default fields
    groupMetadata?: UserGroupMetadata;
    // When the dismiss button is pressed
    onDismiss: () => void;
    // When the confirm button is pressed
    onConfirm: (metadata: UserGroupMetadata) => void;
}
const GroupMetadataDialog = observer((props: GroupMetadataDialogProps) => {
    /**
     * Component: GroupMetadataDialog
     *
     */

    // Group form components
    const [description, setDescription] = useState<string | undefined>(
        props.groupMetadata ? props.groupMetadata.description : undefined
    );
    const [displayName, setDisplayName] = useState<string | undefined>(
        props.groupMetadata ? props.groupMetadata.display_name : undefined
    );
    const [groupId, setGroupId] = useState<string | undefined>(
        props.groupMetadata ? props.groupMetadata.id : undefined
    );

    // default data store access
    // default metadata config

    const classes = useStyles();

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        props.onConfirm({
            description: description,
            display_name: displayName,
            id: groupId,
            //default_data_store_access: usingGroupAccess
            //    ? {
            //          metadata_access: metadataAccess,
            //          data_access: dataAccess,
            //          admin: adminAccess,
            //      }
            //    : undefined,
        } as UserGroupMetadata);
        event.preventDefault();
    };

    return (
        <Dialog open={true}>
            <DialogTitle>
                <Grid container xs={12} justifyContent={"space-between"}>
                    <Grid item>{props.dialogTitle}</Grid>
                    <Grid item>
                        <Button
                            color="warning"
                            variant="outlined"
                            onClick={() => props.onDismiss()}
                        >
                            Exit
                        </Button>
                    </Grid>
                </Grid>
            </DialogTitle>
            <DialogContent>
                <Grid container xs={12} rowGap={2} padding={1}>
                    <Grid item xs={12}>
                        <DialogContentText>
                            Enter the details of the user group
                        </DialogContentText>
                    </Grid>
                    <Grid item xs={12}>
                        <form autoComplete="off" onSubmit={handleSubmit}>
                            <TextField
                                onChange={(e) => setGroupId(e.target.value)}
                                className={classes.FormTextFields}
                                value={groupId}
                                disabled={!props.new}
                                label="Unique ID"
                                variant="outlined"
                                color="secondary"
                                fullWidth
                                required
                            />
                            <TextField
                                onChange={(e) => setDisplayName(e.target.value)}
                                className={classes.FormTextFields}
                                value={displayName}
                                label="Display name"
                                variant="outlined"
                                color="secondary"
                                fullWidth
                                required
                            />
                            <TextField
                                onChange={(e) => setDescription(e.target.value)}
                                className={classes.FormTextFields}
                                value={description}
                                label="Description"
                                variant="outlined"
                                color="secondary"
                                fullWidth
                                required
                            />
                            <Grid container xs={12} justifyContent={"right"}>
                                <Grid item>
                                    <Button
                                        type="submit"
                                        color="secondary"
                                        variant="contained"
                                        endIcon={<KeyboardArrowRightIcon />}
                                    >
                                        Submit
                                    </Button>
                                </Grid>
                            </Grid>
                        </form>
                    </Grid>
                </Grid>
            </DialogContent>
        </Dialog>
    );
});

interface AddMemberDialogProps {
    group: UserGroup;
    onDismiss: () => void;
    onConfirm: (
        username: string,
        email?: string,
        firstName?: string,
        lastName?: string
    ) => void;
}
const AddMemberDialog = observer((props: AddMemberDialogProps) => {
    /**
     * Component: AddMemberDialog
     *
     */
    // Username is the only required field
    const [username, setUsername] = useState<string | undefined>(undefined);
    const [email, setEmail] = useState<string | undefined>(undefined);
    const [firstName, setFirstName] = useState<string | undefined>(undefined);
    const [lastName, setLastName] = useState<string | undefined>(undefined);
    const classes = useStyles();

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        if (username !== undefined) {
            props.onConfirm(
                username,
                email && (email === "" ? undefined : email),
                firstName && (firstName === "" ? undefined : firstName),
                lastName && (lastName === "" ? undefined : lastName)
            );
        }
        event.preventDefault();
    };

    return (
        <Dialog open={true}>
            <DialogTitle>
                <Grid container xs={12} justifyContent={"space-between"}>
                    <Grid item>Adding member</Grid>
                    <Grid item>
                        <Button
                            color="warning"
                            variant="outlined"
                            onClick={() => props.onDismiss()}
                        >
                            Exit
                        </Button>
                    </Grid>
                </Grid>
            </DialogTitle>
            <DialogContent>
                <Grid container xs={12} rowGap={2} padding={1}>
                    <Grid item xs={12}>
                        <DialogContentText>
                            Enter the details of the user to add
                        </DialogContentText>
                    </Grid>
                    <Grid item xs={12}>
                        <form autoComplete="off" onSubmit={handleSubmit}>
                            <TextField
                                onChange={(e) => setUsername(e.target.value)}
                                className={classes.FormTextFields}
                                label="Username"
                                variant="outlined"
                                color="secondary"
                                fullWidth
                                required
                            />
                            <TextField
                                onChange={(e) => setEmail(e.target.value)}
                                className={classes.FormTextFields}
                                label="Email address"
                                variant="outlined"
                                color="secondary"
                                fullWidth
                            />
                            <TextField
                                onChange={(e) => setFirstName(e.target.value)}
                                className={classes.FormTextFields}
                                label="First name"
                                variant="outlined"
                                color="secondary"
                                fullWidth
                                required={false}
                            />
                            <TextField
                                onChange={(e) => setLastName(e.target.value)}
                                className={classes.FormTextFields}
                                label="Last name"
                                variant="outlined"
                                color="secondary"
                                fullWidth
                                required={false}
                            />
                            <Grid container xs={12} justifyContent={"right"}>
                                <Grid item>
                                    <Button
                                        type="submit"
                                        color="secondary"
                                        variant="contained"
                                        endIcon={<KeyboardArrowRightIcon />}
                                    >
                                        Submit
                                    </Button>
                                </Grid>
                            </Grid>
                        </form>
                    </Grid>
                </Grid>
            </DialogContent>
        </Dialog>
    );
});
interface RemovingMembersDialogProps {
    members: Array<string>;
    onDismiss: () => void;
    onConfirm: () => void;
}
const RemoveMembersDialog = observer((props: RemovingMembersDialogProps) => {
    /**
     * Component: Removing members dialog
     *
     */
    return (
        <Dialog open={true}>
            <DialogTitle>Removing members</DialogTitle>
            <DialogContent>
                <DialogContentText>
                    Are you sure you want to remove the following members?
                </DialogContentText>
                <ul>
                    {props.members.map((username) => (
                        <li key={username}>{username}</li>
                    ))}
                </ul>
            </DialogContent>
            <DialogActions>
                <Grid container justifyContent="space-between" padding={3}>
                    <Grid item>
                        <Button
                            color="success"
                            onClick={props.onDismiss}
                            variant="contained"
                        >
                            Dismiss
                        </Button>
                    </Grid>
                    <Grid item>
                        <Button
                            color="warning"
                            onClick={props.onConfirm}
                            variant="contained"
                        >
                            Confirm
                        </Button>
                    </Grid>
                </Grid>
            </DialogActions>
        </Dialog>
    );
});

interface DeleteGroupDialogProps {
    group: UserGroup;
    onDismiss: () => void;
    onConfirm: () => void;
}
const DeleteGroupDialog = observer((props: DeleteGroupDialogProps) => {
    /**
     * Component: DeleteGroupDialog
     *
     */
    return (
        <Dialog open={true}>
            <DialogTitle>Deleting group</DialogTitle>
            <DialogContent>
                <DialogContentText>
                    Are you sure you want to delete this group with{" "}
                    {props.group.users.length} members?
                </DialogContentText>
            </DialogContent>
            <DialogActions>
                <Grid container justifyContent="space-between" padding={3}>
                    <Grid item>
                        <Button
                            color="success"
                            onClick={props.onDismiss}
                            variant="contained"
                        >
                            Dismiss
                        </Button>
                    </Grid>
                    <Grid item>
                        <Button
                            color="warning"
                            onClick={props.onConfirm}
                            variant="contained"
                        >
                            Confirm
                        </Button>
                    </Grid>
                </Grid>
            </DialogActions>
        </Dialog>
    );
});

interface APIActionPopupProps {
    title: string;
    message: string;
    // It's state is controlled by a parent
    open: boolean;
    error: boolean;
}
const APIActionPopup = observer((props: APIActionPopupProps) => {
    /**
     * Component: SuccessPopup
     *
     */

    return (
        <Collapse in={props.open}>
            <Alert severity={props.error ? "error" : "success"}>
                <AlertTitle>{props.title}</AlertTitle>
                {props.message}
            </Alert>
        </Collapse>
    );
});

interface GroupActionsPanelProps {
    populatedGroup: UserGroup;
    onGroupRemoved: () => void;
    onUserListChange: () => void;
    onGroupMetadataChange: () => void;
    selectedMembers: Array<string>;
}
const GroupActionsPanel = observer((props: GroupActionsPanelProps) => {
    /**
     * Component: GroupActionsPanel
     *
     * Actions:
     *
     * add member
     * remove member(s)
     * update group
     * remove group
     */

    // This needs to be observable
    const [localGroupStore] = useState(() => new GroupStore());

    // State for each action

    // Adding member
    const [addingMember, setAddingMember] = useState<boolean>(false);

    // Removing member(s)
    const [removingMembers, setRemovingMembers] = useState<boolean>(false);

    // updating group new info
    const [updatingGroup, setUpdatingGroup] = useState<boolean>(false);

    // Removing group
    const [removingGroup, setRemovingGroup] = useState<boolean>(false);

    // Action success/failure alert
    // is it showing
    const [alertShowing, setAlertShowing] = useState<boolean>(false);
    // what should it say
    const [alertMessage, setAlertMessage] = useState<string | undefined>(
        undefined
    );
    const [alertTitle, setAlertTitle] = useState<string | undefined>(undefined);
    // was it a success or failure
    const [alertError, setAlertError] = useState<boolean>(false);

    // alert duration
    const successAlertDuration = 3000;
    const errorAlertDuration = 10000;

    // helper to setup alert
    const setupAlert = (
        message: string,
        title: string,
        error: boolean,
        postAction?: () => void
    ) => {
        setAlertMessage(message);
        setAlertTitle(title);
        setAlertError(error);
        setAlertShowing(true);
        setTimeout(
            () => {
                setAlertShowing(false);
                // Optionally run post action if one is provided
                if (postAction !== undefined) {
                    postAction();
                }
            },
            error ? errorAlertDuration : successAlertDuration
        );
    };

    const alertContent: JSX.Element = (
        <React.Fragment>
            <APIActionPopup
                title={alertTitle ?? "API Action Result"}
                message={alertMessage ?? "No message provided"}
                error={alertError}
                open={alertShowing}
            ></APIActionPopup>
        </React.Fragment>
    );

    const updatingGroupDialog: JSX.Element = (
        <React.Fragment>
            {updatingGroup && (
                <GroupMetadataDialog
                    dialogTitle="Updating group"
                    // Provide default values to the form
                    groupMetadata={props.populatedGroup as UserGroupMetadata}
                    new={false}
                    onConfirm={(metadata) => {
                        localGroupStore
                            .updateGroup(metadata)
                            .then((content: UpdateGroupResponse) => {
                                // And show success alert
                                setupAlert(
                                    `Successfully updated group details! Refreshing...`,
                                    "Update completed",
                                    false,
                                    () => {
                                        props.onGroupMetadataChange();
                                    }
                                );
                            })
                            .catch((errorMessage: string) => {
                                // Show failure alert
                                setupAlert(
                                    `Failed to update group. Reason: ${errorMessage}.`,
                                    "An error occurred",
                                    true
                                );
                            })
                            .finally(() => {
                                setUpdatingGroup(false);
                            });
                    }}
                    onDismiss={() => {
                        setUpdatingGroup(false);
                    }}
                ></GroupMetadataDialog>
            )}
        </React.Fragment>
    );

    const removeMembersDialog: JSX.Element = (
        <React.Fragment>
            {removingMembers && (
                <RemoveMembersDialog
                    members={props.selectedMembers}
                    onConfirm={() => {
                        localGroupStore
                            .removeMembers(
                                props.selectedMembers,
                                props.populatedGroup.id
                            )
                            .then((content: RemoveMemberResponse) => {
                                // And show success alert
                                setupAlert(
                                    `Successfully removed selected members! Refreshing user list...`,
                                    "Members removed",
                                    false,
                                    () => {
                                        props.onUserListChange();
                                    }
                                );
                            })
                            .catch((errorMessage: string) => {
                                // Show failure alert
                                setupAlert(
                                    `Failed to remove members. Reason: ${errorMessage}. Some users may have been removed. You may want to refresh the page.`,
                                    "An error occurred",
                                    true
                                );
                            })
                            .finally(() => {
                                setRemovingMembers(false);
                            });
                    }}
                    onDismiss={() => {
                        setRemovingMembers(false);
                    }}
                ></RemoveMembersDialog>
            )}
        </React.Fragment>
    );

    const deleteDialog: JSX.Element = (
        <React.Fragment>
            {removingGroup && (
                <DeleteGroupDialog
                    group={props.populatedGroup}
                    onConfirm={() => {
                        localGroupStore
                            .removeGroup(props.populatedGroup.id)
                            .then((content: RemoveGroupResponse) => {
                                // This will refresh the group list thereby
                                // removing this group, no need for a dialog
                                props.onGroupRemoved();
                            })
                            .catch((errorMessage: string) => {
                                // Show failure alert
                                setupAlert(
                                    `Failed to remove group ${props.populatedGroup.display_name}. Reason: ${errorMessage}.`,
                                    "An error occurred",
                                    true
                                );
                            })
                            .finally(() => {
                                setRemovingGroup(false);
                            });
                    }}
                    onDismiss={() => {
                        setRemovingGroup(false);
                    }}
                ></DeleteGroupDialog>
            )}
        </React.Fragment>
    );

    const addMemberDialog: JSX.Element = (
        <React.Fragment>
            {addingMember && (
                <AddMemberDialog
                    group={props.populatedGroup}
                    onConfirm={(
                        username: string,
                        email?: string,
                        firstName?: string,
                        lastName?: string
                    ) => {
                        localGroupStore
                            .addMember(
                                {
                                    username: username,
                                    email: email,
                                    first_name: firstName,
                                    last_name: lastName,
                                } as GroupUser,
                                props.populatedGroup.id
                            )
                            .then((content: AddMemberResponse) => {
                                // Show success alert
                                setupAlert(
                                    `Successfully added new user with username ${username}. List will be refreshed shortly...`,
                                    "User added",
                                    false,
                                    () => {
                                        props.onUserListChange();
                                    }
                                );
                            })
                            .catch((errorMessage: string) => {
                                // Show failure alert
                                setupAlert(
                                    `Failed to add user. Reason: ${errorMessage}.`,
                                    "An error occurred",
                                    true
                                );
                            })
                            .finally(() => {
                                setAddingMember(false);
                            });
                    }}
                    onDismiss={() => {
                        setAddingMember(false);
                    }}
                ></AddMemberDialog>
            )}
        </React.Fragment>
    );

    return (
        <Grid
            container
            xs={12}
            justifyContent={"space-evenly"}
            rowGap={3}
            padding={1.5}
        >
            {
                // Dialogs
            }
            {deleteDialog}
            {addMemberDialog}
            {removeMembersDialog}
            {updatingGroupDialog}
            {
                // Alert
            }
            {alertContent}
            {
                // manage members
            }
            <Grid item xs={12}>
                <Grid
                    container
                    xs={12}
                    alignItems={"center"}
                    rowGap={2}
                    justifyContent={"space-evenly"}
                >
                    <Grid item xs={12}>
                        <Typography variant="subtitle1" align={"center"}>
                            Manage group members - to remove members, make a
                            selection on the left
                        </Typography>
                    </Grid>
                    <Grid item>
                        <Button
                            variant="contained"
                            onClick={() => {
                                setAddingMember(true);
                            }}
                        >
                            Add member
                        </Button>
                    </Grid>
                    {
                        // Remove members
                    }
                    <Grid item>
                        <Button
                            variant="contained"
                            // Don't show if no users selected
                            disabled={props.selectedMembers.length === 0}
                            onClick={() => {
                                setRemovingMembers(true);
                            }}
                        >
                            Remove members
                        </Button>
                    </Grid>
                </Grid>
            </Grid>
            <Grid item xs={12}>
                <Divider />
            </Grid>

            {
                // manage group
            }
            <Grid item xs={12}>
                <Grid
                    container
                    xs={12}
                    rowGap={2}
                    justifyContent={"space-evenly"}
                >
                    <Grid item xs={12}>
                        <Typography variant="subtitle1" align={"center"}>
                            Manage group metadata
                        </Typography>
                    </Grid>

                    <Grid item>
                        <Button
                            variant="contained"
                            onClick={() => {
                                setUpdatingGroup(true);
                            }}
                        >
                            Update group
                        </Button>
                    </Grid>
                    <Grid item>
                        <Button
                            variant="contained"
                            color="warning"
                            onClick={() => {
                                setRemovingGroup(true);
                            }}
                        >
                            Delete group
                        </Button>
                    </Grid>
                </Grid>
            </Grid>
        </Grid>
    );
});

interface GroupControlProps {}
export const GroupControl = observer((props: GroupControlProps) => {
    /**
     * Component: GroupControl
     *
     */

    // header
    const header = (
        <Grid item xs={12}>
            <Typography variant="h5" align="left">
                Group Management
            </Typography>
        </Grid>
    );

    // body depends on state
    var body: JSX.Element = <React.Fragment>Placeholder</React.Fragment>;

    const [addingGroup, setAddingGroup] = useState<boolean>(false);

    // Fetch the group list
    useEffect(() => {
        if (groupStore.listGroupsAction.awaitingLoad()) {
            groupStore.fetchGroupList();
        }
    }, []);

    // API Alert manager

    // State
    // is it showing
    const [alertShowing, setAlertShowing] = useState<boolean>(false);
    // what should it say
    const [alertMessage, setAlertMessage] = useState<string | undefined>(
        undefined
    );
    const [alertTitle, setAlertTitle] = useState<string | undefined>(undefined);
    // was it a success or failure
    const [alertError, setAlertError] = useState<boolean>(false);

    // alert duration
    const successAlertDuration = 3000;
    const errorAlertDuration = 10000;

    // helper to setup alert
    const setupAlert = (
        message: string,
        title: string,
        error: boolean,
        postAction?: () => void
    ) => {
        setAlertMessage(message);
        setAlertTitle(title);
        setAlertError(error);
        setAlertShowing(true);
        setTimeout(
            () => {
                setAlertShowing(false);
                // Optionally run post action if one is provided
                if (postAction !== undefined) {
                    postAction();
                }
            },
            error ? errorAlertDuration : successAlertDuration
        );
    };

    const alertContent: JSX.Element = (
        <React.Fragment>
            <APIActionPopup
                title={alertTitle ?? "API Action Result"}
                message={alertMessage ?? "No message provided"}
                error={alertError}
                open={alertShowing}
            ></APIActionPopup>
        </React.Fragment>
    );

    // For adding a new group
    const newGroupDialog: JSX.Element = (
        <React.Fragment>
            {addingGroup && (
                <GroupMetadataDialog
                    dialogTitle="New group"
                    new={true}
                    onConfirm={(metadata) => {
                        groupStore
                            .addGroup(metadata)
                            .then((content: AddGroupResponse) => {
                                // And show success alert
                                setupAlert(
                                    `Successfully created new group! Refreshing group list...`,
                                    "Create completed",
                                    false,
                                    () => {
                                        groupStore.fetchGroupList();
                                    }
                                );
                            })
                            .catch((errorMessage: string) => {
                                // Show failure alert
                                setupAlert(
                                    `Failed to create group. Reason: ${errorMessage}.`,
                                    "An error occurred",
                                    true
                                );
                            })
                            .finally(() => {
                                setAddingGroup(false);
                            });
                    }}
                    onDismiss={() => {
                        setAddingGroup(false);
                    }}
                ></GroupMetadataDialog>
            )}
        </React.Fragment>
    );

    // If it failed, display an error
    if (groupStore.listGroupsAction.failed()) {
        body = (
            <Grid container xs={12}>
                An error occurred while loading the groups list. Are you sure
                you have access? Try refreshing. Error info:{" "}
                {groupStore.listGroupsAction.errorMessage ?? "None supplied."}
            </Grid>
        );
    }
    // If groups are loading then return loading symbol
    else if (!groupStore.listGroupsAction.ready()) {
        body = (
            <Grid container xs={12} justifyContent={"center"}>
                <Grid item>
                    <CircularProgress />
                </Grid>
            </Grid>
        );
    } else {
        const groupList = groupStore.listGroupsAction.content?.groups;
        body = groupList ? (
            <Grid container xs={12} padding={2} rowGap={1}>
                <Grid item xs={12}>
                    {newGroupDialog}
                    {alertContent}
                </Grid>
                <Grid item xs={12}>
                    <Grid
                        container
                        xs={12}
                        alignContent={"bottom"}
                        justifyContent={"left"}
                        spacing={2}
                    >
                        <Grid item>
                            <IconButton
                                size="large"
                                onClick={() => {
                                    setAddingGroup(true);
                                }}
                                color="success"
                            >
                                <AddIcon fontSize="large" />
                            </IconButton>
                        </Grid>
                        <Grid item>
                            <Grid item xs={12}>
                                <Typography variant="h6">Groups</Typography>
                            </Grid>
                            <Grid item xs={12}>
                                <Typography variant="body1">
                                    You can see a list of groups below. Click to
                                    expand each group and perform management
                                    actions.
                                </Typography>
                            </Grid>
                        </Grid>
                    </Grid>
                </Grid>
                <Grid container xs={12} rowGap={1} padding={1}>
                    {groupList.map((group) => {
                        return (
                            <React.Fragment>
                                <GroupItem
                                    group={group}
                                    onGroupRemoved={() => {
                                        // If the group is removed, refresh the
                                        // group list
                                        groupStore.fetchGroupList();
                                    }}
                                    onMetadataChange={() => {
                                        // Refresh the group list if the metadata is updated
                                        groupStore.fetchGroupList();
                                    }}
                                ></GroupItem>
                                <Grid item xs={12}>
                                    <Divider />
                                </Grid>
                            </React.Fragment>
                        );
                    })}
                </Grid>
            </Grid>
        ) : (
            <React.Fragment>
                An error occurred loading the group list, try refreshing or
                contact an admin.
            </React.Fragment>
        );
    }

    return (
        <Grid container xs={12} rowGap={2}>
            {header}
            {body}
        </Grid>
    );
});
