import { useQueries } from "@tanstack/react-query";
import debounce from "lodash.debounce";
import { useEffect, useState } from "react";
import { queryDispatcher } from "../queries/explore";
import { ItemBase, ItemSubType } from "../shared-interfaces/RegistryModels";
import { useUntypedLoadedItem } from "./useLoadedItem";

// Types for graph
export interface GraphNodeData {
    id: string;
    item_category: string;
    item_subtype: string;
    details?: ItemBase;
}

export interface GraphLinkData {
    source: string;
    target: string;
    type: string;
}

export interface NodeGraphData {
    nodes: GraphNodeData[];
    links: GraphLinkData[];
}

export interface GraphConfig {}

const DEFAULT_CONFIG: GraphConfig = {};

export interface GraphStatus {
    fetching: boolean;
    error: boolean;
    errorMessage?: string;
}

interface ExpanderQuery {
    name: string;
    description: string;
    queryList: Array<QueryType>;
    run: (id: string) => void;
}
export interface GraphExploreQueries {
    expandNode: ExpanderQuery;
    special: Array<ExpanderQuery>;
}

export interface GraphControls {
    resetGraph: () => void;
    onHoverEnter: (id: string) => void;
    onHoverExit: () => void;
    selectFocusNode: (id: string) => void;
    deselectFocusNode: () => void;
    graphQueries: GraphExploreQueries;
}

export interface useProvGraphDataProps {
    rootId: string;
    config?: GraphConfig;
}

export interface HoverData {
    id: string;
    item?: ItemBase;
    subtype?: ItemSubType;
    loading: boolean;
    error: boolean;
    errorMessage?: string;
}

export const QUERY_TYPES = [
    "explore_upstream",
    "explore_downstream",
    "downstream_dataset",
    "upstream_dataset",
    "downstream_agent",
    "upstream_agent",
];
export type QueryType = (typeof QUERY_TYPES)[number];

export interface ExpansionType {
    id: string;
    query: QueryType;
}
export type ExpansionArray = Array<ExpansionType>;

