import ArrowCircleDownTwoTone from "@mui/icons-material/ArrowCircleDownTwoTone";
import ArrowCircleUpTwoTone from "@mui/icons-material/ArrowCircleUpTwoTone";
import HelpIcon from "@mui/icons-material/Help";
import LockOpenIcon from "@mui/icons-material/LockOpen";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import SwapVerticalCircleTwoTone from "@mui/icons-material/SwapVerticalCircleTwoTone";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import ZoomOutIcon from "@mui/icons-material/ZoomOut";
import {
    Box,
    Checkbox,
    CircularProgress,
    ClassNameMap,
    FormControlLabel,
    IconButton,
    Stack,
    Tooltip,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import * as d3 from "d3";
import debounce from "lodash.debounce";
import { observer } from "mobx-react-lite";
import { useEffect, useRef, useState } from "react";
import { GraphToolTip } from "../components/GraphToolTip";
import { DOCUMENTATION_BASE_URL } from "../queries";
import { ItemSubType } from "../shared-interfaces/AuthAPI";
import { getSwatchForSubtype } from "../util";
import { GraphLink, GraphNode, NodeGraph } from "../util/graphUtils";
import { createSubtypeAcronym } from "../util/util";
import { useObservedRef } from "./useObservedRef";
import { HoverData, NodeGraphData } from "./useProvGraphData";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        container: {
            position: "relative",
        },
        link: {
            stroke: "#7A7A7A",
            markerEnd: "url(#arrowhead)",
        },
        nodeContainer: {
            cursor: "grab",
            "&:active": {
                cursor: "grabbing",
            },
        },
        outerRing: {},
        activeOuterRing: {},
        node: {},
        nodeLabel: {
            stroke: "#FFFFFF",
            fontSize: "10px",
        },
        hidden: {
            visibility: "hidden",
        },
        zoomContainer: {
            display: "flex",
            justifyContent: "flex-end",
        },
        zoomIcon: {
            fontSize: "30px",
        },
        expandIcon: {
            fontSize: "30px",
        },
        networkChart: {
            cursor: "grab",
            border: "1px dotted " + theme.palette.primary.light,
            borderRadius: theme.spacing(1),
            marginBottom: theme.spacing(1),
            "&:active": {
                cursor: "grabbing",
            },
        },
        itemDetailViewContainer: {
            display: "block",
            margin: 0,
            padding: 0,
        },
        itemDetailViewContainerClosed: {
            display: "none",
        },
        buttonDrawerIcons: {
            fontSize: "30px",
        },
        buttonTooltipsEmphasize: {
            color: theme.palette.info.light,
            textDecoration: "underline",
        },
        iconGroupBox: {
            border: `1px dotted ${theme.palette.text.secondary}`,
            borderRadius: "20px",
        },
        loadingIconAbsolute: {
            position: "absolute",
            left: theme.spacing(1),
            bottom: "100px",
        },
    })
);

// Constants
const nodeRadius = 30;
const outerNodeRadius = 36;
// Starting point
const buildInitialZoomTransform: () => d3.ZoomTransform = () => {
    return new d3.ZoomTransform(1, 0, 0);
};

// How long to wait before firing single click
const singleClickDelayMS = 400;

// TODO restore active outer node on hover
const activeOuterNodeRadius = 36;

const resetPhysicsFunctionGenerator = (
    nodes: GraphNode[],
    simulation: SimulationType
) => {
    // Generates a function which resets the list of nodes physics locks if any
    const resetFunction = (): void => {
        simulation.stop();
        for (const node of nodes) {
            node.fx = undefined;
            node.fy = undefined;
        }
        simulation.alpha(1).restart();
    };
    return resetFunction;
};

const dragged = (
    simulation: d3.Simulation<GraphNode, undefined>,
    markLocked: () => void
): ((event: any, d: GraphNode) => void) => {
    return (event, d) => {
        // Note that we are locked
        markLocked();

        d.x = event.x;
        d.y = event.y;

        d.fx = event.x;
        d.fy = event.y;

        d.vx = 0;
        d.vy = 0;

        // Reset simulation to preferred energy
        simulation.alpha(physicsParams.drag.dragAlphaReset).restart();
    };
};

const draggedEnd = (event: any, d: GraphNode) => {
    // Only unlock on drop if drag params specifies no lock
    if (!physicsParams.drag.lockOnDrop) {
        d.fx = undefined;
        d.fy = undefined;
    }
};

let arrowWidth = 12;
let arrowHeight = arrowWidth - 2;

interface PhysicsParameters {
    manyBody: {
        // How strong is repulsive e.g. -500
        force: number;
        // max force distance e.g. 500
        maxDistance: number;
        // many body simulation accuracy
        // 0->1
        accuracy: number;
    };

    link: {
        // target distance - think of spring resting state
        distance: number;
    };

    collision: {
        // defaults to zero
        radiusOffset?: number;
    };

    drag: {
        // how much energy reset when dragged 1.0 = none, 0.0 = max
        dragAlphaReset: number;

        // Should the position be locked when let go?
        lockOnDrop: boolean;
    };

    // 0->1 friction - higher=more
    // v@t(n+1) = friction*v@t(n)
    friction: number;
}

