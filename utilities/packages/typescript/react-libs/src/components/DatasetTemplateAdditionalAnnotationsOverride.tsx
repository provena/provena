import { Typography, TextField, IconButton, Checkbox } from "@mui/material";
import { useState, useEffect, useRef } from "react";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Theme } from "@mui/material/styles";
import { FormGroup, FormControlLabel, Stack, Grid } from "@mui/material";
import RemoveIcon from "@mui/icons-material/Remove";
import AddIcon from "@mui/icons-material/Add";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    helperText: {
      marginLeft: 0,
    },
    clearButton: {
      "margin-bottom": theme.spacing(2),
      "margin-top": theme.spacing(2),
    },
  }),
);

// string to string map
type ListFormFormat = [string | undefined, string | undefined][];

type FormDataType = { [k: string]: string };

// The form data is an object, or undefined - which maps k:string -> string i.e.
// KVP
type FormData = FormDataType | undefined;

const formDataToListFormFormat = (formData: FormDataType): ListFormFormat => {
  /*
    Converts the form data type into the state list form format
    */
  const listForm: ListFormFormat = [];
  for (const key of Object.keys(formData)) {
    const val = formData![key];
    listForm.push([key, val]);
  }
  return listForm;
};

interface OverrideProps {
  // This is the form data passed from rjsf
  formData: FormData;

  // This is the change handler from rjsf
  onChange: (data: FormData) => void;

  // title and description for field.
  schema: {
    title: string;
    description: string;
  };

  // ui schema in case overrided
  uiSchema: {
    "ui:description"?: string;
  };

  // Is this required?
  required: boolean;
}

