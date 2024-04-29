import { Grid, Stack, Theme, Typography } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { prettifyRecordName } from "../../util/util";
import {
  ColumnLayoutConfig,
  DEFAULT_LAYOUT_CONFIG,
  JsonContext,
  JsonDetailViewComponent,
  JsonDetailViewComponentProps,
  JsonRenderer,
  JsonTypeOptions,
  JsonTypes,
  StylingData,
  checkForAutoDetectors,
} from "./JsonDetailView";
import {
  BOOLEAN_AUTO_DETECTORS,
  NUMBER_AUTO_DETECTORS,
  OBJECT_AUTO_DETECTORS,
  STRING_AUTO_DETECTORS,
} from "./JsonOverrideDetectors";
import {
  ARRAY_RENDER_OVERRIDES,
  ARRAY_RENDER_PATH_OVERRIDES,
  BOOLEAN_RENDER_OVERRIDES,
  BOOLEAN_RENDER_PATH_OVERRIDES,
  NUMBER_RENDER_OVERRIDES,
  NUMBER_RENDER_PATH_OVERRIDES,
  STRING_RENDER_OVERRIDES,
  STRING_RENDER_PATH_OVERRIDES,
  buildPath,
  checkFieldRenderWithPossibleExclusion,
} from "./JsonRendererOverrides";

/**
    This file contains a set of renderers which act against specific value
    types. 

    All make use of the generateStandardGrid helper function which takes the
    styling info and resolves into the appropriate stack/column layout.

    The job of the renderer is therefore to supply LH/RH content (or
    top/bottom).

    The renderers also must dispatch to any overrides (manual or detected) for
    it's type.

    Some renderers are recursive against the detail view e.g. Object/Array
    renderer.

    NOTE the name field can be undefined - this implies that we are being asked
    to render from the top level of a JSON Object or Array. If the name is
    undefined for other data types then an error is displayed.
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
  }),
);

export const ROW_GAP = 1.5;
export const OBJECT_PADDING = "25px";

export interface ColumnWidths {
  heading: number;
  value: number;
}
export const deriveColumnWidths = (style: StylingData): ColumnWidths => {
  /**
   * Based on the styling config, determine the heading/value column widths.
   */

  // Layout variables (set to defaults)
  var appliedLayout: ColumnLayoutConfig =
    style.layoutConfig !== undefined
      ? style.layoutConfig
      : DEFAULT_LAYOUT_CONFIG;

  // Column layout uses slightly spaced apart columns
  const columnHeadingWidth =
    appliedLayout.propertyNameBase - appliedLayout.columnSpace / 2.0;
  const columnValueWidth =
    appliedLayout.propertyValueBase - appliedLayout.columnSpace / 2.0;

  // Stack layout just uses the full width
  const stackLayoutWidth = 12;

  var headingWidth = columnHeadingWidth;
  var valueWidth = columnValueWidth;

  switch (style.layout) {
    case "column": {
      headingWidth = columnHeadingWidth;
      valueWidth = columnValueWidth;
      break;
    }
    case "stack": {
      headingWidth = stackLayoutWidth;
      valueWidth = stackLayoutWidth;
      break;
    }
  }

  return { heading: headingWidth, value: valueWidth };
};

export interface GenerateStandardGridInput {
  // Style config
  style: StylingData;

  // LH
  lhContent: JSX.Element;
  lhClassName?: string;

  // RH
  rhContent: JSX.Element;
  rhClassName?: string;

  // Override grid class name?
  gridClassName?: string;
}

export function generateStandardGrid(
  inputs: GenerateStandardGridInput,
): JSX.Element {
  /**
    Function: GenerateStandardGrid

    Generates the recommended grid layout - allows specification of the content
    (JSX Element) for the LH/RH (or stacks)
    */

  // determine column widths from layout
  const widths = deriveColumnWidths(inputs.style);

  // Grid class

  return (
    <Grid
      container
      item
      xs={12}
      justifyContent="space-between"
      className={inputs.gridClassName}
      rowGap={ROW_GAP}
      style={{ width: "100%" }}
    >
      <Grid item xs={widths.heading} style={{ width: "100%" }}>
        {inputs.lhContent}
      </Grid>
      <Grid
        container
        item
        xs={widths.value}
        style={{ width: "100%" }}
        sx={{ color: inputs.style.color ?? "inherit" }}
      >
        {inputs.rhContent}
      </Grid>
    </Grid>
  );
}

export const genericStyledRenderer = (inputs: {
  lhContent: JSX.Element;
  rhContent: JSX.Element;
  style: StylingData;
}): JSX.Element => {
  // basic helper function which wraps the generate standard grid as a renderer
  return generateStandardGrid({ ...inputs });
};

