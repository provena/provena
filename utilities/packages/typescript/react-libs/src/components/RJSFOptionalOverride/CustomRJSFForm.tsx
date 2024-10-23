import { withTheme } from "@rjsf/core";
import ObjectField from "./OptionalObjectField";
import ObjectFieldTemplate from "./OptionalObjectFieldTemplate";
import { Theme as MuiTheme } from "@rjsf/mui";

// override these two based on their base definitions in mui theme
MuiTheme.fields = { ...(MuiTheme.fields ?? {}), ObjectField };
MuiTheme.templates = { ...(MuiTheme.templates ?? {}), ObjectFieldTemplate };

export const Form = withTheme(MuiTheme);