export const DatasetTemplateAdditionalAnnotationsOverride = (props: OverrideProps) => {
  /**
   * This form overrides the additional annotations fields in the dataset
   * template resources. The data in this form is held using a list of
   * [key,value] tuples, then interfaced with the parent object style data.
   * This is because it is simpler to work with a list rather than an object
   * when rendering the form. A checkbox is used to include/exclude this
   * field. The description/ui schema is rendered.
   */

  // Not currently used
  const classes = useStyles();

  // This ref keeps track of if the component has already mounted
  const didMount = useRef(false);

  // Form has data?
  const formHasData = !!props.formData;

  // Are there duplicate keys currently?
  const [duplicateKeysPresent, setDuplicateKeysPresent] =
    useState<boolean>(false);

  // Is this form enabled/selected?
  const [enabled, setEnabled] = useState<boolean>(
    formHasData && Object.keys(props.formData!).length > 0,
  );

  // This method transforms the props -> list form format in case data already
  // in form
  const deriveDefault = (props: OverrideProps): ListFormFormat => {
    if (formHasData) {
      return formDataToListFormFormat(props.formData!);
    } else {
      return [];
    }
  };

  // This is the list form of the data currently in the form
  const [listFormData, setListFormData] = useState<ListFormFormat>(
    deriveDefault(props),
  );

  const updateFormData = (
    newElem: [string | undefined, string | undefined],
    targetIndex: number,
  ): void => {
    /*
        This method updates the existing list form data by adding a new element
        at the specified postition. 

        NOTE this intentionally creates a new object so that the react component
        runs the useEffect hook to update the parent
        */
    setListFormData((old: ListFormFormat) => {
      const newFormData: ListFormFormat = [];
      const keyList: string[] = [];
      // Have we found a duplicate?
      var duplicateFound = false;
      old.forEach((elem, index) => {
        if (index === targetIndex) {
          const key = newElem[0];
          if (key) {
            if (keyList.indexOf(key) !== -1) {
              setDuplicateKeysPresent(true);
              duplicateFound = true;
            } else {
              keyList.push(key);
            }
          }
          newFormData.push(newElem);
        } else {
          const key = elem[0];
          if (key) {
            if (keyList.indexOf(key) !== -1) {
              setDuplicateKeysPresent(true);
              duplicateFound = true;
            } else {
              keyList.push(key);
            }
          }
          newFormData.push(elem);
        }
      });
      if (!duplicateFound) {
        setDuplicateKeysPresent(false);
      }
      return newFormData;
    });
  };

  const removeAtIndex = (targetIndex: number): void => {
    /*
        This method removes from the form data list format an item at the
        specified index.

        NOTE this intentionally creates a new object so that the react component
        runs the useEffect hook to update the parent
        */
    setListFormData((old: ListFormFormat) => {
      const newFormData: ListFormFormat = [];
      const keyList: string[] = [];
      // This method also updates the duplicate Found
      var duplicateFound = false;
      old.forEach((elem, index) => {
        if (index !== targetIndex) {
          const key = elem[0];
          if (key) {
            if (keyList.indexOf(key) !== -1) {
              setDuplicateKeysPresent(true);
              duplicateFound = true;
            } else {
              keyList.push(key);
            }
          }
          newFormData.push(elem);
        }
      });
      if (!duplicateFound) {
        setDuplicateKeysPresent(false);
      }
      if (newFormData.length === 0) {
        setEnabled(false);
      }
      return newFormData;
    });
  };

  const convertToObjectAndUpdate = (formData: ListFormFormat): void => {
    /**
     * This method converts the list form form data into the object style
     * required by the form, and runs the on change
     */

    // Iterate through all elements and add key/value
    const newFormData: FormData = {};
    formData.forEach((elem) => {
      let key = elem[0];
      let value = elem[1];
      if (key && value) {
        newFormData[key] = value;
      }
    });
    if (Object.keys(newFormData).length === 0) {
      props.onChange(undefined);
    } else {
      props.onChange(newFormData);
    }
  };

  // Update the form when the new form data changes
  useEffect(
    () => {
      // don't run on first mount to avoid upsetting rjsf
      if (!didMount.current) {
        // we've mounted now
        didMount.current = true;
        return;
      }
      convertToObjectAndUpdate(listFormData);
    },
    // Only run this use effect when the form data changes
    [listFormData],
  );

  const addEmptyItem = () => {
    /**
        Helper method which adds a new empty item to the list form data (e.g.
        plus button) 
         */
    setListFormData((old: ListFormFormat) => {
      old.push([undefined, undefined]);
      const newFormData = [];
      for (const keyValue of old) {
        newFormData.push(keyValue);
      }
      return newFormData;
    });
  };

  return (
    <div>
      {
        // Stack based layout
      }
      <Stack spacing={2.5} padding={2}>
        <Grid
          container
          justifyContent="flex-start"
          spacing={3}
          alignItems="center"
        >
          {
            // Title and description
          }
          <Grid item xs={5}>
            <Typography variant="h6">{props.schema.title}</Typography>
            <Typography variant="subtitle1">
              {props.uiSchema["ui:description"] ?? props.schema.description}
            </Typography>
          </Grid>

          {
            // Enabled checkbox
          }
          <Grid item>
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={enabled}
                    onChange={() => {
                      // If enabling for the first time, add an item
                      if (
                        !enabled &&
                        (!listFormData || listFormData.length === 0)
                      ) {
                        addEmptyItem();
                      }
                      setEnabled(!enabled);
                    }}
                  />
                }
                label="Add annotations?"
              />
            </FormGroup>
          </Grid>
        </Grid>

        {
          // Main form/warning for duplicate keys
        }
        {enabled && (
          <>
            {duplicateKeysPresent && (
              <Grid container justifyContent="center">
                <Grid item>
                  <Typography variant="subtitle1">
                    <b>Warning: duplicate keys present</b>
                  </Typography>
                </Grid>
              </Grid>
            )}
            {
              // Map each k,v in the list form data into two text fields
            }
            {listFormData.map((keyValue, itemIndex) => {
              const key = keyValue[0];
              const value = keyValue[1];
              return (
                <Grid
                  container
                  key={itemIndex}
                  spacing={2}
                  justifyContent="center"
                  alignItems="center"
                >
                  <Grid item xs={2}>
                    <TextField
                      label="key"
                      value={key ?? ""}
                      onChange={(e) => {
                        const newElem: [
                          string | undefined,
                          string | undefined,
                        ] = [e.target.value as string, value];
                        updateFormData(newElem, itemIndex);
                      }}
                    ></TextField>
                  </Grid>
                  <Grid item flexGrow={1}>
                    <TextField
                      label="value"
                      fullWidth
                      value={value ?? ""}
                      disabled={duplicateKeysPresent}
                      onChange={(e) => {
                        const newElem: [
                          string | undefined,
                          string | undefined,
                        ] = [key, e.target.value as string];
                        updateFormData(newElem, itemIndex);
                      }}
                    ></TextField>
                  </Grid>

                  <Grid item xs={2}>
                    <Grid container justifyContent="flex-start">
                      {
                        // Delete button for the entry
                      }
                      <Grid item>
                        <IconButton
                          onClick={() => {
                            removeAtIndex(itemIndex);
                          }}
                        >
                          <RemoveIcon fontSize="large" />
                        </IconButton>
                      </Grid>
                      {
                        // Add plus button if last one
                      }
                      {itemIndex === listFormData.length - 1 && (
                        <Grid item>
                          <IconButton
                            onClick={() => {
                              addEmptyItem();
                            }}
                          >
                            <AddIcon fontSize="large" />
                          </IconButton>
                        </Grid>
                      )}
                    </Grid>
                  </Grid>
                </Grid>
              );
            })}
          </>
        )}
      </Stack>
    </div>
  );
};