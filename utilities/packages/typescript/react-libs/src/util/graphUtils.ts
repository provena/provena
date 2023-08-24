export interface GraphNode extends d3.SimulationNodeDatum {
    id: string;
    item_category: string;
    item_subtype: string;
    onHover: boolean;
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
    // The type of relation - e.g. the label of the link
    type: string;
    // The endpoint of the arrow (x,y)
    targetX?: number;
    targetY?: number;
}

export interface NodeGraph {
    directed: boolean;
    multigraph: boolean;
    nodes: GraphNode[];
    links: GraphLink[];
}
export interface Tooltip {
    id: string;
    category: boolean;
    subcategory: string;
}

export interface ITooltip {
    data: Tooltip;
}
