import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import ClearIcon from "@mui/icons-material/Clear";
import { Theme } from "@mui/material/styles";
import { Button, Grid, IconButton, Stack } from "@mui/material";
import { REGISTRY_LINK } from "react-libs";
import LaunchIcon from "@mui/icons-material/Launch";
import { useCombinedLoadedItem } from "react-libs";
import { ItemDisplayWithStatusComponent } from "./ItemDisplayWithStatus";

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
    })
);

interface SideDetailPanelProps {
    id: string;
    onClose: () => void;
    onExploreRoot: () => void;
    disableExplore?: boolean;
}
const SideDetailPanel = (props: SideDetailPanelProps) => {
    /**
    Component: SideDetailPanel

    Renders in the side panel an independently managed loaded item.

    */
    const classes = useStyles();
    const registryLink = REGISTRY_LINK + `/item/${props.id}`;

    // Load the item (from ID -> Typed)
    const loadedItem = useCombinedLoadedItem({
        id: props.id,
    });

    return (
        <div className={classes.detailPanel}>
            <Stack spacing={2}>
                <Grid container justifyContent="space-between">
                    <Grid item>
                        <Stack direction="column" spacing={2}>
                            <Button
                                variant="outlined"
                                onClick={props.onExploreRoot}
                                disabled={!!props.disableExplore}
                            >
                                View Entity Lineage
                            </Button>
                            <Button
                                variant="outlined"
                                onClick={() => {
                                    window.open(
                                        registryLink,
                                        "_blank",
                                        "noopener,noreferrer"
                                    );
                                }}
                            >
                                View In Registry{" "}
                                <LaunchIcon style={{ marginLeft: "10px" }} />
                            </Button>
                        </Stack>
                    </Grid>

                    <Grid item>
                        <IconButton onClick={props.onClose}>
                            <ClearIcon />
                        </IconButton>
                    </Grid>
                </Grid>
                {
                    // Display the loaded item including possible error status
                }
                <ItemDisplayWithStatusComponent
                    id={props.id}
                    layout="stack"
                    disabled={false}
                    status={loadedItem}
                />
            </Stack>
        </div>
    );
};

export default SideDetailPanel;