const proposedParams: PhysicsParameters = {
    manyBody: {
        force: -500,
        // approx twice link distance max
        maxDistance: 400,
        accuracy: 0.4,
    },

    drag: {
        // not as much energy on let go
        dragAlphaReset: 0.3,
        // lock on let go
        lockOnDrop: true,
    },

    link: {
        distance: 200,
    },

    collision: {
        radiusOffset: 50,
    },

    // some additional friction
    friction: 0.5,
};

const physicsParams: PhysicsParameters = proposedParams;

// Id/group name constants
const arrowHeadGraphicID = "arrowhead";

// Selects based on the nodes group
const nodesSelector = ".nodes";

// Selects based on the line type
const arrowsSelector = "line";
const edgesPathSelector = ".edgepath";
const edgeLabelSelector = ".edgelabel";

// Some class names
const pathClassName = "edgepath";
const edgeLabelClassName = "edgelabel";

const arrowHeadGraphic = (svg: any): void => {
    // Appends to the provided svg selection a defs object
    svg.append("defs")
        .append("marker")
        .attr("id", arrowHeadGraphicID)
        .attr("viewBox", "0 0 10 10")
        .attr("refX", 5)
        .attr("refY", 5)
        .attr("markerUnits", "strokeWidth")
        .attr("markerWidth", arrowWidth)
        .attr("markerHeight", arrowHeight)
        .attr("orient", "auto")
        .append("svg:path")
        .attr("d", "M 0 0 L 10 5 L 0 10 z")
        .attr("stroke", "#7A7A7A")
        .attr("fill", "#7A7A7A");
};

const safeFromTo = (
    graphLink: GraphLink
): { from: GraphNode | undefined; to: GraphNode | undefined } => {
    if (
        !(
            typeof graphLink.source == "string" ||
            typeof graphLink.source == "number" ||
            typeof graphLink.target == "string" ||
            typeof graphLink.target == "number" ||
            graphLink.source === undefined ||
            graphLink.target === undefined
        )
    ) {
        return {
            from: graphLink.source as GraphNode,
            to: graphLink.target as GraphNode,
        };
    }
    return { from: undefined, to: undefined };
};

type SimulationType = d3.Simulation<GraphNode, undefined>;

type TimerType = ReturnType<typeof setTimeout> | undefined;
interface AddSimulationBehavioursInputs {
    simulation: SimulationType;
    nodesSelection: d3.Selection<SVGGElement, GraphNode, SVGGElement, unknown>;
    nodes: GraphNode[];
    exploreNodeFunction: (id: string) => void;
    markLocked: () => void;
    onHoverEnter: (id: string) => void;
    onHoverExit: () => void;
    setDragging: (dragging: boolean) => void;
    getDragging: () => boolean;
    selectFocusNode: (id: string) => void;
    getDblClickTimer: () => TimerType;
    setDblClickTimer: (timer: TimerType) => void;
}
interface AddSimulationBehavioursOutputs {
    resetPhysicsHandler: () => void;
}
const addSimulationBehaviours = (
    inputs: AddSimulationBehavioursInputs
): AddSimulationBehavioursOutputs => {
    // What happens when nodes are dragged?
    let nodeDragBehavior = d3
        .drag<any, GraphNode>()
        // No handler for drag start
        //.on("dragstart", dragstart)
        .on("drag", (e, d: GraphNode) => {
            // Update node position
            dragged(inputs.simulation, inputs.markLocked)(e, d);
        })
        .on("start", (e, d: GraphNode) => {
            // Notify that we are in dragging mode
            inputs.setDragging(true);
            // While dragging the hover menu should be disabled to avoid
            // flickering
            inputs.onHoverExit();
        })
        .on("end", (e, d: GraphNode) => {
            inputs.setDragging(false);
            draggedEnd(e, d);
        });

    inputs.nodesSelection
        .on("mouseenter", (e, node: GraphNode) => {
            if (!inputs.getDragging()) {
                inputs.onHoverEnter(node.id);
            }
        })
        .on("mouseleave", (e, node: GraphNode) => {
            if (!inputs.getDragging()) {
                inputs.onHoverExit();
            }
        });

    // Define single and double click behaviours
    const dblClick = (e: any, node: GraphNode) => {
        inputs.exploreNodeFunction(node.id);
    };

    const singleClick = (e: any, node: GraphNode) => {
        inputs.selectFocusNode(node.id);
    };

    // Add the click event which focuses on the node
    inputs.nodesSelection.on("click", (e, node) => {
        // If there is a current dbl click timer - fire dbl click event and
        // clear timer
        if (inputs.getDblClickTimer() !== undefined) {
            clearTimeout(inputs.getDblClickTimer());
            inputs.setDblClickTimer(undefined);
            dblClick(e, node);
        } else {
            // Run the single click event after delay
            inputs.setDblClickTimer(undefined);

            // Set timeout
            inputs.setDblClickTimer(
                setTimeout(() => {
                    singleClick(e, node);
                    inputs.setDblClickTimer(undefined);
                }, singleClickDelayMS)
            );
        }
    });

    // Add the drag behaviour to the node elements
    inputs.nodesSelection.call(nodeDragBehavior);

    // reset physics logic
    const resetPhysicsHandler = resetPhysicsFunctionGenerator(
        inputs.nodes,
        inputs.simulation
    );

    return {
        resetPhysicsHandler,
    };
};

