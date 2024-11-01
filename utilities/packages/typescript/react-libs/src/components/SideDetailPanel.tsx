import createStyles from "@mui/styles/createStyles";
import React, { useState } from "react";
import makeStyles from "@mui/styles/makeStyles";
import ClearIcon from "@mui/icons-material/Clear";
import { Theme } from "@mui/material/styles";
import {
  Button,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  Menu,
  MenuItem,
  Select,
  SelectChangeEvent,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import LaunchIcon from "@mui/icons-material/Launch";
import { FileDownload } from "@mui/icons-material";
import { REGISTRY_LINK } from "../queries";
import { useCombinedLoadedItem } from "../hooks";
import { ItemDisplayWithStatusComponent } from "./ItemDisplayWithStatus";
import { ExpansionArray, GraphExploreQueries } from "../hooks/useProvGraphData";
import HelpOutline from "@mui/icons-material/HelpOutline";
import { useGenerateReportDialog } from "../hooks/useGenerateReportDialog";
import { ItemSubType } from "../provena-interfaces/RegistryModels";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    detailPanel: {
      overflowY: "scroll",
      height: "100%",
      wordBreak: "break-all",
      wordWrap: "break-word",
      border: "1px dotted " + theme.palette.primary.light,
      borderRadius: "10px",
      marginLeft: theme.spacing(1),
      padding: "12px 6px 12px 12px",
    },
    queryPopup: {
      backgroundColor: "#f5f5f9",
      color: "rgba(0, 0, 0, 0.87)",
      maxWidth: 220,
      fontSize: theme.typography.pxToRem(12),
      border: "1px solid #dadde9",
    },
    titleBar: {
      display: "flex",
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "end",
      width: "100%",
    },
    buttonsBar: {
      display: "flex",
      flexDirection: "row",
      justifyContent: "space-between",
      width: "100%",
      paddingBottom: theme.spacing(1),
    },
    buttons: {
      width: "100%",
    },
    selectionFormControl: {
      width: "100%",
      color: theme.palette.primary.main,
    },
    selectRoot: {
      display: "flex",
      flexWrap: "wrap",
      width: "100%",
      color: theme.typography.body1.color,
      justifyContent: "space-between",
      "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
        borderWidth: "thin",
      },
    },
    selectionItem: {
      display: "flex",
      flexWrap: "wrap",
      width: "100%",
      justifyContent: "space-between",
    },
    menuItem: {
      width: "100%",
    },
  }),
);

interface SideDetailPanelProps {
  id: string;
  onClose: () => void;
  onExploreRoot: () => void;
  graphQueries?: GraphExploreQueries;
  disableExplore?: boolean;
  graphQueriesNodes: ExpansionArray;
}
const SideDetailPanel = (props: SideDetailPanelProps) => {
  /**
    Component: SideDetailPanel

    Renders in the side panel an independently managed loaded item.

    */

  
  // Defined states for Menu Management for "Entity Actions"
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null); 
  const open = Boolean(anchorEl)
  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null);
  }

  const classes = useStyles();
  const registryLink = REGISTRY_LINK + `/item/${props.id}`;

  const filterTitle = "Provenance Queries";
  const placeholderText = "Click to select a query";

  // Load the item (from ID -> Typed)
  const loadedItem = useCombinedLoadedItem({
    id: props.id,
  });

  const itemDisabled = (currentId: string, values: string[]) => {
    return !!props.graphQueriesNodes.find(
      (item) => item.id === currentId && values.includes(item.query),
    );
  };

  // Conditionally renders the "Generate Report Button"
  const subtype = loadedItem.data?.item_subtype as ItemSubType | undefined;
  const isStudy = subtype === "STUDY"
  const isModelRun = subtype === "MODEL_RUN";

  const isModelRunOrStudy =
    isStudy || isModelRun &&
    loadedItem.data

  const { openDialog, renderedDialog } = useGenerateReportDialog({
    id: loadedItem?.data?.id,
    itemSubType: loadedItem.data?.item_subtype
  })

  const renderSelectionDropDown = (id: string) => {
    return (
      <FormControl fullWidth className={classes.selectionFormControl}>
        <InputLabel id="explore-selections-label">{filterTitle}</InputLabel>
        <Select
          labelId="explore-selections-label"
          id="explore-selections-select"
          value={placeholderText}
          displayEmpty
          renderValue={() => (
            <Typography variant="body1">{placeholderText}</Typography>
          )}
          label={filterTitle}
          fullWidth
          className={classes.selectRoot}
          variant="outlined"
        >
          {props.graphQueries &&
            props.graphQueries.special.map((query) => {
              return (
                <MenuItem
                  key={query.name}
                  value={query.name}
                  disabled={itemDisabled(props.id, query.queryList)}
                  onClick={() => {
                    query.run(props.id);
                  }}
                  style={{ justifyContent: "space-between" }}
                >
                  <Typography variant="body1">{query.name}</Typography>
                  <Tooltip
                    title={
                      <React.Fragment>
                        <Typography color="inherit">{query.name}</Typography>
                        {query.description}
                      </React.Fragment>
                    }
                  >
                    <IconButton
                      disabled={false}
                      style={{
                        transition: "none",
                      }}
                    >
                      <HelpOutline fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </MenuItem>
              );
            })}
        </Select>
      </FormControl>
    );
  };

  return (
    <div className={classes.detailPanel}>
      <Grid container xs={12} className={classes.titleBar}>
        <Typography variant="h6">Entity Details</Typography>
        <IconButton onClick={props.onClose}>
          <ClearIcon />
        </IconButton>
      </Grid>
      <Stack direction="column" spacing={3}>
        <Divider />
        <Grid container xs={12} className={classes.buttonsBar}>
          <Grid item md={6} className={classes.buttons} pr={1}>
            <Button
              variant="outlined"
              fullWidth
              onClick={props.onExploreRoot}
              disabled={!!props.disableExplore}
            >
              View Entity Lineage
            </Button>
          </Grid>
          <Grid item md={6} className={classes.buttons}>
            <Button
              variant="outlined"
              fullWidth
              onClick={handleClick}
            >
              Entity Actions
            </Button>
            <Menu
              anchorEl={anchorEl}
              open={open}
              onClose={handleClose}
            >
              <MenuItem
                onClick={() => {
                  window.open(registryLink, "_blank", "noopener,noreferrer");
                }}
              >
                View In Registry
                <LaunchIcon style={{ marginLeft: "10px" }} />
              </MenuItem>

              <MenuItem
                onClick={openDialog}
                disabled={!isModelRunOrStudy}
              >
                Generate Report
                <FileDownload style={{ marginLeft: "10px" }} />
              </MenuItem>
            </Menu>
          </Grid>
        </Grid>
        {/* Selections dropdown for query filtering */}
        <Stack direction="row" spacing={2}>
          {renderSelectionDropDown(props.id)}
        </Stack>
        {
          // Display the loaded item including possible error status
        }
        <ItemDisplayWithStatusComponent
          id={props.id}
          layout="stack"
          disabled={false}
          status={loadedItem}
        />

        // Renders the Generate Report Dialog
        {renderedDialog}

      </Stack>
    </div>
  );
};

export default SideDetailPanel;
