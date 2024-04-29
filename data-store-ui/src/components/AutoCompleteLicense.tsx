import { Autocomplete, Box, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import makeStyles from "@mui/styles/makeStyles";

/*
This component should be used as a replacement field in the rjsf (React Json Schema form)
component. It fills in the path value of the form using a lookup from the static 
assets bucket. In this bucket there is a list of licenses which include 'name', 
'title' and 'path' fields. This is presented as a drop down list. If a default value is
provided by the props.formData field then that will be used as the default value, otherwise
the first value in the list will be used (copyright reserved for now.)
*/

// Selected list item type
interface CurrentSelection {
  name?: string;
  title?: string;
  path?: string;
  error: boolean;
  loading: boolean;
}

// Responses from the API
interface ResponseItem {
  name: string;
  title: string;
  path: string;
}

// The response object shape from API
interface ResponseObject {
  licenses: ResponseItem[];
}

// Theme to align helper text properly
const useStyles = makeStyles((theme) => ({
  helperText: {
    marginLeft: 0,
  },
}));

// Given the current selection returns the text that should be rendered
const renderLabelText = (value: CurrentSelection) => {
  if (value.error) {
    return "An error occurred while loading the license list...";
  } else if (value.loading) {
    return "Loading...";
  } else {
    var partsList: string[] = [];

    // Add to potential info
    if (value.path) {
      partsList.push(value.path);
    }
    if (value.name) {
      partsList.push(value.name);
    }
    if (value.title) {
      partsList.push(value.title);
    }

    // Render
    return partsList.join(" - ");
  }
};

const AutoCompleteLicense = (props: any) => {
  // Setup theming
  const classes = useStyles();
  // options list
  const [options, setOptions] = useState<CurrentSelection[]>([
    // Sets the initial options list
    { error: false, loading: true },
  ]);

  // Configure initial value of the license selection
  var initialValue: CurrentSelection;

  // If the props has valid data in it, assume this is
  // correct and display
  if (props.formData && props.formData !== "") {
    initialValue = {
      path: props.formData,
      error: false,
      loading: false,
    };
  } else {
    // There is no input default data so use
    // loading value initially and update in setup
    initialValue = {
      loading: true,
      error: false,
    };
  }

  // Set current value with initialValue
  const [currentValue, setCurrentValue] = useState<
    CurrentSelection | undefined
  >(initialValue);

  // What happens when an item is selected?
  const submitChanges = (value: CurrentSelection) => {
    // Warning in case of invalid path - not well handled as seems like edge case
    // And validation will pick it up
    if (!value.path) {
      console.log("Trying to set license without path!");
    }
    // Default to ""
    const path = value.path ?? "";

    // Set the value and notify form of update
    setCurrentValue(value);
    props.onChange(path);
  };

  // Setup the initial license option list after initial load
  useEffect(() => {
    fetch(`https://static.rrap-is.com/assets/cc_licenses.json`)
      .then((res) => res.json())
      .then((json) => {
        // Get json API response
        let parsedJson = json as ResponseObject;
        // Parse as response object and transform objects
        let optionsList: CurrentSelection[] = parsedJson.licenses.map(
          (resItem: ResponseItem) => ({
            name: resItem.name,
            path: resItem.path,
            title: resItem.title,
            loading: false,
            error: false,
          }),
        );
        // Update options list from API
        setOptions(optionsList);

        // If no license is selected then choose the first item
        // And let the form know
        if (!currentValue || currentValue.loading) {
          submitChanges(optionsList[0]);
        }
      })
      .catch((e) => {
        // Set error option
        setOptions([
          {
            error: true,
            loading: false,
          },
        ]);
      });
  }, []);
  return (
    <div className="">
      <Autocomplete
        options={options}
        // Default to loading object if no value provided
        value={
          currentValue ?? {
            loading: true,
            error: false,
          }
        }
        onChange={(ele, value) => {
          // If no value then we provide an empty
          // path meaning cleared selection
          submitChanges(
            value ?? {
              path: "",
              error: false,
              loading: false,
            },
          );
        }}
        // What text?
        getOptionLabel={(option: CurrentSelection) => {
          return renderLabelText(option);
        }}
        // What react component
        renderOption={(props, option) => (
          <Box component="li" {...props}>
            <p>{renderLabelText(option)}</p>
          </Box>
        )}
        // How is input rendered?
        renderInput={(params) => (
          <TextField
            // Force alignment properly
            FormHelperTextProps={{
              className: classes.helperText,
            }}
            required={props.required}
            {...params}
            label="Choose a license"
            helperText={props.schema.description}
          />
        )}
      />
    </div>
  );
};

export default AutoCompleteLicense;
