import {
    Alert,
    AlertTitle,
    Button,
    CircularProgress,
    Grid,
    Stack,
    Theme,
    Typography,
} from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { unset } from "lodash";
import { useState } from "react";
import { useTypedLoadedItem } from "../../hooks";
import { ItemBase, ItemSubType } from "../../shared-interfaces/RegistryModels";
import {
    prepareObject,
    prettifyRecordName,
    timestampToLocalTime,
} from "../../util/util";
import {
    CopyableLinkComponent,
    CopyableLinkedHandleComponent,
    CopyableTextComponent,
} from "../CopyFloatingButton";
import { LinkedUsernameDisplayComponent as LinkedUsernameToJsonDetails } from "../LinkedUsernameDisplay";
import { SubtypeHeaderComponent } from "../SubtypeSpecialisedHeader";
import {
    FieldRendererMap,
    JsonDetailViewComponent,
    JsonDetailViewComponentProps,
    JsonTypes,
    RendererOverride,
} from "./JsonDetailView";
import {
    ROW_GAP,
    genericStyledRenderer,
    objectRenderer,
    objectRendererBoxer,
    stringRenderer,
} from "./JsonTypeRenderers";

/**
    This file contains renderer overrides which are used by the type renderers
    in JsonTypeRenderers. 

    An override is applicable against a value type as specified by the
    RendererOverride generic type. 

    The renderer is very open ended - it can return any JSX.Element. 

    Most renderers use the genericStyledRenderer helper which takes a LH/RH
    JSX.Element content and renders into the styling specified by the props.

    Some overrides make modifications and pass into existing type renderers,
    others define new rendering approaches such as the id resolver overrides.
 */

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        boldText: {
            fontWeight: "bold",
        },
        valueText: {
            display: "inline-block",
            wordBreak: "break-all",
        },
    })
);

// How many characters before a string is truncated?
export const TRUNCATION_LIMIT = 100;

// Defines a handle display renderer override
export const urlOverride: RendererOverride<string> = (
    name: string,
    val: string,
    props: JsonDetailViewComponentProps
) => {
    const classes = useStyles();

    // LH Content
    const lhContent = (
        <Typography className={classes.boldText}>
            {prettifyRecordName(name)}
        </Typography>
    );

    // RH Content
    const rhContent = (
        <Typography className={classes.valueText}>
            <CopyableLinkComponent link={val} />
        </Typography>
    );

    return genericStyledRenderer({
        style: props.style,
        lhContent,
        rhContent,
    });
};

// For those don't need the href link, copy to the clipboard only
export const copyableOverride: RendererOverride<string> = (
    name: string,
    val: string,
    props: JsonDetailViewComponentProps
) => {
    const classes = useStyles();

    // LH Content
    const lhContent = (
        <Typography className={classes.boldText}>
            {prettifyRecordName(name)}
        </Typography>
    );

    // RH Content
    const rhContent = (
        <Typography className={classes.valueText}>
            <CopyableTextComponent text={val} clipBoard={val} />
        </Typography>
    );

    return genericStyledRenderer({
        style: props.style,
        lhContent,
        rhContent,
    });
};

// Wraps the username link service display as an override
export const linkedUsernameOverride: RendererOverride<string> = (
    name: string,
    val: string,
    props: JsonDetailViewComponentProps
) => {
    const classes = useStyles();

    // LH Content
    const lhContent = (
        <Typography className={classes.boldText}>
            {prettifyRecordName("owner_details")}
        </Typography>
    );

    // RH Content -> Will be a JSON detailed render of customised contents

    const boxedContent = objectRendererBoxer({
        interior: (
            <LinkedUsernameToJsonDetails username={val} jsonProps={props} />
        ),
        style: props.style,
    });

    return genericStyledRenderer({
        style: { ...props.style, layout: "stack" },
        lhContent,
        rhContent: boxedContent,
    });
};

// Defines a handle display renderer override
export const emailOverride: RendererOverride<string> = (
    name: string,
    val: string,
    props: JsonDetailViewComponentProps
) => {
    const classes = useStyles();

    // LH Content
    const lhContent = (
        <Typography className={classes.boldText}>
            {prettifyRecordName(name)}
        </Typography>
    );

    // RH Content
    const rhContent = (
        <Typography className={classes.valueText}>
            <CopyableLinkComponent link={"mailto:" + val} content={val} />
        </Typography>
    );

    return genericStyledRenderer({
        style: props.style,
        lhContent,
        rhContent,
    });
};

