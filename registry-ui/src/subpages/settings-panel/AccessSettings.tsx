import AddIcon from "@mui/icons-material/Add";
import ClearIcon from "@mui/icons-material/Clear";
import EditIcon from "@mui/icons-material/Edit";
import {
    Button,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    Grid,
    IconButton,
    Stack,
    Switch,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";
import {
    DOCUMENTATION_BASE_URL,
    fetchAuthConfiguration,
    fetchAvailableRoles,
    fetchGroupList,
    fetchUserGroups,
    updateAuthConfiguration,
} from "react-libs";
import { SuccessPopup } from "../../components/Popups";
import { UserGroupMetadata } from "../../shared-interfaces/AuthAPI";
import {
    AccessSettings,
    DescribedRole,
    ItemSubType,
} from "../../shared-interfaces/RegistryModels";

import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import {
    DataGrid,
    GridColDef,
    GridRowsProp,
    GridSelectionModel,
} from "@mui/x-data-grid";
import { useKeycloak } from "@react-keycloak/web";
import isEqual from "lodash.isequal";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        selectGroupDialog: {
            maxHeight: "80vh",
            minHeight: "70vh",
        },
    })
);

const rolesPrettyPrint = (roles: string[]): string => {
    return roles.join(", ");
};

interface RolesSelectorProps {
    availableRoles: DescribedRole[];
    roles: string[];
    setRoles: (roles: string[]) => void;
}
const RolesSelector = observer((props: RolesSelectorProps) => {
    /**
    Component: RolesSelector

    Displays a set of selectable roles from a provided list of available
    described roles.
    */
    return (
        <Table>
            <TableHead>
                <TableRow key="header">
                    <TableCell key="Access Type">Role Name</TableCell>
                    <TableCell key="Description">Description</TableCell>
                    <TableCell key="Granted">Granted</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {props.availableRoles.map((describedRole: DescribedRole) => {
                    const granted =
                        props.roles.indexOf(describedRole.role_name) !== -1;
                    return (
                        <TableRow key={describedRole.role_name}>
                            <TableCell>
                                <b>{describedRole.role_display_name}</b>
                            </TableCell>
                            <TableCell>{describedRole.description}</TableCell>
                            <TableCell>
                                <Switch
                                    checked={granted}
                                    onChange={() => {
                                        if (granted) {
                                            // if currently granted, remove

                                            // copy to make a new reference
                                            const newList: string[] =
                                                JSON.parse(
                                                    JSON.stringify(props.roles)
                                                );

                                            // remove the role name
                                            newList.splice(
                                                newList.indexOf(
                                                    describedRole.role_name
                                                ),
                                                1
                                            );

                                            // update
                                            props.setRoles(newList);
                                        } else {
                                            // if not granted, add

                                            // copy to make a new reference
                                            const newList: string[] =
                                                JSON.parse(
                                                    JSON.stringify(props.roles)
                                                );

                                            // push the role name
                                            newList.push(
                                                describedRole.role_name
                                            );

                                            // update
                                            props.setRoles(newList);
                                        }
                                    }}
                                />
                            </TableCell>
                        </TableRow>
                    );
                })}
            </TableBody>
        </Table>
    );
});

interface GeneralAccessProps {
    itemSubtype: ItemSubType;
    roles: string[];
    availableRoles: DescribedRole[];
    setRoles: (roles: string[]) => void;
}
const GeneralAccess = observer((props: GeneralAccessProps) => {
    /**
    Component: GeneralAccess

    Displays and allows modification of the selected general access roles
    */
    const helpLink = DOCUMENTATION_BASE_URL + "/registry/access-control.html";
    return (
        <div style={{ width: "100%" }}>
            <Stack direction="column" spacing={2}>
                <Typography variant={"h5"}>General Access</Typography>
                <Typography variant={"subtitle1"}>
                    Select which roles are granted to all users of the Registry
                    for this resource. For more information, visit{" "}
                    <a href={helpLink} target="_blank" rel="noreferrer">
                        the documentation
                    </a>
                    .
                </Typography>
                <RolesSelector
                    roles={props.roles}
                    setRoles={props.setRoles}
                    availableRoles={props.availableRoles}
                />
            </Stack>
        </div>
    );
});

interface GroupsListDisplayProps {
    // Make the selection
    submitSelection: (groups: string[]) => void;
    // available groups
    userGroupMetadata: UserGroupMetadata[];
    // User group list
    userGroups: UserGroupMetadata[];
}
interface DataGridGroupItem {
    id: string;
    display_name: string;
    description: string;
    is_member: boolean;
}