interface DrawLinksInputs {
    // Graph and canvas components
    svg: d3.Selection<SVGGElement, unknown, HTMLElement, any>;
    links: GraphLink[];
    nodesSelector: string;

    // selectors
    arrowsSelector: string;
    edgesPathSelector: string;
    edgeLabelSelector: string;

    // styling
    classes: ClassNameMap<string>;

    // Show labels
    showLabels: boolean;
}
interface DrawLinksOutputs {
    linkLineSelection: d3.Selection<
        SVGLineElement,
        GraphLink,
        SVGGElement,
        unknown
    >;
    // Paths and labels are conditional on showing labels
    edgePathSelection: d3.Selection<
        SVGPathElement,
        GraphLink,
        SVGGElement,
        unknown
    >;
    edgeLabelSelection:
        | d3.Selection<SVGTextPathElement, GraphLink, SVGGElement, unknown>
        | undefined;
}
const drawLinks = (inputs: DrawLinksInputs): DrawLinksOutputs => {
    /**
    Function: drawLinks

    Draws the lines, arrow heads etc for the links between nodes    
    */

    // Add the lines connecting nodes
    const linkElements = inputs.svg
        .selectAll(inputs.arrowsSelector)
        .data<GraphLink>(inputs.links)
        .enter()
        .append<SVGLineElement>("line")
        .attr("class", inputs.classes.link);

    var edgeLabels:
        | d3.Selection<SVGTextPathElement, GraphLink, SVGGElement, unknown>
        | undefined = undefined;

    // Paths for text
    const edgePaths = inputs.svg
        //make path go along with the link provide position for link labels
        .selectAll(inputs.edgesPathSelector)
        .data(inputs.links)
        .enter()
        .append("path")
        .attr("class", pathClassName)
        .attr("fill-opacity", 0)
        .attr("stroke-opacity", 0)
        .attr("id", function (d, i) {
            return pathClassName + i;
        })
        .style("pointer-events", "none");

    // Conditionally render labels
    if (inputs.showLabels) {
        edgeLabels = inputs.svg
            .selectAll(inputs.edgeLabelSelector)
            .data(inputs.links)
            .enter()
            .append("text")
            .style("pointer-events", "none")
            .attr("class", edgeLabelClassName)
            .attr("id", function (d, i) {
                return edgeLabelClassName + i;
            })
            .attr("font-size", 12)
            .attr("fill", "#232323")
            // To render text along the shape of a <path>, enclose the text in a
            // <textPath> element that has an href attribute with a reference to the
            // <path> element.
            .append("textPath")
            .attr("xlink:href", function (d, i) {
                return "#" + pathClassName + i;
            })
            .style("text-anchor", "middle")
            .style("pointer-events", "none")
            .attr("startOffset", "50%")
            .style("alignment-baseline", "after-edge")
            .text((d: GraphLink) => d.type);
    }
    return {
        linkLineSelection: linkElements,
        edgePathSelection: edgePaths,
        edgeLabelSelection: edgeLabels,
    };
};

interface DrawNodesInputs {
    nodes: GraphNode[];
    nodesSelector: string;
    classes: ClassNameMap<string>;
    svg: d3.Selection<SVGGElement, unknown, HTMLElement, any>;
    focusNodeId?: string;
}
interface DrawNodesOutputs {
    nodesSelection: d3.Selection<SVGGElement, GraphNode, SVGGElement, unknown>;
}
const drawNodes = (inputs: DrawNodesInputs): DrawNodesOutputs => {
    /**
    Function: DrawNodes
    
    Draws the nodes to the specified SVG canvas and returns the selection
    */
    const nodeElements = inputs.svg
        .selectAll(inputs.nodesSelector)
        .data(inputs.nodes)
        .enter()
        .append("g")
        .attr("class", inputs.classes.nodeContainer);

    nodeElements
        .append("circle")
        .attr("class", inputs.classes.outerRing)
        .attr("id", (d: GraphNode) => {
            return "outer" + d.id;
        })
        .attr("r", (d: GraphNode) => {
            return outerNodeRadius;
        })
        // If current node is the focused node, change its colour to its tintColour, as a focusing highlight
        .attr("fill", (d: GraphNode) => {
            return d.id === inputs.focusNodeId
                ? getSwatchForSubtype(d.item_subtype as ItemSubType).tintColour
                : getSwatchForSubtype(d.item_subtype as ItemSubType).colour;
        });
    nodeElements
        .append("circle")
        .attr("class", inputs.classes.node)
        .attr("fill", (d: GraphNode) => {
            return getSwatchForSubtype(d.item_subtype as ItemSubType).colour;
        })
        .attr("r", (d: GraphNode) => {
            return nodeRadius;
        })
        // If current node is the focused node, change its white ring to its tintColour, as a focusing highlight
        .attr("stroke", (d: GraphNode) => {
            return d.id === inputs.focusNodeId
                ? getSwatchForSubtype(d.item_subtype as ItemSubType).tintColour
                : "#ffffff"; //white
        })
        .attr("stroke-width", 3);

    nodeElements.append("title").text((d: GraphNode) => d.id);

    nodeElements
        .append("text")
        .attr("class", inputs.classes.nodeLabel)
        .attr("text-anchor", "middle")
        .attr("startOffset", "50%")
        .attr("alignment-baseline", "middle")
        .text((d: GraphNode) => createSubtypeAcronym(d.item_subtype));

    // Return the selection for further per node modifications
    return {
        nodesSelection: nodeElements,
    };
};