// Defines a handle display renderer override
export const handleOverride: RendererOverride<string> = (
    name: string,
    val: string,
    props: JsonDetailViewComponentProps
) => {
    const classes = useStyles();

    // LH Content
    const lhContent = (
        <Typography className={classes.boldText}>
            {prettifyRecordName(name)}
        </Typography>
    );

    // RH Content
    const rhContent = (
        <Typography className={classes.valueText}>
            <CopyableLinkedHandleComponent handleId={val} />
        </Typography>
    );

    return genericStyledRenderer({
        style: props.style,
        lhContent,
        rhContent,
    });
};

// Defines a handle display renderer override
export const serialisedJsonOverride: RendererOverride<string> = (
    name: string,
    val: string,
    props: JsonDetailViewComponentProps
) => {
    /**
     *  Assumes that the value contents are valid JSON - parses into JS object
     *  then uses the JSON detail view recursively with the updated object
     *  contents.
     */
    // Parse the RH content as an object
    const classes = useStyles();

    try {
        // This could throw validation err
        const parsedObject = JSON.parse(val);
        return JsonDetailViewComponent({
            ...props,
            json: { name, value: parsedObject },
        });
    } catch {
        // Just default back to a generic styled render - don't recurse because
        // we'll have an infinite override loop in that case

        // LH Content
        const lhContent = (
            <Typography className={classes.boldText}>
                {prettifyRecordName(name)}
            </Typography>
        );

        // RH Content
        const rhContent = (
            <Typography className={classes.valueText}>
                {prettifyRecordName(val)}
            </Typography>
        );
        return genericStyledRenderer({
            lhContent,
            rhContent,
            style: props.style,
        });
    }
};

// Defines a handle display renderer override
export const truncationOverride: RendererOverride<string> = (
    name: string,
    val: string,
    props: JsonDetailViewComponentProps
) => {
    const classes = useStyles();
    const [expanded, setExpanded] = useState<boolean>(false);
    const truncatedValue = val.substring(0, TRUNCATION_LIMIT) + "...";

    // LH Content
    const lhContent = (
        <Typography className={classes.boldText}>
            {prettifyRecordName(name)}
        </Typography>
    );

    // RH Content
    const rhContent = (
        <Grid
            container
            justifyContent="space-between"
            alignItems="center"
            flexWrap="nowrap"
        >
            <Grid item xs={10}>
                <Typography className={classes.valueText}>
                    {expanded ? val : truncatedValue}
                </Typography>
            </Grid>
            <Grid item>
                <Button
                    onClick={(e) => {
                        setExpanded((old) => !old);
                    }}
                    variant="outlined"
                >
                    {expanded ? "Collapse" : "Expand"}
                </Button>
            </Grid>
        </Grid>
    );

    return genericStyledRenderer({
        style: props.style,
        lhContent,
        rhContent,
    });
};

function subtypedIdResolverOverrideGenerator(inputs: {
    subtype: ItemSubType;
    fieldnameOverride?: string;
}): RendererOverride<string> {
    // Defines a handle display renderer override
    const override: RendererOverride<string> = (
        name: string,
        val: string,
        props: JsonDetailViewComponentProps
    ) => {
        const classes = useStyles();
        const [expanded, setExpanded] = useState<boolean>(false);

        const loadedItem = useTypedLoadedItem({
            enabled: expanded,
            id: val,
            subtype: inputs.subtype,
        });
        const item = loadedItem.data?.item;

        // avoids recursive lookup of owner username on Person - it is assumed
        // the person is the owner.

        // TODO do we want a more elegant approach?
        if (inputs.subtype === "PERSON" && item !== undefined) {
            unset(item, "owner_username");
        }

        // LH Content (same as usual)
        const lhContent = (
            <Stack
                direction="row"
                spacing={1.5}
                alignItems="center"
                justifyContent="flex-start"
            >
                <Typography className={classes.boldText}>
                    {inputs.fieldnameOverride ?? prettifyRecordName(name)}
                </Typography>
                <Button
                    variant="outlined"
                    onClick={(e) => {
                        setExpanded((old) => !old);
                    }}
                >
                    {expanded ? "Collapse" : "Expand"}
                </Button>
            </Stack>
        );

        // Always resolve this even if object is empty - just to avoid unstable hook
        // order
        const rhRenderedObject = objectRenderer({
            ...props,
            json: {
                // Top level render
                name: undefined,
                value: prepareObject(item ?? {}) as unknown as {
                    [k: string]: JsonTypes;
                },
            },
        });
        var readyToDisplay = false;

        // RH Content -> depends on if resolved yet

        var rhContent = <p>Loading...</p>;

        if (!expanded) {
            rhContent = (
                <Typography className={classes.valueText}>
                    <CopyableLinkedHandleComponent handleId={val} />
                </Typography>
            );
        } else {
            if (loadedItem.loading) {
                rhContent = <CircularProgress />;
            } else if (loadedItem.error) {
                rhContent = (
                    <div style={{ width: "100%" }}>
                        <Alert severity="error" variant="outlined">
                            <AlertTitle>Error Loading ID: {val}</AlertTitle>
                            Error : {loadedItem.errorMessage ?? "Unknown"}
                        </Alert>
                    </div>
                );
            } else if (item !== undefined) {
                readyToDisplay = true;
            }
        }

        if (readyToDisplay) {
            return genericStyledRenderer({
                // Force stack layout for loaded object - use boxer to reuse
                // boxing logic but retain customised entry

                // Override to stack
                style: { ...props.style, layout: "stack" },
                lhContent,

                // Show the rendered object within box
                rhContent: objectRendererBoxer({
                    style: props.style,
                    interior: (
                        <Stack direction="column" spacing={ROW_GAP}>
                            <SubtypeHeaderComponent
                                item={item! as ItemBase}
                                compact={true}
                            />
                            {rhRenderedObject}
                        </Stack>
                    ),
                }),
            });
        } else {
            return genericStyledRenderer({
                // Force stack layout for loaded object
                style: props.style,
                lhContent,
                rhContent,
            });
        }
    };

    return override;
}

