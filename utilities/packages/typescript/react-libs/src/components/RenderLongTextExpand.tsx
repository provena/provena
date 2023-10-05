import { Link, Typography } from "@mui/material";
import { useState } from "react";

export interface RenderLongTextExpandProps {
    text: string;
    // How many characters need to be left as "View less" text
    // undefined for showing the whole text, with no expand function
    initialCharNum?: number;
}

export const RenderLongTextExpand = (props: RenderLongTextExpandProps) => {
    /**
    Component: RenderLongTextExpand

    Renders long text, default to "View less", can click "View more" to expand the whole texts.
    Refer to https://mui.com/x/react-data-grid/row-height/
    */

    // Default is not expanded
    const [expanded, setExpanded] = useState<boolean>(false);

    // If need to show "view less"/"view more"
    const showExpand =
        props.initialCharNum !== undefined &&
        props.text.length > props.initialCharNum;

    // For long Text render, can collapse text.
    if (props.text === "" || !props.text) return <Typography></Typography>;

    if (!showExpand) return <Typography>{props.text}</Typography>;

    const slicedText = props.text.slice(0, props.initialCharNum) + "...";

    return (
        <Typography>
            {expanded ? props.text : slicedText}
            <Typography>
                {showExpand && (
                    <Link
                        type="button"
                        component="button"
                        sx={{ fontSize: "inherit" }}
                        onClick={() =>
                            setExpanded((expanded: boolean) => !expanded)
                        }
                    >
                        {expanded ? "view less" : "view more"}
                    </Link>
                )}
            </Typography>
        </Typography>
    );
};