type TickFunction = () => void;

interface RedrawCanvasProps {
    canvasSelector: string;
    nodes: GraphNode[];
    links: GraphLink[];
    classes: ClassNameMap<string>;
    showLabels: boolean;
    zoomTransform: d3.ZoomTransform | undefined;
    setZoomTransform: (transform: d3.ZoomTransform | undefined) => void;
    focusNodeId?: string;
}
interface RedrawCanvasResponse {
    nodesSelection: d3.Selection<SVGGElement, GraphNode, SVGGElement, unknown>;
    tick: TickFunction;
    zoomInHandler: () => void;
    zoomOutHandler: () => void;
}

const redrawCanvas = (inputs: RedrawCanvasProps): RedrawCanvasResponse => {
    // clear all from the svg canvas
    d3.select(inputs.canvasSelector).selectAll("*").remove();

    // Setup d3 canvas/svg object to draw on
    let canvas = d3
        .select(inputs.canvasSelector)
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100%");

    // Setup stored graphics (only done once)
    arrowHeadGraphic(canvas);

    // Create root group on canvas
    const svg = canvas.append("g");

    // Setup zoom behaviour for the canvas
    const zoom = d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.3, 5])
        .on("zoom", (event) => {
            inputs.setZoomTransform(event.transform);
            svg.attr("transform", event.transform);
        });

    // If there was an existing zoom state - update it here - otherwise
    // initialise
    canvas.call(
        zoom.transform,
        inputs.zoomTransform ?? buildInitialZoomTransform()
    );

    // Attach zoom behaviour to the canvas by calling
    canvas.call(zoom);

    // Disable dblclick zoom
    canvas.on("dblclick.zoom", null);

    // Supply zoom handlers for button controls
    const zoomInHandler = () => {
        canvas.call(zoom.scaleBy, 1.3);
    };
    const zoomOutHandler = () => {
        canvas.call(zoom.scaleBy, 1.0 / 1.3);
    };

    // Draw link graphics (below nodes)
    const { linkLineSelection, edgePathSelection } = drawLinks({
        svg: svg,
        links: inputs.links,
        nodesSelector: nodesSelector,
        arrowsSelector: arrowsSelector,
        edgesPathSelector: edgesPathSelector,
        edgeLabelSelector: edgeLabelSelector,
        classes: inputs.classes,
        showLabels: inputs.showLabels,
    });

    // Draw node graphics
    const { nodesSelection: nodeElements } = drawNodes({
        nodesSelector: nodesSelector,
        nodes: inputs.nodes,
        classes: inputs.classes,
        svg,
        focusNodeId: inputs.focusNodeId,
    });

    // Add behaviors and handlers for the nodes

    // Return the tick function
    const tick = () => {
        linkLineSelection.each(function (d: GraphLink) {
            if (
                typeof d.source == "string" ||
                typeof d.source == "number" ||
                typeof d.target == "string" ||
                typeof d.target == "number" ||
                d.source === undefined ||
                d.target === undefined
            ) {
                console.log(
                    "Tick function for uninitialised link... ignoring. From",
                    d.source,
                    ", To:",
                    d.target
                );
            } else {
                const from = d.source;
                const to = d.target;
                if (to.x && to.y && from.x && from.y) {
                    var x1 = from.x,
                        y1 = from.y,
                        x2 = to.x,
                        y2 = to.y,
                        angle = Math.atan2(y2 - y1, x2 - x1);
                    d.targetX =
                        x2 - Math.cos(angle) * (nodeRadius + arrowWidth);
                    d.targetY =
                        y2 - Math.sin(angle) * (nodeRadius + arrowWidth);
                }
            }
        });

        // Update link start endpoint positions
        linkLineSelection
            .attr("x1", (l) => {
                const { from } = safeFromTo(l);
                return from?.x ?? 0;
            })
            .attr("y1", (l) => {
                const { from } = safeFromTo(l);
                return from?.y ?? 0;
            })
            .attr("x2", (l) => {
                return l.targetX ?? 0;
            })
            .attr("y2", (l) => {
                return l.targetY ?? 0;
            });

        // Update node positions
        nodeElements
            .attr("cx", (d: GraphNode) => d.x ?? 0)
            .attr("cy", (d: GraphNode) => d.y ?? 0)
            .attr("transform", (d: GraphNode) => `translate(${d.x},${d.y})`);

        edgePathSelection.attr("d", (d: GraphLink) => {
            const { from, to } = safeFromTo(d);
            if (!from || !to) {
                console.log("Invalid D attribute update...");
                console.log(d);
                return "";
            } else {
                return "M " + from.x + " " + from.y + " L " + to.x + " " + to.y;
            }
        });
    };

    return {
        tick,
        nodesSelection: nodeElements,
        zoomInHandler,
        zoomOutHandler,
    };
};