function renamerOverrideGenerator(
    renamer: (input: string) => string
): RendererOverride<string> {
    return (name, val, props) => {
        // Override the name in the props to change Uri to URI
        const newName = renamer(name);
        const updatedProps = { ...props, json: { name: newName, value: val } };

        return stringRenderer(updatedProps);
    };
}

export const uriOverride = renamerOverrideGenerator((input) => {
    return input.replace("uri", "URI");
});

export const orcidOverride = renamerOverrideGenerator((input) => {
    return input.replace("orcid", "ORCID");
});

export const rorOverride = renamerOverrideGenerator((input) => {
    return input.replace("ror", "ROR");
});

// Defines a handle display renderer override
export const timestampOverride: RendererOverride<number> = (
    name: string,
    val: number,
    props: JsonDetailViewComponentProps
) => {
    // Just use the normal string renderer with a changed string value
    const renderedTime = timestampToLocalTime(val);
    const overriddenProps = { ...props, json: { name, value: renderedTime } };
    return stringRenderer(overriddenProps);
};

// Maps field name -> Override
export const STRING_RENDER_OVERRIDES: FieldRendererMap<string> = new Map([
    // IDs/handles that shouldn't resolve
    ["id", handleOverride],

    // Show the owner username as a special component
    ["owner_username", linkedUsernameOverride],

    // This field is only present when the link resolves and is injected by the
    // above override
    [
        "linked_person_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "PERSON",
            fieldnameOverride: "Linked Person",
        }),
    ],

    // Recursive resolvable IDs - i.e. registry items
    [
        "organisation_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "ORGANISATION",
            fieldnameOverride: "Organisation",
        }),
    ],
    [
        "publisher_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "ORGANISATION",
            fieldnameOverride: "Publisher",
        }),
    ],
    [
        "requesting_organisation_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "ORGANISATION",
            fieldnameOverride: "Requesting Organisation",
        }),
    ],
    [
        "software_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "MODEL",
            fieldnameOverride: "Model",
        }),
    ],
    [
        "modeller_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "PERSON",
            fieldnameOverride: "Modeller",
        }),
    ],
    [
        "dataset_template_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "DATASET_TEMPLATE",
            fieldnameOverride: "Dataset Template",
        }),
    ],
    [
        "dataset_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "DATASET",
            fieldnameOverride: "Dataset",
        }),
    ],
    [
        "template_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "DATASET_TEMPLATE",
            fieldnameOverride: "Dataset Template",
        }),
    ],
    [
        "workflow_template_id",
        subtypedIdResolverOverrideGenerator({
            subtype: "MODEL_RUN_WORKFLOW_TEMPLATE",
            fieldnameOverride: "Workflow Template",
        }),
    ],

    ["orcid", orcidOverride],
    ["ror", rorOverride],
    ["email", emailOverride],
    // the S3 URI field name override doesn't work - okay for now
    ["s3_uri", copyableOverride],
    ["bucket_name", copyableOverride],
    ["path", copyableOverride],

    // Show prov serialisation of model run as object

    //TODO determine if we want to show this or expand it to enable toggled view
    // ["prov_serialisation", serialisedJsonOverride],
]);

export const OBJECT_RENDER_OVERRIDES: FieldRendererMap<object> = new Map([]);

export const BOOLEAN_RENDER_OVERRIDES: FieldRendererMap<boolean> = new Map([]);

export const NUMBER_RENDER_OVERRIDES: FieldRendererMap<number> = new Map([
    ["updated_timestamp", timestampOverride],
    ["created_timestamp", timestampOverride],
    ["start_time", timestampOverride],
    ["end_time", timestampOverride],
]);