const GroupsListDisplay = observer((props: GroupsListDisplayProps) => {
    /**
     * Component: GroupsListDisplay
     *
     */
    const defaultRowsPerPage = 5;
    const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);
    const [selectionModel, setSelectionModel] = useState<GridSelectionModel>(
        []
    );
    const [onlyMyGroups, setOnlyMyGroups] = useState<boolean>(false);

    const displayGroupList = (
        groups: Array<UserGroupMetadata>,
        userGroups: Array<UserGroupMetadata>
    ) => {
        const isMember = (id: string) => {
            var found = false;
            for (const g of userGroups) {
                if (g.id === id) {
                    found = true;
                    break;
                }
            }
            return found;
        };
        const rows: GridRowsProp = groups
            // Make a standard interface from group items and pull out
            // membership
            .map((group) => {
                return {
                    id: group.id,
                    display_name: group.display_name,
                    description: group.description,
                    is_member: isMember(group.id),
                } as DataGridGroupItem;
            })
            // If only my group is applied then filter the items based on this
            .filter((group) => {
                if (onlyMyGroups) {
                    return group.is_member;
                } else {
                    return true;
                }
            });
        const columns: GridColDef[] = [
            { field: "display_name", headerName: "Name", flex: 0.2 },
            { field: "description", headerName: "Description", flex: 0.6 },
            { field: "is_member", headerName: "Membership", flex: 0.2 },
        ];

        return (
            <div style={{ height: 400, width: "100%" }}>
                <Grid
                    container
                    spacing={2}
                    alignItems={"center"}
                    justifyContent={"left"}
                >
                    <Grid item>Only show groups I am in?</Grid>
                    <Grid item>
                        <Switch
                            checked={onlyMyGroups}
                            onChange={() => {
                                setOnlyMyGroups(!onlyMyGroups);
                            }}
                        />
                    </Grid>
                </Grid>
                <DataGrid
                    pageSize={pageSize}
                    rowsPerPageOptions={[5, 10, 20]}
                    columns={columns}
                    rows={rows}
                    onPageSizeChange={(size) => {
                        setPageSize(size);
                    }}
                    checkboxSelection
                    onSelectionModelChange={(newSelectionModel) => {
                        setSelectionModel(newSelectionModel);
                        props.submitSelection(
                            newSelectionModel as Array<string>
                        );
                    }}
                    selectionModel={selectionModel}
                ></DataGrid>
            </div>
        );
    };

    return displayGroupList(props.userGroupMetadata, props.userGroups);
});

interface GroupSelectorDialogProps {
    // list of new group Ids
    submitSelection: (groups: string[]) => void;
    // available groups
    userGroupMetadata: UserGroupMetadata[];
    // user groups
    userGroups: UserGroupMetadata[];
    // close dialog function - map to close buttons
    handleClose: () => void;
}

const GroupSelectorDialog = observer((props: GroupSelectorDialogProps) => {
    /**
     * Component: GroupSelectorDialog
     *
     */
    const [selections, setSelections] = useState<Array<string>>([]);

    const classes = useStyles();

    return (
        <Dialog
            open={true}
            onClose={props.handleClose}
            fullWidth={true}
            maxWidth={"md"}
            // thanks to https://stackoverflow.com/a/47763027
            classes={{ paper: classes.selectGroupDialog }}
        >
            <DialogTitle>Select groups</DialogTitle>
            <DialogContent>
                <DialogContentText>
                    Please choose a selection of groups from the below list.
                </DialogContentText>
                <GroupsListDisplay
                    submitSelection={(groups: Array<string>) => {
                        setSelections(groups);
                    }}
                    userGroups={props.userGroups}
                    userGroupMetadata={props.userGroupMetadata}
                ></GroupsListDisplay>
            </DialogContent>
            <DialogActions>
                <Button onClick={props.handleClose}>Cancel</Button>
                <Button
                    color="success"
                    disabled={selections.length === 0}
                    onClick={() => {
                        if (selections.length > 0) {
                            props.submitSelection(selections);
                            props.handleClose();
                        }
                    }}
                >
                    Submit
                </Button>
            </DialogActions>
        </Dialog>
    );
});