const calculateCenterPoint = (
    width: number,
    height: number,
    transform: d3.ZoomTransform | undefined
): { x: number; y: number } => {
    /**
        Uses the transform to correct for canvas position.

        Based on reversing the transform then offsetting proper height/width to
        current center of canvas.
     */
    if (transform) {
        const { x, y, k } = transform;
        return {
            x: -x / k + width / (2 * k),
            y: -y / k + height / (2 * k),
        };
    } else {
        return {
            x: width / 2,
            y: height / 2,
        };
    }
};

interface RefreshSimulationInputs {
    width: number;
    height: number;
    nodes: GraphNode[];
    links: GraphLink[];
    tick: () => void;
    existingSimulation: SimulationType | undefined;
    reheat: boolean;
    zoomTransform: d3.ZoomTransform | undefined;
}

interface RefreshSimulationOutputs {
    simulation: SimulationType;
}
const refreshSimulation = (
    inputs: RefreshSimulationInputs
): RefreshSimulationOutputs => {
    /**
     * This function either creates or updates a d3 force simulation. This
     * involves updating the nodes, links, center force, tick function and
     * potentially reheating the simulation.
     */

    // Setup forces for simulation - nodes are attached later
    let simulation = inputs.existingSimulation ?? d3.forceSimulation();

    // Calculate center point - applies zoom transform offset correction
    let centerPoint = calculateCenterPoint(
        inputs.width,
        inputs.height,
        inputs.zoomTransform
    );

    simulation.stop();
    simulation = simulation
        // Add nodes
        .nodes(inputs.nodes)
        .force(
            "charge",
            d3
                .forceManyBody()
                .strength(physicsParams.manyBody.force)
                .distanceMax(physicsParams.manyBody.maxDistance)
                .theta(physicsParams.manyBody.accuracy)
        )
        // Update centering force to current center relative to zoom
        .force("forceX", d3.forceX(centerPoint.x))
        .force("forceY", d3.forceY(centerPoint.y))
        .force(
            "collide",
            d3.forceCollide(
                nodeRadius + (physicsParams.collision.radiusOffset ?? 0)
            )
        )
        .force(
            "link",
            d3
                .forceLink(inputs.links)
                .id(function (d: any) {
                    return d.id;
                })
                .distance(physicsParams.link.distance)
        )
        .velocityDecay(physicsParams.friction)
        .on("tick", inputs.tick);

    // Potentially reheat simulation
    if (inputs.reheat) {
        simulation.alpha(1.0);
    }

    // Always restart
    simulation.restart();

    return { simulation };
};

const mergeGraphDataIntoD3 = (
    graph: NodeGraph,
    graphData: NodeGraphData
): [NodeGraph, boolean] => {
    /**
     * Merge the graph data into the D3 data object - return a boolean noting if
     * anything changed.
     *
     * loop through the incoming data nodes and links and look for anything new
     * and update as we go Note that this method also deletes node if not
     * present in new graph.
     *
     */
    let change = false;

    // Keep track of discovered nodes
    let foundIdList: string[] = [];
    let foundLinkList: { from: string; to: string }[] = [];

    // for each new node, add to output if not already present
    for (const newNode of graphData.nodes) {
        // Mark as discovered
        foundIdList.push(newNode.id);

        let found = false;
        for (const oldNode of graph.nodes) {
            if (newNode.id === oldNode.id) {
                found = true;
                break;
            }
        }

        if (!found) {
            // change found
            change = true;
            // push a copy of new node
            graph.nodes.push({
                id: newNode.id,
                item_category: newNode.item_category,
                item_subtype: newNode.item_subtype,
                onHover: false,
            });
        }
    }

    // Now for each link - check if already from/to present - NOTE currently
    // restrict to only one relation between nodes

    // New links are referenced by the ID and don't contain the actual memory
    // links which forces intiialise
    for (const newLink of graphData.links) {
        // Mark as discovered
        foundLinkList.push({ from: newLink.source, to: newLink.target });

        let found = false;
        for (const oldLink of graph.links) {
            // safe from to on old link
            const { from, to } = safeFromTo(oldLink);

            // If linked - then check ID
            if (from && to) {
                if (newLink.source === from.id && newLink.target === to.id) {
                    found = true;
                    break;
                }
            } else {
                // Check directly by ID
                if (
                    newLink.source === oldLink.source &&
                    newLink.target === oldLink.target
                ) {
                    found = true;
                    break;
                }
            }
        }

        if (!found) {
            // change found
            change = true;

            // push a copy of new node
            graph.links.push({
                source: newLink.source,
                target: newLink.target,
                type: newLink.type,
            });
        }
    }

    // Now we have added all new things - delete any non present
    // Find list of indexes to delete
    const toDeleteNodeIndexes: number[] = [];
    const toDeleteLinkIndexes: number[] = [];

    // Iterate through existing graph nodes and
    graph.nodes.forEach((node, index) => {
        if (foundIdList.indexOf(node.id) === -1) {
            toDeleteNodeIndexes.push(index);
        }
    });
    // And the same for links as identified by to/from combination
    graph.links.forEach((link, index) => {
        const { from, to } = safeFromTo(link);
        // Source/target nodes are linked in memory
        if (from && to) {
            if (
                foundLinkList.findIndex((otherLink) => {
                    return otherLink.from === from.id && otherLink.to === to.id;
                }) === -1
            ) {
                toDeleteLinkIndexes.push(index);
            }
        }
        // Already strings
        else {
            if (
                foundLinkList.findIndex((otherLink) => {
                    return (
                        otherLink.from === link.source &&
                        otherLink.to === link.target
                    );
                }) === -1
            ) {
                toDeleteLinkIndexes.push(index);
            }
        }
    });

    // delete by reverse splicing (to avoid creating new array reference)
    for (const index of toDeleteNodeIndexes.reverse()) {
        graph.nodes.splice(index, 1);
    }
    for (const index of toDeleteLinkIndexes.reverse()) {
        graph.links.splice(index, 1);
    }

    // Mark as changed where required
    if (toDeleteNodeIndexes.length > 0 || toDeleteLinkIndexes.length > 0) {
        change = true;
    }

    return [graph, change];
};

