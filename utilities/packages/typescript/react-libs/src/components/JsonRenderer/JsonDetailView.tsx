import React from "react";
import { RendererMap } from "./JsonTypeRenderers";

/**
    This page contains the JsonDetailView component which is a dispatcher against:
    - renderers in the JsonTypeRenderers file
    - overrides in the JsonRendererOverrides file
    - auto detectors for overrides in the JsonOverrideDetectors file
 */

// These are the types of values JSON can have for our purposes
export type JsonTypes =
  | number
  | string
  | boolean
  | null
  | undefined
  | { [k: string]: JsonTypes }
  | Array<JsonTypes>;

// This is a enum to help dispatching against these types
export type JsonTypeOptions =
  | "number"
  | "string"
  | "boolean"
  | "nullundefined"
  | "object"
  | "array";

export interface JsonData {
  // Field name (optional if top level of JSON object)
  name: string | undefined;
  // Field value
  value: JsonTypes;
}

// Stack = Heading over Content (two rows, one column)
// Column = Heading next to Content (one row, two columns)
export type DetailLayoutOptions = "stack" | "column";

export interface ColumnLayoutConfig {
  // Final value := base - columnSpace/2
  propertyNameBase: number;
  propertyValueBase: number;
  columnSpace: number;
}

// Constants/defaults
export const DEFAULT_COLUMN_SPACING = 1;
export const DEFAULT_PROPERTY_NAME_WIDTH = 3;
export const DEFAULT_PROPERTY_VALUE_WIDTH = 12 - DEFAULT_PROPERTY_NAME_WIDTH;

export const DEFAULT_LAYOUT_CONFIG: ColumnLayoutConfig = {
  propertyNameBase: DEFAULT_PROPERTY_NAME_WIDTH,
  propertyValueBase: DEFAULT_PROPERTY_VALUE_WIDTH,
  columnSpace: DEFAULT_COLUMN_SPACING,
};

export interface StylingData {
  // What color style string to use
  color: string;
  // What layout option - stack or column
  layout: DetailLayoutOptions;
  // If column above can optionally override default column sizes
  layoutConfig?: ColumnLayoutConfig;
}

export type ContextArray = string[];
export interface JsonContext {
  // The list of field names - empty if top level - from highest to lowest
  fields: ContextArray;
}

export interface JsonDetailViewComponentProps {
  // To render we require the data + the style
  json: JsonData;
  style: StylingData;
  context: JsonContext;
}

// Define a set of renderer overrides for the various types

// A renderer takes the name/val combination
export type RendererOverride<T> = (
  name: string,
  val: T,
  props: JsonDetailViewComponentProps,
) => JSX.Element | null;

export type RendererAndExclusions<T> = {
  renderer: RendererOverride<T>;
  exclusions?: Array<string>;
};
export type AllFieldRendererMap<T> = Map<string, RendererAndExclusions<T>>;
export type PathedRendererMap<T> = Map<string, RendererOverride<T>>;

// An override detector uses the value to determine a renderer override if any
export type OverrideDetector<T> = (
  name: string,
  value: T,
) => RendererOverride<T> | undefined;

// A list of detectors of some type
export type OverrideDetectorList<T> = Array<OverrideDetector<T>>;

export function checkForAutoDetectors<T>(
  detectorList: OverrideDetectorList<T>,
  name: string,
  value: T,
): RendererOverride<T> | undefined {
  /**
    Checks a detector list and returns a renderer of corresponding type if any
    detection was successful. 
     */
  for (const detector of detectorList) {
    let possibleDetector = detector(name, value);
    if (possibleDetector !== undefined) {
      return possibleDetector;
    }
  }
  return undefined;
}

export type JsonRenderer = (
  props: JsonDetailViewComponentProps,
) => JSX.Element | null;

const resolveRenderer = (data: JsonData): JsonRenderer | undefined => {
  /**
     Determines the correct JsonRenderer based on the type. 

     Note that arrays are also objects so we need to use the Array.isArray
     method.
     */
  const value = data.value;

  // Always check directly for null/undefined-  appears to be more reliable
  // than using typeof
  if (value === undefined || value === null) {
    return RendererMap.get("nullundefined");
  } else {
    switch (typeof value) {
      case "number": {
        return RendererMap.get("number");
      }
      case "string": {
        return RendererMap.get("string");
      }
      case "boolean": {
        return RendererMap.get("boolean");
      }
      case "undefined": {
        return RendererMap.get("nullundefined");
      }
      case "object": {
        if (Array.isArray(value)) {
          return RendererMap.get("array");
        } else {
          return RendererMap.get("object");
        }
      }
      default: {
        return undefined;
      }
    }
  }
};

export const JsonDetailViewComponent = (
  props: JsonDetailViewComponentProps,
) => {
  /**
    Component: JsonDetailViewComponent

    Renders a pretty print of JSON data.

    The process is to split rendering depending on object type using handlers
    for each. 

    There is also a system for both auto detected and manually specified
    overrides. 

    Overrides are per type and should be resolved and called from the respective
    renderer.

    The architecture:

    - resolve the renderer based on the type 
    - each type dispatches to an enum which maps to a renderer
    - each type has a list of overrides and override detectors - overrides are
      manually specified from the field name, detectors take the name/value and
      can apply overrides if desired
    - all overrides respect the layout (column vs stack) and the colour scheme
    - objects/array can recursively call the detail view on the sub parts to
      resolve nested parts


    GOTCHAS:

    - If the structural contents of the JSON change dynamically then we could
      have accidental conditional hook ordering when changed. Ensure that the
      top level component is keyed uniquely against the contents so that react
      doesn't rerender the item. This will force a remount. E.g. if using to
      display an item which changes use the item ID + history ID (if relevant)
      id as the keys.
    */

  // get the relevant renderer
  const renderer = resolveRenderer(props.json);

  // Fall through in case renderer resolution fails
  if (renderer === undefined) {
    return <p>Cannot render this type of value...</p>;
  }

  // Otherwise we can confidently render the contents
  const renderedContent = renderer(props);

  return <React.Fragment>{renderedContent}</React.Fragment>;
};