interface EditGroupPermissionDialogProps {
    group: UserGroupMetadata;
    selectedRoles: string[];
    availableRoles: DescribedRole[];
    confirmHandler: (roles: string[]) => void;
    closeHandler: () => void;
}
const EditGroupPermissionDialog = observer(
    (props: EditGroupPermissionDialogProps) => {
        /**
    Component: EditGroupPermissionDialog

    Shows a dialog which allows the modification of selected roles for a group.   
    */

        // Keep an updated list - then update on confirm
        const [updatedRoles, setUpdatedRoles] = useState<string[]>(
            props.selectedRoles
        );
        return (
            <Dialog
                open={true}
                onClose={props.closeHandler}
                fullWidth={true}
                maxWidth={"md"}
            >
                <DialogTitle>Modify Group Permissions</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        You can use the sliders below to choose which roles are
                        granted to users within this group for the current
                        resource.
                    </DialogContentText>
                    <RolesSelector
                        availableRoles={props.availableRoles}
                        roles={updatedRoles}
                        setRoles={setUpdatedRoles}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={props.closeHandler}>Cancel</Button>
                    <Button
                        color="success"
                        onClick={() => {
                            props.confirmHandler(updatedRoles);
                        }}
                    >
                        Submit
                    </Button>
                </DialogActions>
            </Dialog>
        );
    }
);

