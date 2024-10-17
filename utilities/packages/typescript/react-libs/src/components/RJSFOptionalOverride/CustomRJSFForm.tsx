import ErrorIcon from "@material-ui/icons/Error";
import ErrorOutlineIcon from "@material-ui/icons/ErrorOutline";
import { List, ListItem, Paper, Stack, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { withTheme } from "@rjsf/core";
import { Theme as MuiTheme } from "@rjsf/mui";
import { ErrorListProps } from "@rjsf/utils";
import ObjectField from "./OptionalObjectField";
import ObjectFieldTemplate from "./OptionalObjectFieldTemplate";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    interactionContainer: {
      padding: theme.spacing(1),
    },
    interactionPanel: {
      display: "flex",
      justifyContent: "space-around",
      alignItems: "center",
      backgroundColor: "white",
      padding: theme.spacing(1),
      borderRadius: 5,
    },
    mainActionButton: {
      marginBottom: theme.spacing(2),
      width: "40%",
    },
    stackContainer: {
      backgroundColor: "white",
      borderRadius: 5,
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
      paddingTop: theme.spacing(1),
      paddingBottom: theme.spacing(1),
    },
    errorListContainer: {
      backgroundColor: "#FFF5F5", // Light pink background
      borderRadius: theme.shape.borderRadius,
      padding: theme.spacing(2),
      marginBottom: theme.spacing(2),
      border: "1px solid #FFA5A5", // Light red border
    },
    errorListTitle: {
      color: "#D32F2F", // Dark red color for title
      marginBottom: theme.spacing(2),
      display: "flex",
      alignItems: "center",
      fontWeight: 600,
    },
    errorListSubtitle: {
      color: theme.palette.common.black, // Dark red color for title
      marginBottom: theme.spacing(2),
      display: "flex",
      alignItems: "center",
      fontWeight: 500,
    },
    errorIcon: {
      marginRight: theme.spacing(1),
      fontSize: "30px",
      color: "#D32F2F", // Dark red color for icon
    },
    errorListList: {
      padding: 0,
    },
    errorListItem: {
      backgroundColor: "#FFFFFF", // White background for each item
      borderRadius: theme.shape.borderRadius,
      marginBottom: theme.spacing(1),
      padding: theme.spacing(1.5, 2),
      boxShadow: "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
      border: "1px solid #FFCCCB", // Very light red border
      "&:last-child": {
        marginBottom: 0,
      },
    },
    errorText: {
      fontFamily: "monospace",
      wordBreak: "break-word",
      color: "#424242", // Dark grey for error text
    },
  })
);

/**
 * Stylizes an error property string by transforming dot notation and array indices
 * into a more readable format.
 *
 * @param property - The error property string to stylize.
 * @returns A stylized version of the property string, or the original string if stylization fails.
 *
 * @example
 * // Returns "inputs[0] -> resources -> deferred"
 * stylizeErrorProperty(".inputs.0.resources.deferred")
 *
 * @example
 * // Returns "data -> items[2] -> name"
 * stylizeErrorProperty("data.items.2.name")
 *
 * @example
 * // Returns the original string if stylization fails
 * stylizeErrorProperty("invalid..property")
 */
function stylizeErrorProperty(property: string): string {
  try {
    // Remove leading dot if present
    const trimmedProperty = property.replace(/^\./, "");

    // Split the property string into parts
    const parts = trimmedProperty.split(".");

    // Transform each part
    const transformedParts = parts.map((part, index) => {
      // Check if the part is a number (array index)
      if (/^\d+$/.test(part)) {
        // If the previous part exists and isn't already an array notation
        if (index > 0 && !parts[index - 1].endsWith("]")) {
          return `[${part}]`;
        }
      }
      return part;
    });

    // Join the parts with " -> " and replace ".[]" with "[]"
    return transformedParts.join(" -> ").replace(/\.\[/g, "[");
  } catch (error) {
    // If any error occurs during the process, return the original string
    return property;
  }
}

function ErrorListTemplate({ errors }: ErrorListProps) {
  const classes = useStyles();

  return (
    <Paper className={classes.errorListContainer} elevation={0}>
      <Typography variant="h6" className={classes.errorListTitle}>
        <ErrorOutlineIcon className={classes.errorIcon} />
        Your form has errors!
      </Typography>
      <Typography variant="subtitle1" className={classes.errorListSubtitle}>
        Your form could not be validated. The errors are listed below. Please
        correct these errors before submitting the form.
      </Typography>
      <List className={classes.errorListList}>
        {errors.map((error, index) => (
          <ListItem key={index} className={classes.errorListItem}>
            <Stack
              direction="row"
              justifyItems={"flex-start"}
              spacing={2}
              alignItems="center"
            >
              <ErrorIcon color="action" />
              <Typography variant="body2" className={classes.errorText}>
                <b>{stylizeErrorProperty(error.property ?? "Form")}</b>
                <br />
                {error.message}
              </Typography>
            </Stack>
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}

// override these two based on their base definitions in mui theme
MuiTheme.fields = {
  ...(MuiTheme.fields ?? {}),
  ObjectField,
};
MuiTheme.templates = {
  ...(MuiTheme.templates ?? {}),
  ObjectFieldTemplate,
  ErrorListTemplate,
};

export const Form = withTheme(MuiTheme);
