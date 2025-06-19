import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import LaunchIcon from "@mui/icons-material/Launch";
import {
  Button,
  Grid,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import React, { useState } from "react";
import { hdlPrefix } from "../config";
import { useTypedLoadedItem } from "../hooks";
import { ItemBase, ItemSubType } from "../provena-interfaces/RegistryModels";
import { REGISTRY_LINK } from "../queries";
import { mapSubTypeToPrettyName } from "../util/subtypeStyling";
import { generateRegistryDeepLink } from "../util/util";
import {
  registryHelpLink,
  SearchSelectorComponent,
} from "./SubtypeSearchOrManualFormOverride";

export interface SubtypeSearchSelectorProps {
  required: boolean;
  title: string;
  description: string;
  subtypePlural: string;
  selectedId: string | undefined;
  setSelectedId: (id: string | undefined) => void;
  // What subtype?
  subtype: ItemSubType;
  // Should the title persist after selection?
  persistTitle?: boolean;
}

// Styles for downshift menu are modified based on content from
// https://www.digitalocean.com/community/tutorials/how-to-use-downshift-in-common-dropdown-use-cases
const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    helperText: {
      marginLeft: 0,
    },
    clearButton: {
      "margin-bottom": theme.spacing(2),
      "margin-top": theme.spacing(2),
    },
    input: {
      margin: "1rem",
      width: "20rem",
      padding: "1rem .5rem",
    },
    // The overall search dropdown Div
    downshiftDropdown: {
      margin: "0 auto",
      width: "100%",
      border: "1px solid whitesmoke",
      borderBottom: "none",
    },
    // A child item of the dropdown
    dropdownItem: {
      padding: "0.5rem",
      cursor: "pointer",
      borderBottom: "1px solid whitesmoke",
      fontSize: "1rem",
      textAlign: "left",
      width: "100%",
    },
  })
);

export const SubtypeSearchSelector = (props: SubtypeSearchSelectorProps) => {
  const classes = useStyles();

  // Is the input confirmed?
  const selectionMade: boolean = !!props.selectedId && props.selectedId !== "";

  // Description from schema with default fall through
  const { title, description } = props;

  // Has the user entered a manual term?
  const [manualInput, setManualInput] = useState<string>("");

  // Pretty name for subtype
  const subtypeName = mapSubTypeToPrettyName(props.subtype);
  const exploreDeepLink = generateRegistryDeepLink(props.subtype);

  // This is the header content which is always present whether search is
  // used or not
  const headerContent = (
    <Grid container justifyContent="space-between" alignItems="center">
      <Grid item xs={7}>
        <Stack spacing={1}>
          <Typography variant="h6">
            {title + (props.required ? "*" : "")}
          </Typography>
          <Typography variant="subtitle1">{description}</Typography>
        </Stack>
      </Grid>
      <Grid item>
        <Button
          onClick={() => {
            // Clear the selection
            window.open(exploreDeepLink, "_blank", "noopener,noreferrer");
          }}
          variant="outlined"
        >
          Explore {props.subtypePlural} in the Registry
          <LaunchIcon style={{ marginLeft: "10px" }} />
        </Button>
      </Grid>
    </Grid>
  );

  // This is the loaded data for selected item - whether through search or
  // manually

  // If the value is selected, show the following content
  // Make sure we have loaded the item based on ID
  const loadedItem = useTypedLoadedItem({
    id: props.selectedId,
    subtype: props.subtype,
  });

  const typedItem =
    loadedItem.data?.item !== undefined
      ? (loadedItem.data?.item as ItemBase)
      : undefined;

  // parse the display name contents
  const itemDisplayNameContents = loadedItem.loading
    ? "Loading item..."
    : loadedItem.error
    ? `An error occurred while loading the ${subtypeName}. Error: ${
        loadedItem.errorMessage ?? "Unknown error..."
      }.`
    : typedItem?.display_name ?? "Unknown name...";

  const itemLoadedSuccessfully =
    !loadedItem.error && loadedItem.data !== undefined;

  // The following is shown when the user has made a selection - either
  // through search or manually - contains error fallback for the loaded
  // item
  const selectionContent = (
    <Stack>
      <p>
        Selected {subtypeName}: {itemDisplayNameContents} (
        <a href={hdlPrefix + props.selectedId} target="_blank" rel="noreferrer">
          <b>{props.selectedId}</b>
        </a>
        ){" "}
        {itemLoadedSuccessfully && (
          <Tooltip title={"Successfully fetched item from the Registry"}>
            <CheckCircleIcon style={{ color: "green" }} />
          </Tooltip>
        )}
        {loadedItem.error && (
          <p>
            {" "}
            Please ensure that selected ID is a valid, registered {subtypeName}.
            You can learn more about the registry{" "}
            <a href={registryHelpLink} target="_blank" rel="noreferrer">
              here
            </a>
            .
          </p>
        )}
      </p>
      <Stack direction="row" spacing={2} alignItems="center" padding={0}>
        <Button
          className={classes.clearButton}
          variant="outlined"
          color="secondary"
          onClick={() => {
            // Clear the selection
            window.open(
              REGISTRY_LINK + "/item/" + props.selectedId,
              "_blank",
              "noopener,noreferrer"
            );
          }}
        >
          view in registry <LaunchIcon style={{ marginLeft: "10px" }} />
        </Button>
        <Button
          className={classes.clearButton}
          variant="outlined"
          color="warning"
          onClick={() => {
            // Clear the selection
            props.setSelectedId(undefined);
          }}
        >
          Clear Selection
        </Button>
      </Stack>
    </Stack>
  );

  const searchSelectContent = (
    // Otherwise include a mention here that the publisher needs to be selected
    <React.Fragment>
      <Grid
        container
        justifyContent="space-evenly"
        alignItems="flex-start"
        spacing={2}
      >
        <Grid item flexGrow={1.5}>
          {
            // Search
            // Uses downshift - see https://www.downshift-js.com/
          }
          <SearchSelectorComponent
            selection={props.selectedId}
            subtype={props.subtype}
            setSelection={props.setSelectedId}
          />
        </Grid>
        <Grid item>
          <p>Or</p>
        </Grid>
        <Grid item flexGrow={1}>
          {
            // Select manually
          }
          <Stack direction="row" spacing={2} alignItems="center">
            <TextField
              fullWidth
              onChange={(e) => {
                setManualInput(e.target.value);
              }}
              value={manualInput}
              // Catch the enter key to quickly submit manual
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  // avoid firing to parent
                  e.preventDefault();
                  // Submit contents
                  props.setSelectedId(manualInput);
                }
              }}
              label={`Manually enter the ID of a ${subtypeName}`}
            />
            <Button
              variant={"contained"}
              onClick={(e) => {
                props.setSelectedId(manualInput);
              }}
            >
              Submit
            </Button>
          </Stack>
        </Grid>
      </Grid>
    </React.Fragment>
  );

  return (
    <Stack spacing={1.5}>
      {headerContent}
      {selectionMade ? selectionContent : searchSelectContent}
    </Stack>
  );
};