interface GroupAccessProps {
    itemSubtype: ItemSubType;
    groupMetadata: UserGroupMetadata[];
    userGroups: UserGroupMetadata[];
    groups: { [k: string]: string[] };
    availableRoles: DescribedRole[];
    setGroups: (groups: { [k: string]: string[] }) => void;
}
const GroupAccess = observer((props: GroupAccessProps) => {
    /**
    Component: GroupAccess

    Displays and allows modification of the selected group access roles
    
    */

    // styles
    const classes = useStyles();

    // Derive the selected groups as a list to map through
    const selectedGroups: string[] = Object.keys(props.groups);

    // State
    const [selectingGroupDialog, setSelectingGroupDialog] =
        useState<boolean>(false);

    const [editingGroupDialog, setEditingGroupDialog] =
        useState<boolean>(false);
    const [editingGroupId, setEditingGroupId] = useState<string | undefined>(
        undefined
    );

    // Handlers

    const removeGroupHandler = (groupId: string): void => {
        // Create a new groups reference
        const newGroups = JSON.parse(JSON.stringify(props.groups));

        // Remove the group by ID
        delete newGroups[groupId];

        // Update
        props.setGroups(newGroups);
    };

    const addGroupsHandler = (groupIds: string[]): void => {
        // Create a new groups reference
        const newGroups = JSON.parse(JSON.stringify(props.groups));

        // Add the group by Id - empty role list by default
        const currentGroups = Object.keys(props.groups);
        groupIds.forEach((id: string) => {
            // only add if not already present
            if (currentGroups.indexOf(id) === -1) {
                newGroups[id] = [];
            }
        });

        // Update
        props.setGroups(newGroups);
    };

    const handleGroupRolesChange = (groupId: string, roles: string[]): void => {
        // Create a new groups reference
        const newGroups = JSON.parse(JSON.stringify(props.groups));

        // Replace the roles for specified group
        newGroups[groupId] = JSON.parse(JSON.stringify(roles));

        // Update
        props.setGroups(newGroups);
    };

    return (
        <div style={{ width: "100%" }}>
            {
                // Are we selecting a group? Show dialog
            }
            {selectingGroupDialog && (
                <GroupSelectorDialog
                    submitSelection={addGroupsHandler}
                    userGroupMetadata={props.groupMetadata.filter(
                        (group: UserGroupMetadata) => {
                            // only include groups in selector which are not
                            // already present in the groups configuration
                            const currentGroups = Object.keys(props.groups);
                            return currentGroups.indexOf(group.id) === -1;
                        }
                    )}
                    userGroups={props.userGroups}
                    handleClose={() => {
                        setSelectingGroupDialog(false);
                    }}
                />
            )}
            {
                // Are we editing a group permission set? Show dialog
            }
            {editingGroupDialog && (
                <EditGroupPermissionDialog
                    group={
                        props.groupMetadata.find((g: UserGroupMetadata) => {
                            return g.id === editingGroupId!;
                        }) ??
                        ({
                            id: "error",
                            display_name: "error",
                            description: "error",
                        } as UserGroupMetadata)
                    }
                    selectedRoles={props.groups[editingGroupId!]}
                    availableRoles={props.availableRoles}
                    confirmHandler={(roles: string[]) => {
                        handleGroupRolesChange(editingGroupId!, roles);
                        setEditingGroupDialog(false);
                        setEditingGroupId(undefined);
                    }}
                    closeHandler={() => {
                        setEditingGroupDialog(false);
                        setEditingGroupId(undefined);
                    }}
                />
            )}
            {
                // Table and heading
            }
            <Stack direction="column" spacing={2}>
                <Typography variant={"h5"}>Group Access</Typography>
                <Typography variant={"subtitle1"}>
                    Use the table below to specify roles for this resource on a
                    per-group basis.
                </Typography>
                <Table>
                    <TableHead>
                        <TableRow key="header">
                            <TableCell key="Group Name">Group Name</TableCell>
                            <TableCell key="Description">Description</TableCell>
                            <TableCell key="Roles">Roles</TableCell>
                            <TableCell key="Edit"></TableCell>
                            <TableCell key="Clear"></TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {selectedGroups.map((groupId: string) => {
                            const roles: string[] = props.groups[groupId];
                            const metadata: UserGroupMetadata | undefined =
                                props.groupMetadata.find(
                                    (metadata: UserGroupMetadata) => {
                                        return metadata.id === groupId;
                                    }
                                );

                            return (
                                <TableRow key={groupId}>
                                    {
                                        // Group name
                                    }
                                    <TableCell>
                                        {metadata?.display_name ?? "Error"}
                                    </TableCell>
                                    {
                                        // Group description
                                    }
                                    <TableCell>
                                        {metadata?.description ?? "Error"}
                                    </TableCell>
                                    {
                                        // Granted roles
                                    }
                                    <TableCell>
                                        {roles.length === 0
                                            ? "None"
                                            : rolesPrettyPrint(roles)}
                                    </TableCell>
                                    {
                                        // Edit button
                                    }
                                    <TableCell>
                                        <IconButton
                                            disabled={editingGroupDialog}
                                            onClick={() => {
                                                if (!editingGroupDialog) {
                                                    setEditingGroupId(groupId);
                                                    setEditingGroupDialog(true);
                                                }
                                            }}
                                            size="large"
                                        >
                                            <EditIcon />
                                        </IconButton>
                                    </TableCell>
                                    <TableCell>
                                        <IconButton
                                            onClick={() => {
                                                removeGroupHandler(groupId);
                                            }}
                                            size="large"
                                            color={"warning"}
                                        >
                                            <ClearIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                        <TableRow key={"add group"}>
                            {
                                // Group name
                            }
                            <TableCell colSpan={4} />
                            {
                                // Add new group button
                            }
                            <TableCell>
                                <IconButton
                                    disabled={selectingGroupDialog}
                                    onClick={() => {
                                        setSelectingGroupDialog(true);
                                    }}
                                    size="large"
                                    color={"success"}
                                >
                                    <AddIcon />
                                </IconButton>
                            </TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </Stack>
        </div>
    );
});

const compareAccessSettings = (
    oldSettings: AccessSettings,
    newSettings: AccessSettings
): boolean => {
    return !isEqual(oldSettings, newSettings);
};

interface UpdateAuthConfigurationProps {
    id: string;
    newSettings: AccessSettings;
    oldSettings: AccessSettings;
    itemSubtype: ItemSubType;
    onSuccessfulUpdate: (settings: AccessSettings) => void;
    onClear: () => void;
}
const UpdateAuthConfiguration = observer(
    (props: UpdateAuthConfigurationProps) => {
        /**
        Component: UpdateAuthConfiguration

        Conditionally displays a popup which allows the user to submit the changes.
        */

        const difference = compareAccessSettings(
            props.newSettings,
            props.oldSettings
        );

        const [submitting, setSubmitting] = useState<boolean>(false);
        const [updateQK, setUpdateQK] = useState<string>("updateauth");
        const [successPopup, setSuccessPopup] = useState<boolean>(false);
        const popupDuration = 3000;

        // Pending query for update - only submitted when enabled
        const { isSuccess, isFetching, isError, error } = useQuery({
            queryKey: [updateQK],
            queryFn: () => {
                return updateAuthConfiguration(
                    props.id,
                    props.itemSubtype,
                    props.newSettings
                );
            },
            onSuccess: (res) => {
                // Start popup
                setSuccessPopup(true);

                // Timeout popup
                setTimeout(() => {
                    // Dismiss popup
                    setSuccessPopup(false);
                    // Alert parent causing refreshing
                    props.onSuccessfulUpdate(props.newSettings);
                }, popupDuration);
            },
            enabled: submitting,
        });

        if (successPopup) {
            return (
                <div style={{ width: "100%" }}>
                    <SuccessPopup
                        title={"Update Successful"}
                        message={
                            "Access settings were successfully updated! Refreshing..."
                        }
                        open={successPopup}
                    />
                </div>
            );
        }
        if (!difference) {
            return null;
        }

        if (submitting) {
            if (isError) {
                return (
                    <Grid
                        container
                        justifyContent="center"
                        style={{
                            padding: 25,
                        }}
                        sx={{
                            border: 5,
                            borderColor: "red",
                        }}
                    >
                        <Grid
                            xs={12}
                            sx={{
                                marginBottom: 3,
                            }}
                        >
                            <Typography variant="body1" align="center">
                                An error occurred while submitting your updated
                                access permissions. The error was:{" "}
                                {error ?? "Unknown"}. Try refreshing the page or
                                run the update again. Hit dismiss below to hide
                                this message.
                            </Typography>
                        </Grid>
                        <Grid>
                            <Button
                                variant="contained"
                                onClick={() => {
                                    setSubmitting(false);
                                }}
                            >
                                Dismiss error
                            </Button>
                        </Grid>
                    </Grid>
                );
            } else {
                // In progress on submission
                return <p>Submitting</p>;
            }
        }

        // Otherwise - there is a difference
        return (
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
                    <Stack direction="column" spacing={2}>
                        <Typography variant="h5" align="center">
                            Submit your access changes by pressing the button
                            below, or revert your changes.
                        </Typography>
                        {props.itemSubtype === "DATASET" && (
                            <Typography variant="subtitle1" align="left">
                                Before submitting this access change, please
                                determine if there are any ethics, privacy or
                                Indigenous knowledge considerations for this
                                dataset. Ensure only appropriate users will be
                                granted access.
                            </Typography>
                        )}
                    </Stack>
                </Grid>
                <Grid container xs={12} spacing={2} justifyContent={"center"}>
                    <Grid item>
                        <Button
                            variant="contained"
                            color="warning"
                            onClick={props.onClear}
                        >
                            Revert changes
                        </Button>
                    </Grid>
                    <Grid item>
                        <Button
                            variant="contained"
                            color="success"
                            onClick={() => {
                                // Update the unique query key
                                setUpdateQK("updateauth" + Date.now());
                                // Start the query
                                setSubmitting(true);
                            }}
                        >
                            Submit changes
                        </Button>
                    </Grid>
                </Grid>
            </Grid>
        );
    }
);

const copyAuthConfiguration = (old: AccessSettings): AccessSettings => {
    return JSON.parse(JSON.stringify(old)) as AccessSettings;
};

interface AccessControlProps {
    id: string;
    itemSubtype: ItemSubType;
}
export const AccessControl = observer((props: AccessControlProps) => {
    /**
    Component: AccessControl
    
    */

    // Auth info
    const { keycloak } = useKeycloak();
    const username = keycloak.tokenParsed?.preferred_username;

    // standard state
    // --------------
    const [proposedAuthConfiguration, setProposedAuthConfiguration] = useState<
        AccessSettings | undefined
    >(undefined);

    // expander
    const [expanded, setExpanded] = useState<boolean>(false);

    // required dynamic fetched state
    // ------------------------------

    // current auth configuration
    const {
        isSuccess: getAuthConfigSuccess,
        isFetching: getAuthConfigFetching,
        data: getAuthConfigData,
        isError: getAuthConfigIsError,
        error: getAuthConfigError,
        refetch: getAuthConfigRefetch,
    } = useQuery({
        queryKey: [props.id + "fetchauthconfig"],
        queryFn: () => {
            return fetchAuthConfiguration(props.id, props.itemSubtype);
        },
        onSuccess: (data: AccessSettings) => {
            setProposedAuthConfiguration(data);
        },
    });

    // groups list
    const groupsCacheTimeout = 30 * 1000; // 30s
    const {
        isSuccess: groupsListSuccess,
        isFetching: groupsListFetching,
        data: groupsListData,
        isError: groupsListIsError,
        error: groupsListError,
    } = useQuery({
        queryKey: [props.id + "fetchgroupslist"],
        queryFn: () => {
            return fetchGroupList();
        },
        staleTime: groupsCacheTimeout,
    });

    // user groups
    const userGroupsTimeout = 30 * 1000; // 30s
    const {
        isSuccess: userGroupsSuccess,
        isFetching: userGroupsFetching,
        data: userGroupsData,
        isError: userGroupsIsError,
        error: userGroupsError,
    } = useQuery({
        queryKey: [props.id + "fetchusergroups"],
        queryFn: () => {
            return fetchUserGroups();
        },
        staleTime: userGroupsTimeout,
    });

    // available roles - cache this
    const rolesCacheTimeout = 120 * 1000; // 120s
    const {
        isSuccess: availableRolesSuccess,
        isFetching: availableRolesFetching,
        data: availableRolesData,
        isError: availableRolesIsError,
        error: availableRolesError,
    } = useQuery({
        queryKey: [props.id + "fetchavailableroles"],
        queryFn: () => {
            return fetchAvailableRoles(props.itemSubtype);
        },
        staleTime: rolesCacheTimeout,
    });

    // States
    // ------

    // Loading
    const loading =
        getAuthConfigFetching ||
        groupsListFetching ||
        userGroupsFetching ||
        availableRolesFetching;

    // An error occurred
    const isError =
        groupsListIsError ||
        userGroupsIsError ||
        getAuthConfigIsError ||
        availableRolesIsError;

    // The error message (if any)
    const errorMessage: string | undefined =
        (groupsListError as string | undefined) ||
        (userGroupsError as string | undefined) ||
        (availableRolesError as string | undefined) ||
        (getAuthConfigError as string | undefined);

    // Handle non standard states
    // --------------------------

    if (loading) {
        return <CircularProgress />;
    }

    if (isError) {
        return <p>An error occurred. Message: {errorMessage ?? "Unknown."}</p>;
    }

    const headerContent = (
        <Grid
            container
            xs={12}
            alignItems={"center"}
            justifyContent={"flex-start"}
            spacing={2}
        >
            <Grid item>
                <h2>Access Control</h2>
            </Grid>
            <Grid item>
                <IconButton size="small" onClick={() => setExpanded(!expanded)}>
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
            </Grid>
            <Grid item xs={12}>
                Provides controls over who can see or edit the metadata and data
                of your resource. {expanded ? "" : "Expand to see more."}
            </Grid>
        </Grid>
    );

    var bodyContent = <React.Fragment></React.Fragment>;

    if (expanded) {
        bodyContent = (
            <React.Fragment>
                <div style={{ minWidth: "100%", width: "100%" }}>
                    <UpdateAuthConfiguration
                        id={props.id}
                        itemSubtype={props.itemSubtype}
                        oldSettings={getAuthConfigData!}
                        newSettings={proposedAuthConfiguration!}
                        onClear={() => {
                            setProposedAuthConfiguration(
                                JSON.parse(JSON.stringify(getAuthConfigData!))
                            );
                        }}
                        onSuccessfulUpdate={() => {
                            getAuthConfigRefetch();
                        }}
                    />
                    <Stack spacing={3} style={{ width: "100%" }}>
                        <h3>
                            Owner username: {getAuthConfigData!.owner}
                            {getAuthConfigData!.owner === username
                                ? " (You)"
                                : ""}
                        </h3>

                        <GeneralAccess
                            itemSubtype={props.itemSubtype}
                            availableRoles={availableRolesData!.roles!}
                            roles={proposedAuthConfiguration?.general || []}
                            setRoles={(roles: string[]) => {
                                const newConfiguration = copyAuthConfiguration(
                                    proposedAuthConfiguration!
                                );
                                newConfiguration.general = roles;
                                setProposedAuthConfiguration(newConfiguration);
                            }}
                        ></GeneralAccess>
                        <GroupAccess
                            itemSubtype={props.itemSubtype}
                            groupMetadata={groupsListData!.groups!}
                            availableRoles={availableRolesData!.roles!}
                            userGroups={userGroupsData!.groups!}
                            groups={proposedAuthConfiguration?.groups || {}}
                            setGroups={(groups: { [k: string]: string[] }) => {
                                const newConfiguration = copyAuthConfiguration(
                                    proposedAuthConfiguration!
                                );
                                newConfiguration.groups = groups;
                                setProposedAuthConfiguration(newConfiguration);
                            }}
                        ></GroupAccess>
                    </Stack>
                </div>
            </React.Fragment>
        );
    }

    // Handle normal case once all data is retrieved
    // All data can be assumed to be present at this point
    return (
        <Stack>
            {headerContent}
            {bodyContent}
        </Stack>
    );
});