export interface useProvGraphDataResponse {
    // Graph and controls may not be present if errors occurred
    graph?: NodeGraphData;
    controls?: GraphControls;
    hoverData?: HoverData;
    focusNodeId: string | undefined;
    queriedNodes: ExpansionArray;
    status: GraphStatus;
}
export const useProvGraphData = (
    props: useProvGraphDataProps
): useProvGraphDataResponse => {
    /**
    Hook: useProvGraph

    Manages the data/connections and interactions with the prov graph.
    */

    // Extract info from props
    const config = props.config ?? DEFAULT_CONFIG;
    const rootId = props.rootId;

    // Maintain a list of expanded nodes which will be loaded with another hook
    // Start by expanding the root id
    const defaultExpanded: ExpansionArray = [
        { id: rootId, query: "explore_upstream" },
        { id: rootId, query: "explore_downstream" },
    ];
    const [queriedNodes, setQueriedNodes] =
        useState<ExpansionArray>(defaultExpanded);

    // Simple handler to restart - reset all state
    const resetGraph = () => {
        setQueriedNodes(defaultExpanded);
        setFocusNodeId(undefined);
        setHoverId(undefined);
    };

    // If the root id changes - reset the graph
    useEffect(() => {
        resetGraph();
    }, [props.rootId]);

    const addNodeQuery = (id: string, types: Array<QueryType>): void => {
        // non mutating copy and push
        const newList = queriedNodes.map((i) => i);
        types.forEach((type) => {
            newList.push({ id, query: type });
        });
        setQueriedNodes(newList);
    };

    const generateBasicExploreFunc = (types: Array<QueryType>) => {
        return (id: string) => {
            addNodeQuery(id, types);
        };
    };

    // Hover state
    const [hoverId, setHoverId] = useState<string | undefined>(undefined);

    // If hover Id is defined - load the data for the item
    const loadedHoverItem = useUntypedLoadedItem({
        id: hoverId,
        enabled: hoverId !== undefined,
        queryKeyPrefix: "hover",
    });

    // Return nicely formatted data if ID is selected
    const hoverData: HoverData | undefined = hoverId
        ? {
              id: hoverId,
              item: loadedHoverItem.data,
              subtype: loadedHoverItem.data?.item_subtype,
              loading: loadedHoverItem.loading,
              error: loadedHoverItem.error,
              errorMessage: loadedHoverItem.errorMessage,
          }
        : undefined;

    // Selected state
    const [focusNodeId, setFocusNodeId] = useState<string | undefined>(
        undefined
    );

    // Selected state handlers
    const selectFocusNode = (id: string) => {
        setFocusNodeId(id);
    };
    const deselectFocusNode = () => {
        setFocusNodeId(undefined);
    };

    // Use react query list to manage list of expanded nodes
    const expandCacheTime = 60000; // 60s

    // process into list of queries
    const resolvedQueries = queriedNodes.map((expansion: ExpansionType) => {
        const resolvedQuery = queryDispatcher({
            id: expansion.id,
            query: expansion.query,
        });
        return {
            resolvedQuery,
            ...expansion,
        };
    });

    // Filter for only valid expansion types
    const filteredQueries = resolvedQueries.filter((resolvedExpansion) => {
        return resolvedExpansion.resolvedQuery !== undefined;
    });

    const expandQueries = useQueries({
        queries: filteredQueries.map((resolvedExpansion) => {
            const { id, query, resolvedQuery } = resolvedExpansion;
            return {
                // Unique set of node query, type and id
                queryKey: ["nodequery" + query + id],
                queryFn: () => {
                    return resolvedQuery!;
                },
                staleTime: Infinity,
            };
        }),
    });

    const mergeGraphs = (
        baseG: NodeGraphData,
        newG: NodeGraphData
    ): NodeGraphData => {
        // copy the base graph
        const outputG: NodeGraphData = JSON.parse(JSON.stringify(baseG));

        // for each new node, add to output if not already present
        for (const newNode of newG.nodes) {
            let found = false;
            for (const oldNode of outputG.nodes) {
                if (newNode.id === oldNode.id) {
                    found = true;
                    break;
                }
            }

            if (!found) {
                // push a copy of new node
                outputG.nodes.push(JSON.parse(JSON.stringify(newNode)));
            }
        }

        // Now for each link - check if already from/to present - NOTE currently
        // restrict to only one relation between nodes
        for (const newLink of newG.links) {
            let found = false;
            for (const oldLink of outputG.links) {
                if (
                    newLink.source === oldLink.source &&
                    newLink.target === oldLink.target
                ) {
                    found = true;
                    break;
                }
            }

            if (!found) {
                // push a copy of new node
                outputG.links.push(JSON.parse(JSON.stringify(newLink)));
            }
        }

        return outputG;
    };

    // Based on the expanded nodes and current nodes, reproduce the graph state
    const deriveGraphState = (): NodeGraphData => {
        // collect all nodes from all expanded nodes
        // derive the connections using a map as we go

        var cumulativeGraph: NodeGraphData = { nodes: [], links: [] };

        for (const result of expandQueries) {
            if (result.data) {
                // This can potentially be a list of lineage responses - not just one
                const lineageResponse = result.data;

                // Parse as graphs
                const fallbackGraph = { nodes: [], links: [] } as NodeGraphData;
                const newGraph = (lineageResponse.graph ??
                    fallbackGraph) as unknown as NodeGraphData;
                cumulativeGraph = mergeGraphs(cumulativeGraph, newGraph);
            }
        }

        return cumulativeGraph;
    };

    // Derive graph state
    const graphData = deriveGraphState();

    // Debounce hover logic
    const onHoverExitDebounced = debounce(() => setHoverId(undefined), 500);

    // Clean up any debounced exits
    const onHoverEnterDebounced = (id: string) => {
        setHoverId(id);
        onHoverExitDebounced.cancel();
    };

    // Graph states

    // Loading := Any of the expand queries is loading
    const loading = expandQueries.some((q) => q.isFetching);
    const isError = expandQueries.some((q) => q.isError);
    const errorMessage: string | undefined = expandQueries.find(
        (q) => q.isError
    )?.error as string;

    return {
        graph: graphData,
        status: {
            fetching: loading,
            error: isError,
            errorMessage: errorMessage,
        },
        hoverData: hoverData,
        focusNodeId: focusNodeId,
        queriedNodes: queriedNodes,
        controls: {
            resetGraph,
            onHoverEnter: onHoverEnterDebounced,
            onHoverExit: onHoverExitDebounced,
            selectFocusNode,
            deselectFocusNode,
            graphQueries: {
                expandNode: {
                    name: "Expand Node",
                    description:
                        "Expands all node relationships one step in the upstream and downstream direction",
                    queryList: ["explore_downstream", "explore_upstream"],
                    run: generateBasicExploreFunc([
                        "explore_downstream",
                        "explore_upstream",
                    ]),
                },
                special: [
                    {
                        name: "Effected Downstream Datasets",
                        description:
                            "Expands all node relationships in the downstream direction to find any effected Datasets.",
                        queryList: ["downstream_dataset"],
                        run: generateBasicExploreFunc(["downstream_dataset"]),
                    },

                    {
                        name: "Contributing Upstream Datasets",
                        description:
                            "Expands all node relationships in the upstream direction to find any contributing Datasets.",
                        queryList: ["upstream_dataset"],
                        run: generateBasicExploreFunc(["upstream_dataset"]),
                    },
                    {
                        name: "Effected Downstream Agents",
                        description:
                            "Expands all node relationships in the downstream direction to find any effected Agents.",
                        queryList: ["downstream_agent"],
                        run: generateBasicExploreFunc(["downstream_agent"]),
                    },

                    {
                        name: "Contributing Upstream Agents",
                        description:
                            "Expands all node relationships in the upstream direction to find any contributing Agents.",
                        queryList: ["upstream_agent"],
                        run: generateBasicExploreFunc(["upstream_agent"]),
                    },
                ],
            },
        },
    };
};