interface ControlDrawerProps {
    toggleExpanded: () => void;
    zoomInHandler: () => void;
    zoomOutHandler: () => void;
    resetGraph: () => void;
    resetPhysicsHandler: () => void;
    setShowLabels: (show: boolean) => void;
    setUpstreamExpansion: (expandUpstream: boolean) => void;
    setDownstreamExpansion: (expandDownstream: boolean) => void;
    expandUpstream: boolean;
    expandDownstream: boolean;
    loading: boolean;
    showLabels: boolean;
    locked: boolean;
}
const ControlDrawer = observer((props: ControlDrawerProps) => {
    /**
    Component: ButtonDrawer

    Returns a horizontally arranged stack of buttons for controlling the graph
    */

    // CSS styles
    const classes = useStyles();

    const provExplorationDoc =
        DOCUMENTATION_BASE_URL +
        "/provenance/exploring-provenance/exploring-record-lineage.html#important-terms-and-concepts-for-provenance-exploration";

    // Expansion tooltips text styles
    const upstreamTooltipsTitle = (
        <div>
            Explore{" "}
            <a href={provExplorationDoc} target="_blank">
                <strong className={classes.buttonTooltipsEmphasize}>
                    upstream
                </strong>
            </a>{" "}
            only.
        </div>
    );
    const downstreamTooltipsTitle = (
        <div>
            Explore{" "}
            <a href={provExplorationDoc} target="_blank">
                <strong className={classes.buttonTooltipsEmphasize}>
                    downstream
                </strong>
            </a>{" "}
            only.
        </div>
    );
    const upAndDownTooltipsTitle = (
        <div>
            Explore both{" "}
            <a href={provExplorationDoc} target="_blank">
                <strong className={classes.buttonTooltipsEmphasize}>
                    upstream and downstream
                </strong>
            </a>
            .
        </div>
    );

    return (
        <Stack direction="row" justifyContent="space-between">
            {
                // LHS buttons
            }
            <Stack direction="row" justifyContent="left" spacing={2}>
                <FormControlLabel
                    control={
                        <Checkbox
                            onChange={() => {
                                props.setShowLabels(!props.showLabels);
                            }}
                            checked={props.showLabels}
                        />
                    }
                    label="Show link labels"
                />
            </Stack>
            {
                // Central buttons / status
            }
            <Stack direction="row" justifyContent="center" spacing={2}>
                {props.loading && <CircularProgress />}
            </Stack>
            {
                // RHS buttons
            }
            <Stack
                direction="row"
                justifyContent="right"
                alignItems="center"
                spacing={2}
            >
                <Box className={classes.iconGroupBox}>
                    <Tooltip title={upstreamTooltipsTitle} arrow>
                        <IconButton
                            onClick={() => {
                                props.setUpstreamExpansion(true);
                                props.setDownstreamExpansion(false);
                            }}
                            color={
                                props.expandUpstream && !props.expandDownstream
                                    ? "primary"
                                    : "inherit"
                            }
                        >
                            <ArrowCircleUpTwoTone
                                className={classes.buttonDrawerIcons}
                            />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title={downstreamTooltipsTitle} arrow>
                        <IconButton
                            onClick={() => {
                                props.setUpstreamExpansion(false);
                                props.setDownstreamExpansion(true);
                            }}
                            color={
                                !props.expandUpstream && props.expandDownstream
                                    ? "primary"
                                    : "inherit"
                            }
                        >
                            <ArrowCircleDownTwoTone
                                className={classes.buttonDrawerIcons}
                            />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title={upAndDownTooltipsTitle} arrow>
                        <IconButton
                            onClick={() => {
                                props.setUpstreamExpansion(true);
                                props.setDownstreamExpansion(true);
                            }}
                            color={
                                props.expandUpstream && props.expandDownstream
                                    ? "primary"
                                    : "inherit"
                            }
                        >
                            <SwapVerticalCircleTwoTone
                                className={classes.buttonDrawerIcons}
                            />
                        </IconButton>
                    </Tooltip>
                </Box>
                <Box className={classes.iconGroupBox}>
                    <IconButton onClick={props.zoomOutHandler} title="Zoom Out">
                        <ZoomOutIcon className={classes.buttonDrawerIcons} />
                    </IconButton>
                    <IconButton onClick={props.zoomInHandler} title="Zoom In">
                        <ZoomInIcon className={classes.buttonDrawerIcons} />
                    </IconButton>
                </Box>
                {props.locked && (
                    <IconButton
                        onClick={props.resetPhysicsHandler}
                        title="Unlock Node Positions"
                    >
                        <LockOpenIcon className={classes.buttonDrawerIcons} />
                    </IconButton>
                )}
                <IconButton onClick={props.toggleExpanded} title="Expand Graph">
                    <OpenInFullIcon className={classes.buttonDrawerIcons} />
                </IconButton>
                <IconButton
                    onClick={() => {
                        props.resetGraph();
                        // The reset graph also resets physics to ensure
                        // recentering and reheat
                        props.resetPhysicsHandler();
                    }}
                    title="Restart Graph"
                >
                    <RestartAltIcon className={classes.buttonDrawerIcons} />
                </IconButton>
                <IconButton
                    onClick={() => {
                        window.open(
                            DOCUMENTATION_BASE_URL +
                                "/provenance/exploring-provenance/exploring-record-lineage.html",
                            "_blank",
                            "noopener,noreferrer"
                        );
                    }}
                    title="Get Help"
                >
                    <HelpIcon className={classes.buttonDrawerIcons} />
                </IconButton>
            </Stack>
        </Stack>
    );
});