/*
==============
TYPE RENDERERS
==============
*/
export const stringRenderer: JsonRenderer = (
  props: JsonDetailViewComponentProps,
): JSX.Element | null => {
  const classes = useStyles();

  // Check for undefined name
  if (props.json.name === undefined) {
    console.error(
      "Was not expecting undefined name for string value in detail view.",
    );
    return null;
  }

  // Pull out and case key/val
  const key = prettifyRecordName(props.json.name);
  const val = props.json.value as string;

  // Check for a direct or auto renderer override
  const relevantPath = buildPath([
    buildPath(props.context.fields),
    props.json.name,
  ]);
  const override =
    // Pathed render
    STRING_RENDER_PATH_OVERRIDES.get(relevantPath) ??
    // Field name render with possible exclusions
    checkFieldRenderWithPossibleExclusion<string>({
      renderMap: STRING_RENDER_OVERRIDES,
      context: relevantPath,
      fieldName: props.json.name,
    }) ??
    checkForAutoDetectors<string>(STRING_AUTO_DETECTORS, props.json.name, val);
  if (override !== undefined) {
    return override(props.json.name, val, props);
  }

  // LH Content
  const lhContent = <Typography className={classes.boldText}>{key}</Typography>;

  // RH Content
  const rhContent = (
    <Typography className={classes.valueText}>{val}</Typography>
  );

  return genericStyledRenderer({
    style: props.style,
    lhContent,
    rhContent,
  });
};
export const numberRenderer = (
  props: JsonDetailViewComponentProps,
): JSX.Element | null => {
  const classes = useStyles();

  // Pull out and case key/val
  if (props.json.name === undefined) {
    console.error(
      "Was not expecting undefined name for number value in detail view.",
    );
    return null;
  }

  // Pull out and case key/val
  const key = prettifyRecordName(props.json.name);
  const val = props.json.value as number;

  // Check for a direct or auto renderer override
  const relevantPath = buildPath([
    buildPath(props.context.fields),
    props.json.name,
  ]);
  const override =
    NUMBER_RENDER_PATH_OVERRIDES.get(relevantPath) ??
    // Field name render with possible exclusions
    checkFieldRenderWithPossibleExclusion<number>({
      renderMap: NUMBER_RENDER_OVERRIDES,
      context: relevantPath,
      fieldName: props.json.name,
    }) ??
    checkForAutoDetectors<number>(NUMBER_AUTO_DETECTORS, props.json.name, val);
  if (override !== undefined) {
    return override(props.json.name, val, props);
  }

  // LH Content
  const lhContent = <Typography className={classes.boldText}>{key}</Typography>;

  // RH Content
  const rhContent = (
    <Typography className={classes.valueText}>{val}</Typography>
  );

  return genericStyledRenderer({
    style: props.style,
    lhContent,
    rhContent,
  });
};
export const booleanRenderer = (
  props: JsonDetailViewComponentProps,
): JSX.Element | null => {
  const classes = useStyles();

  // Pull out and case key/val
  if (props.json.name === undefined) {
    console.error(
      "was not expecting undefined name for straight boolean value in detail view.",
    );
    return null;
  }

  const key = prettifyRecordName(props.json.name);
  const val = props.json.value as boolean;

  // Check for a direct or auto renderer override
  const relevantPath = buildPath([
    buildPath(props.context.fields),
    props.json.name,
  ]);
  const override =
    BOOLEAN_RENDER_PATH_OVERRIDES.get(relevantPath) ??
    // Field name render with possible exclusions
    checkFieldRenderWithPossibleExclusion<boolean>({
      renderMap: BOOLEAN_RENDER_OVERRIDES,
      context: relevantPath,
      fieldName: props.json.name,
    }) ??
    checkForAutoDetectors<boolean>(
      BOOLEAN_AUTO_DETECTORS,
      props.json.name,
      val,
    );
  if (override !== undefined) {
    return override(props.json.name, val, props);
  }

  // LH Content
  const lhContent = <Typography className={classes.boldText}>{key}</Typography>;

  // RH Content
  const rhContent = (
    <Typography className={classes.valueText}>{val.toString()}</Typography>
  );

  return genericStyledRenderer({
    style: props.style,
    lhContent,
    rhContent,
  });
};
export const nullundefinedRenderer = (
  props: JsonDetailViewComponentProps,
): JSX.Element | null => {
  // Don't render null content
  return null;
};

export const objectRendererBoxer = (inputs: {
  interior: JSX.Element;
  style: StylingData;
}) => {
  return (
    <div
      style={{
        padding: OBJECT_PADDING,
        border: `1px dotted ${inputs.style.color}`,
        borderRadius: "8px",
        width: "100%",
      }}
    >
      {inputs.interior}
    </div>
  );
};

export const appendContext = (inputs: {
  name: string;
  context: JsonContext;
}): JsonContext => {
  const { name, context } = inputs;
  const newContext: JsonContext = JSON.parse(JSON.stringify(context));
  newContext.fields.push(name);
  return newContext;
};

