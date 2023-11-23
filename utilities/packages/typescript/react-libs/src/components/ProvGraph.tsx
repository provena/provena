import { Alert, Grid, Stack } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { observer } from "mobx-react-lite";
import { useProvGraphData } from "../hooks/useProvGraphData";
import { useProvGraphRenderer } from "../hooks/useProvGraphRenderer";
import SideDetailPanel from "./SideDetailPanel";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        container: {
            position: "relative",
        },
        detailPanel: {
            overflowY: "scroll",
            wordBreak: "break-all",
            wordWrap: "break-word",
        },
    })
);

interface ProvGraphProps {
    rootId: string;
    setRootId: (rootId: string) => void;
    toggleExpanded: () => void;
    expanded: boolean;
}

const ProvGraph = observer((props: ProvGraphProps) => {
    const classes = useStyles();

    // The ID of the html element to render into
    const canvasId = "provchart";

    // Manages state of graph source data and provides interaction controls
    const graphHook = useProvGraphData({ rootId: props.rootId });

    // Visualises/renders the graph and maps interactive handlers to nodes
    const voidHandler = () => {};
    const { render, height } = useProvGraphRenderer({
        controls: {
            expandNodeEvent:
                graphHook.controls?.graphQueries.expandNode.run ?? voidHandler,
            resetGraph: graphHook.controls?.resetGraph ?? voidHandler,
            toggleExpanded: props.toggleExpanded,
            onHoverEnter: graphHook.controls?.onHoverEnter ?? ((id) => {}),
            onHoverExit: graphHook.controls?.onHoverExit ?? voidHandler,
            selectFocusNode:
                graphHook.controls?.selectFocusNode ?? ((id) => {}),
            deselectFocusNode:
                graphHook.controls?.deselectFocusNode ?? voidHandler,
            setUpstreamExpansion:
                graphHook.controls?.setUpstreamExpansion ??
                ((expandUpstream) => {}),
            setDownstreamExpansion:
                graphHook.controls?.setDownstreamExpansion ??
                ((expandDownstream) => {}),
        },
        state: {
            nodeGraphData: graphHook.graph,
            expanded: props.expanded,
            hoverData: graphHook.hoverData,
            loading: graphHook.status.fetching,
            focusNodeId: graphHook.focusNodeId,
            expandUpstream: graphHook.expandUpstream,
            expandDownstream: graphHook.expandDownstream,
        },
        canvasId: canvasId,
    });

    // Is the graph empty
    const graphEmpty = !(graphHook.graph && graphHook.graph.nodes.length > 0);
    const showGraphEmpty = graphEmpty && !graphHook.status.fetching;

    // Should the graph div be shown?
    const showGraph = !graphEmpty;

    // Maintain a detailed side view component based on controls/data of graph
    // hooks
    const showDetails = showGraph && graphHook.focusNodeId !== undefined;
    const detailWidth = 4;

    return (
        <Grid className={classes.container}>
            <Grid>
                <Stack direction="column" alignItems="center">
                    {graphHook.status.error && (
                        <Alert
                            variant="outlined"
                            color="error"
                            severity="error"
                        >
                            <b>An error occurred while traversing the graph.</b>
                            <br /> <br />
                            Error: {graphHook.status.errorMessage ??
                                "Unknown"}. <br />
                            <br />
                            Try refreshing the page.
                        </Alert>
                    )}
                    {showGraphEmpty && (
                        <Alert variant="outlined" color="info" severity="info">
                            <b>Empty provenance graph</b>
                            <br /> <br />
                            There are no connections to or from this root node.
                            No graph will be rendered.
                        </Alert>
                    )}
                    <Grid container>
                        {showGraph && (
                            <Grid item xs={showDetails ? 12 - detailWidth : 12}>
                                {graphHook.graph && render()}
                            </Grid>
                        )}
                        {showDetails && (
                            <Grid item xs={detailWidth}>
                                <div
                                    style={{
                                        height: height,
                                        maxHeight: height,
                                    }}
                                >
                                    <SideDetailPanel
                                        id={graphHook.focusNodeId!}
                                        onClose={
                                            graphHook.controls
                                                ?.deselectFocusNode ??
                                            voidHandler
                                        }
                                        onExploreRoot={() => {
                                            props.setRootId(
                                                graphHook.focusNodeId!
                                            );
                                        }}
                                        disableExplore={
                                            graphHook.focusNodeId ===
                                            props.rootId
                                        }
                                        graphQueries={
                                            graphHook.controls?.graphQueries
                                        }
                                        graphQueriesNodes={
                                            graphHook.queriedNodes
                                        }
                                    />
                                </div>
                            </Grid>
                        )}
                    </Grid>
                </Stack>
            </Grid>
        </Grid>
    );
});

export default ProvGraph;