export interface UseProvGraphRendererControls {
    // The event to use when expanding a node
    expandNodeEvent: (id: string) => void;

    // The event to use to reset graph data
    resetGraph: () => void;

    // The event to expand/collapse
    toggleExpanded: () => void;

    // Hover enter/leave
    onHoverEnter: (id: string) => void;
    onHoverExit: () => void;

    // Controlling focused node
    selectFocusNode: (id: string) => void;
    deselectFocusNode: () => void;

    // Set upstream expansion and downstream expansion
    // True for need expand, false for no needs
    setUpstreamExpansion: (expandUpstream: boolean) => void;
    setDownstreamExpansion: (expandDownstream: boolean) => void;
}
export interface UseProvGraphRendererState {
    // The graph data to render
    nodeGraphData: NodeGraphData | undefined;

    // Currently expanded?
    expanded: boolean;

    // If hover is active, hover data
    hoverData?: HoverData;

    // Underlying data loading
    loading: boolean;

    // If click and focus on a node, node id
    focusNodeId?: string;

    // For setting double-click exploration direction, true for need expend in this direction
    expandUpstream: boolean;
    expandDownstream: boolean;
}

export interface useProvGraphRendererProps {
    // The id to use for the canvas
    canvasId: string;

    // Controls
    controls: UseProvGraphRendererControls;