export const objectRenderer = (
  props: JsonDetailViewComponentProps,
): JSX.Element => {
  const classes = useStyles();

  // This is a map from string to other JSON content
  const val = props.json.value as { [k: string]: JsonTypes };

  // This is a top level unnamed object - just compose with gaps the detail
  // view of each part
  if (props.json.name === undefined) {
    return (
      <Stack direction="column" spacing={ROW_GAP}>
        {Object.entries(val).map((keyVal, index) => {
          const key = keyVal[0];
          const val = keyVal[1];
          return (
            <JsonDetailViewComponent
              json={{ name: key, value: val }}
              style={props.style}
              context={props.context}
            />
          );
        })}
      </Stack>
    );
  }

  // We are not at top level and we have a name - standard display
  const key = prettifyRecordName(props.json.name);

  // new context
  const newContext = appendContext({
    name: props.json.name,
    context: props.context,
  });

  // LH Content
  const lhContent = <Typography className={classes.boldText}>{key}</Typography>;

  // RH Content -> the lower level is just the result of boxing the result of
  // rendering a top level object -> hence the recursive call with the name stripped
  const rhContent = objectRendererBoxer({
    style: props.style,
    interior: objectRenderer({
      ...props,
      json: { ...props.json, name: undefined },
      context: newContext,
    }),
  });

  return genericStyledRenderer({
    // force a stack layout for object
    style: { ...props.style, layout: "stack" },
    lhContent,
    rhContent,
  });
};
export const arrayRenderer = (
  props: JsonDetailViewComponentProps,
): JSX.Element | null => {
  const classes = useStyles();

  // This is a map from string to other JSON content
  const val = props.json.value as Array<JsonTypes>;
  const emptyString = "No entries";

  // override
  // Check for a direct or auto renderer override
  if (props.json.name !== undefined) {
    const relevantPath = buildPath([
      buildPath(props.context.fields),
      props.json.name,
    ]);
    const override =
      ARRAY_RENDER_PATH_OVERRIDES.get(relevantPath) ??
      // Field name render with possible exclusions
      checkFieldRenderWithPossibleExclusion<object>({
        renderMap: ARRAY_RENDER_OVERRIDES,
        context: relevantPath,
        fieldName: props.json.name,
      }) ??
      checkForAutoDetectors<object>(
        OBJECT_AUTO_DETECTORS,
        props.json.name,
        val,
      );

    if (override !== undefined) {
      return override(props.json.name, val, props);
    }
  }

  const newContext =
    props.json.name === undefined
      ? props.context
      : appendContext({
          name: props.json.name!,
          context: props.context,
        });

  // Start by removing any null or defined entries
  const filtered = val.filter((e) => {
    return !(e === undefined || e === null);
  });

  // Return a string rendering instead for empty arrays
  if (filtered.length === 0) {
    return stringRenderer({
      ...props,
      json: { name: props.json.name, value: emptyString },
    });
  }

  // Assuming we have entries - what type are they
  // TODO don't assume that all items are of the same type...
  const exampleEntry = filtered[0];
  const entryType = typeof exampleEntry;

  // Serialisable types
  if (
    entryType === "string" ||
    entryType === "boolean" ||
    entryType === "number"
  ) {
    // We can just list these using a string renderer
    return stringRenderer({
      ...props,
      json: { name: props.json.name, value: filtered.toString() },
    });
  } else {
    // In the case that we have an object - render a stack of boxed objects
    const rhContent = (
      <Stack direction="column" spacing={ROW_GAP} style={{ width: "100%" }}>
        {filtered.map((entry) => {
          const interiorContent = (
            <JsonDetailViewComponent
              json={{ name: undefined, value: entry }}
              style={props.style}
              // Inject context here since we strip name
              context={newContext}
            />
          );
          return objectRendererBoxer({
            interior: interiorContent,
            style: props.style,
          });
        })}
      </Stack>
    );

    // Are we looking at field or a top level?
    if (props.json.name === undefined) {
      // Just return the RH content
      return rhContent;
    } else {
      // return the layout embedded RH content

      // LH Content
      const lhContent = (
        <Typography className={classes.boldText}>
          {prettifyRecordName(props.json.name)}
        </Typography>
      );

      return genericStyledRenderer({
        // force a stack layout for object
        style: { ...props.style, layout: "stack" },
        lhContent,
        rhContent,
      });
    }
  }
};

export const RendererMap: Map<JsonTypeOptions, JsonRenderer> = new Map([
  // This maps the json type into a renderer for that type
  ["string", stringRenderer],
  ["number", numberRenderer],
  ["boolean", booleanRenderer],
  ["nullundefined", nullundefinedRenderer],
  ["object", objectRenderer],
  ["array", arrayRenderer],
]);
