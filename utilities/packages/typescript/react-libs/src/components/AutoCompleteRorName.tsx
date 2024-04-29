import {
  Autocomplete,
  Box,
  Button,
  FormGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import makeStyles from "@mui/styles/makeStyles";
import { useQuery } from "@tanstack/react-query";
import { debounce } from "lodash";
import React, { useState } from "react";

/*
This component should be used as a replacement field in the rjsf (React Json Schema form)
component. It provides a lookup into the ROR registry for institutions using the search 
API. This means that the user can type in CSIRO for example and select the correct ROR
which is a machine readable unique identifier for an organisation. The props.formData 
will be used as the default selection where possible.  
*/

// Theme to align helper text properly
const useStyles = makeStyles((theme) => ({
  helperText: {
    marginLeft: 0,
  },
  clearButton: {
    "margin-bottom": theme.spacing(3),
  },
}));

interface RORResponseItem {
  name: string;
  id: string;
  country: {
    country_name: string;
  };
  acronyms: string[];
}

// Definition of an option item in the options list
interface OptionsType {
  name: string;
  id?: string;
  country?: string;
  acronyms?: string[];
  error: boolean;
}

// Definition of the current selection/value
interface SelectionValue {
  name?: string;
  ror?: string;
}

// Definition of the fields from the generated props
// that we are interested in
interface AutoCompleteRorNameProps {
  // Provides the current value
  // of the form - displays as selection
  // if present
  formData: SelectionValue;

  // Function to be called when changed
  onChange: (data: SelectionValue) => void;
  // Schema description for this sub component
  schema: {
    title: string;
    description: string;
    properties: {
      name: {
        title: string;
        description: string;
        required: boolean;
      };
      ror: {
        title: string;
        description: string;
        required: boolean;
      };
    };
  };
  // Does this need to be displayed?
  required: boolean;

  // ui schema in case overrided
  uiSchema: {
    "ui:description"?: string;
  };
}

export const AutoCompleteRorName = (props: AutoCompleteRorNameProps) => {
  const classes = useStyles();

  // link to ROR
  const rorLink = "https://ror.org/";

  // has the user requested to manually enter ROR/name?
  const [manualOverride, setManualOverride] = useState<boolean>(false);

  // Pickup the input value from the props
  // if provided
  const [searchInput, setSearchInput] = useState<string>("");

  // debounce the input
  const debounceTimeout = 300;
  const debouncedSetSearchInput = debounce(setSearchInput, debounceTimeout);

  // fetch cache
  const cacheTime = 60000;

  // This is used to let the form know that a selection was made
  // This is made from the list of options
  const submitChanges = (selectedOption: OptionsType) => {
    console.log(selectedOption);
    if (!selectedOption.error) {
      if (!selectedOption.id) {
        console.log("Selected option had no id!");
      }
      let selectedValue: SelectionValue = {
        name: selectedOption.name,
        ror: selectedOption.id ?? "",
      };
      props.onChange(selectedValue);
    }
  };

  // This is used to update the list of options as the API requests are made
  // based on the inputted string
  const queryRor = (query: string): Promise<OptionsType[]> => {
    let encodedSearchInput = encodeURIComponent(query);
    return fetch(
      `https://api.ror.org/organizations?query=${encodedSearchInput}&page=1&filter=country.country_code:AU`,
    )
      .then((res) => res.json())
      .then((json) => {
        // Parse the response as list of
        // ROR responses
        let items = json["items"] as RORResponseItem[];

        return items.map((ele: RORResponseItem) => {
          return {
            name: ele.name,
            id: ele.id,
            country: ele.country.country_name,
            acronyms: ele.acronyms,
            error: false,
          } as OptionsType;
        });
      })
      .catch((e) => {
        return [
          {
            name: "Experienced an error while loading ...",
            error: true,
          },
        ];
      });
  };

  const { isFetching, isSuccess, data } = useQuery({
    queryKey: ["ror", searchInput],
    queryFn: () => {
      return queryRor(searchInput);
    },
    // only run search if non zero input + not in manual override mode
    enabled: searchInput.length > 0 && !manualOverride,
    staleTime: cacheTime,
  });

  const renderLabel = (option: OptionsType) => {
    // Error label
    if (option.error) {
      return option.name;
    }
    // Otherwise - render properly
    return `${option.country ?? "Unknown Country"} - ${option.name} ${
      (option.acronyms &&
        option.acronyms.length > 0 &&
        "(" + option.acronyms.join(",") + ")") ||
      ""
    } : ${option.id ?? ""}`;
  };

  // Use the latest retrieved data from react query as the options type
  var options: OptionsType[] = [];

  if (isSuccess) {
    options = data ?? ([] as OptionsType[]);
  }

  // This defines the viewed input component
  return (
    <div className="">
      {
        // If there is existing formData include here
      }
      {props.formData.name && !manualOverride ? (
        <React.Fragment>
          <p>
            {" "}
            <b>Selected publisher name : </b>
            {props.formData.name}
            <br />{" "}
            {props.formData.ror && (
              <b>
                Selected publisher{" "}
                <a href={rorLink} target="_blank">
                  ROR
                </a>
                : {props.formData.ror}
              </b>
            )}
          </p>
          <Button
            className={classes.clearButton}
            variant="outlined"
            color="secondary"
            onClick={() => {
              const clearValue: SelectionValue = {
                name: undefined,
                ror: undefined,
              };
              // Clear the selection
              props.onChange(clearValue);
            }}
          >
            Clear Selection
          </Button>
          <br />
        </React.Fragment>
      ) : (
        // Otherwise include a mention here that the publisher needs to be selected
        <React.Fragment>
          <Stack
            style={{ width: "100%" }}
            direction="row"
            justifyContent="space-between"
            alignItems="center"
          >
            {manualOverride ? (
              <p>
                <b>
                  Manually enter the name and optionally the{" "}
                  <a href={rorLink} target="_blank">
                    ROR
                  </a>{" "}
                  of the desired organisation.
                  {props.required ? "*" : ""}
                </b>
              </p>
            ) : (
              <p>
                <b>
                  Use the search tool below to select a Research Organisation
                  Registry (
                  <a href={rorLink} target="_blank">
                    ROR
                  </a>
                  ) ID. {props.required ? "*" : ""}
                </b>
              </p>
            )}
            {manualOverride ? (
              <Button
                onClick={() => {
                  setManualOverride(false);
                }}
                variant="contained"
                color="success"
              >
                Return to search
              </Button>
            ) : (
              <Button
                onClick={() => {
                  setManualOverride(true);
                }}
                variant="contained"
                color="warning"
              >
                Manual Override
              </Button>
            )}
          </Stack>
        </React.Fragment>
      )}
      {!manualOverride ? (
        <Stack spacing={2}>
          {
            // Show the auto complete if manual override is disabled
          }
          <Typography variant="subtitle1">
            {props.schema.description}
          </Typography>
          <Autocomplete
            filterOptions={(optionsList: OptionsType[]) => {
              return optionsList;
            }}
            clearOnBlur={false}
            clearOnEscape={false}
            loading={isFetching}
            // List of options
            options={options}
            // What happens when you select an option
            onChange={(ele, value: OptionsType | null) => {
              console.log(ele, value ?? "");
              if (value) {
                submitChanges(value);
              }
            }}
            getOptionLabel={(option) => {
              return renderLabel(option);
            }}
            renderOption={(props, option) => {
              return (
                <Box component="li" {...props}>
                  {renderLabel(option)}
                </Box>
              );
            }}
            renderInput={(params) => (
              <TextField
                // This refers to the field as a UI element
                // not the data itself and is therefore not required
                // The underlying data fields are required though
                // and this does not overwrite it
                required={false}
                onChange={(e) => {
                  debouncedSetSearchInput(e.target.value);
                }}
                value={searchInput}
                {...params}
                label="Search for and select an organisation"
                FormHelperTextProps={{
                  className: classes.helperText,
                }}
              />
            )}
          />
        </Stack>
      ) : (
        // Show the manual form entry if manual input is requested
        <FormGroup>
          <Stack spacing={2}>
            {
              // Name
            }
            <Typography variant="subtitle1">
              {props.schema.description}
            </Typography>
            <TextField
              required={props.schema.properties.name.required ?? true}
              onChange={(e) => {
                var newValue: SelectionValue = JSON.parse(
                  JSON.stringify(props.formData),
                );
                newValue.name = e.target.value;
                props.onChange(newValue);
              }}
              value={props.formData.name ?? ""}
              helperText={
                props.schema.properties.name.description ??
                "Enter the name of the organisation"
              }
              label={props.schema.properties.name.title ?? "Organisation name"}
              FormHelperTextProps={{
                className: classes.helperText,
              }}
            />
            {
              // ROR
            }
            <TextField
              required={props.schema.properties.ror.required ?? false}
              onChange={(e) => {
                var newValue: SelectionValue = JSON.parse(
                  JSON.stringify(props.formData),
                );
                newValue.ror = e.target.value;
                props.onChange(newValue);
              }}
              value={props.formData.ror ?? ""}
              label={props.schema.properties.ror.title ?? "Organisation ROR"}
              helperText={
                props.schema.properties.ror.description ??
                "Enter the ROR of the organisation as a URL"
              }
              FormHelperTextProps={{
                className: classes.helperText,
              }}
            />
          </Stack>
        </FormGroup>
      )}
    </div>
  );
};