    // State
    state: UseProvGraphRendererState;
}
export interface useProvGraphRendererResponse {
    render: () => JSX.Element;
    height: number;
}
export const useProvGraphRenderer = (
    props: useProvGraphRendererProps
): useProvGraphRendererResponse => {
    /**
    Hook: useuseProvGraphRenderer

    Maintains a consistent internal state so that d3 can manage
    adding/maintaining properties.

    Needs to merge new data against the existing persistent data carefully and
    manage state updates.

    */
    // CSS styles
    const classes = useStyles();

    // Dynamic graph handlers
    const voidHandler = () => {};
    const [zoomInHandler, setZoomInHandler] = useState<() => void>(
        () => voidHandler
    );
    const [zoomOutHandler, setZoomOutHandler] = useState<() => void>(
        () => voidHandler
    );
    const [resetPhysicsHandler, setResetPhysicsHandler] = useState<() => void>(
        () => voidHandler
    );

    // Managed callback ref with size observer
    const callbackSizeObserver = useObservedRef({ debug: false });

    // State
    const [graphData, setGraphData] = useState<NodeGraph | undefined>(
        undefined
    );
    const [simulation, setSimulation] = useState<SimulationType | undefined>(
        undefined
    );
    const [locked, setLocked] = useState<boolean>(false);
    // are we currently dragging?
    const [dragging, setDragging] = useState<boolean>(false);
    const draggingRef = useRef<boolean>(false);

    // Timer to manage single vs double click events
    const [dblClickTimer, setDblClickTimer] = useState<
        ReturnType<typeof setTimeout> | undefined
    >(undefined);
    // Need to keep a ref to this due to D3 handlers needing active state
    const dblClickTimerRef = useRef<TimerType>(undefined);

    // Update timer ref when timer state changes
    useEffect(() => {
        dblClickTimerRef.current = dblClickTimer;
    }, [dblClickTimer]);

    // Do we want to show labels?
    const [showLabels, setShowLabels] = useState<boolean>(true);

    // Update dragging ref when dragging changes
    useEffect(() => {
        draggingRef.current = dragging;
    }, [dragging]);

    // Current zoom state
    const [zoomTransform, setZoomTransform] = useState<
        d3.ZoomTransform | undefined
    >(undefined);

    // Get handler for non rerendered simulation live state
    const getDragging = () => {
        return draggingRef.current;
    };

    // layout state
    const defaultHeight = 500;
    const expandedHeight = 800;

    // Maintains the current height/width of the render div - height is driving
    // control for div, width is observed
    const [height, setHeight] = useState<number>(defaultHeight);
    // Width is observed using the custom hook
    const width = callbackSizeObserver.dims.width;

    // When expanded changes, update height
    useEffect(() => {
        setHeight(props.state.expanded ? expandedHeight : defaultHeight);
    }, [props.state.expanded]);

    // What selector to use for the prov graph
    const selector = "#" + props.canvasId;

    const graphModelChangedHandler = (
        // The new node data to update the graph and simulation with
        data: NodeGraph,
        // If true reheats the simulation - used when more nodes loaded
        reheat: boolean
    ) => {
        // Redraw canvas and refresh tick handler
        const {
            tick,
            nodesSelection,
            zoomInHandler: newZoomInHandler,
            zoomOutHandler: newZoomOutHandler,
        } = redrawCanvas({
            canvasSelector: selector,
            nodes: data.nodes,
            links: data.links,
            classes: classes,
            showLabels: showLabels,
            zoomTransform: zoomTransform,
            setZoomTransform: debounce(setZoomTransform, 200),
            focusNodeId: props.state.focusNodeId,
        });

        // Create or update existing simulation
        const { simulation: newSimulation } = refreshSimulation({
            existingSimulation: simulation,
            tick: tick,
            nodes: data.nodes,
            links: data.links,
            // Width is guaranteed to be defined here
            width: width!,
            height: height,
            reheat: reheat,
            zoomTransform,
        });

        // Set simulation if changed
        setSimulation(newSimulation);

        // Update behaviours which link graphical elements and simulation
        // properties
        const { resetPhysicsHandler: newResetPhysicsHandler } =
            addSimulationBehaviours({
                simulation: newSimulation,
                nodes: data.nodes,
                nodesSelection,
                exploreNodeFunction: props.controls.expandNodeEvent,
                markLocked: () => {
                    setLocked(true);
                },
                onHoverEnter: (id: string) => {
                    props.controls.onHoverEnter(id);
                },
                onHoverExit: () => {
                    props.controls.onHoverExit();
                },
                selectFocusNode: props.controls.selectFocusNode,
                setDragging: setDragging,
                getDragging,
                getDblClickTimer: () => {
                    return dblClickTimerRef.current;
                },
                setDblClickTimer,
            });

        // Update dynamic handlers derived from graph drawing
        setZoomInHandler(() => newZoomInHandler);
        setZoomOutHandler(() => newZoomOutHandler);
        setResetPhysicsHandler(() => () => {
            newResetPhysicsHandler();
            setLocked(false);
        });
    };

    // Check if the underlying graph data needs to be changed and merge if so
    useEffect(() => {
        // Don't try to start simulation until width is ready
        if (width && props.state.nodeGraphData) {
            const [possibleNewGraph, changed] = mergeGraphDataIntoD3(
                graphData ?? {
                    directed: true,
                    multigraph: true,
                    nodes: [],
                    links: [],
                },
                props.state.nodeGraphData
            );
            if (changed) {
                setGraphData(possibleNewGraph);
                // Redraw and reheat graph
                graphModelChangedHandler(possibleNewGraph, true);
            }
        }
    }, [props.state.nodeGraphData]);

    // Stateful variables which need to force a graph model reload due to d3
    useEffect(() => {
        if (graphData) {
            // Redraw but don't reheat graph
            graphModelChangedHandler(graphData, false);
        }
    }, [
        showLabels,
        width,
        props.state.focusNodeId,
        // TODO, Currently use these two dependence to force graph redraw after selecting the exploring directions.
        // Otherwise the graph uses old states and the double-click won't synchronise the lasted selections in the tool panel.
        props.state.expandUpstream,
        props.state.expandDownstream,
    ]);

    return {
        render: () => (
            <div>
                <Stack direction="column">
                    {
                        //Main div for svg canvas
                    }
                    <div
                        id={props.canvasId}
                        // Use ref callback style - this callback updates the
                        // current ref reference and sets initial height/width
                        ref={callbackSizeObserver.callbackRef}
                        className={classes.networkChart}
                        style={{ height: height.toString() + "px" }}
                    ></div>
                    {
                        // graph controls
                    }
                    <ControlDrawer
                        toggleExpanded={props.controls.toggleExpanded}
                        zoomInHandler={zoomInHandler}
                        zoomOutHandler={zoomOutHandler}
                        resetGraph={props.controls.resetGraph}
                        setUpstreamExpansion={
                            props.controls.setUpstreamExpansion
                        }
                        setDownstreamExpansion={
                            props.controls.setDownstreamExpansion
                        }
                        expandUpstream={props.state.expandUpstream}
                        expandDownstream={props.state.expandDownstream}
                        locked={locked}
                        resetPhysicsHandler={resetPhysicsHandler}
                        setShowLabels={setShowLabels}
                        showLabels={showLabels}
                        loading={props.state.loading}
                    />
                </Stack>
                {
                    // Tooltip popup
                }
                {props.state.hoverData && (
                    <GraphToolTip hoverData={props.state.hoverData} />
                )}
            </div>
        ),
        height: height,
    };
};
