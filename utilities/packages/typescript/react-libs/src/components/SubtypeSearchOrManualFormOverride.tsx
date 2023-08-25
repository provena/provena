import {
    Button,
    CircularProgress,
    IconButton,
    TextField,
    InputAdornment,
    Grid,
    Stack,
    Typography,
    Tooltip,
} from "@mui/material";
import React, { useState } from "react";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Theme } from "@mui/material/styles";
import { ItemBase, ItemSubType } from "../shared-interfaces/RegistryModels";
import LaunchIcon from "@mui/icons-material/Launch";
import { LoadedResult, useLoadedSearch } from "../hooks/useLoadedSearch";
import { generateRegistryDeepLink } from "../util/util";
import { mapSubTypeToPrettyName } from "../util/subtypeStyling";
import { hdlPrefix } from "../config";
import { DOCUMENTATION_BASE_URL, REGISTRY_LINK } from "../queries";
import Downshift from "downshift";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { FieldProps } from "@rjsf/utils";
import { deriveTitleDescription } from "../util/util";
import { useTypedLoadedItem } from "../hooks";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

// Styles for downshift menu are modified based on content from
// https://www.digitalocean.com/community/tutorials/how-to-use-downshift-in-common-dropdown-use-cases
const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        helperText: {
            marginLeft: 0,
        },
        clearButton: {
            "margin-bottom": theme.spacing(2),
            "margin-top": theme.spacing(2),
        },
        input: {
            margin: "1rem",
            width: "20rem",
            padding: "1rem .5rem",
        },
        // The overall search dropdown Div
        downshiftDropdown: {
            margin: "0 auto",
            width: "100%",
            border: "1px solid whitesmoke",
            borderBottom: "none",
        },
        // A child item of the dropdown
        dropdownItem: {
            padding: "0.5rem",
            cursor: "pointer",
            borderBottom: "1px solid whitesmoke",
            fontSize: "1rem",
            textAlign: "left",
            width: "100%",
        },
    })
);

// Definition of option in the list of options to pick from.
interface OptionsType {
    id: string;
    display_name: string;
    version?: number;
    error: boolean;
    errorMessage?: string;
    loading: boolean;
}

// Current selection/value
type IdSelectionValue = string | undefined;

interface SearchSelectorComponentProps {
    selection: IdSelectionValue;
    setSelection: (selection: IdSelectionValue) => void;
    subtype: ItemSubType;

    //styling
    helperText?: string;
}
export const SearchSelectorComponent = (
    props: SearchSelectorComponentProps
) => {
    /**
    Component: SearchSelectorComponent
    
    This is the downshift selector by itself for searching/selecting an item.
    */

    const classes = useStyles();

    // What is the user searching for?
    const [searchInput, setSearchInput] = useState<string>("");

    // use this to let the parent form know a selection was made
    const submitChanges = (selectedOption: OptionsType) => {
        // Process the selection and alert form if not loading/error
        if (!selectedOption.error && !selectedOption.loading) {
            if (!selectedOption.id) {
                console.log("Selected option had no id!");
            }
            let selectedValue = selectedOption.id;
            props.setSelection(selectedValue);
        }
    };

    // use the custom hook for a loaded search list
    const searchResults = useLoadedSearch({
        subtype: props.subtype,
        searchQuery: searchInput,
    });
    const { data: results, loading, error, errorMessage } = searchResults;

    // derive options from the results
    var options: OptionsType[] = [];

    // If there is an error, display a single item - this item can never be
    // submitted - just helps display the error
    if (error) {
        options = [
            {
                id: "error",
                display_name: "",
                version: undefined,
                error: error,
                errorMessage: errorMessage,
                loading: false,
            },
        ];
        // If results are not undefined then map into options type
    } else if (results !== undefined) {
        options = results.map((loadedResult: LoadedResult) => {
            return {
                // NOTE ID is always present even when item is not loaded
                id: loadedResult.id,
                display_name: loadedResult.item?.display_name ?? "",
                version: loadedResult.item?.versioning_info?.version,
                error: loadedResult.isError,
                errorMessage: loadedResult.errorMessage,
                loading: loadedResult.loading,
            };
        });
    }

    // Is there any item loading or total form loading? informs the loading spinner
    const anyLoading = loading || options.some((option) => option.loading);

    // How do we render labels in the dropdown?
    const renderLabel = (option: OptionsType) => {
        if (option.error) {
            return `(${option.id}) Error: ${
                option.errorMessage ?? "Unknown error occurred."
            }`;
        }
        if (option.loading) {
            return `Details loading...(${option.id})`;
        }
        // else, render properly as got some results.

        // Check if item has version
        const versionNum =
            option.version !== undefined ? ` (V${option.version})` : "";
            
        return `${option.display_name}${versionNum} - ${option.id}`;
    };

    // Pretty name for subtype
    const subtypeName = mapSubTypeToPrettyName(props.subtype);

    return (
        <Downshift
            // The search input
            inputValue={searchInput}
            // When the value changes - i.e. update state
            onInputValueChange={(value: string) => {
                setSearchInput(value);
            }}
            // If the selected value changes
            onChange={(selection: OptionsType | null) => {
                if (selection) {
                    submitChanges(selection);
                }
            }}
            // Render function for items
            itemToString={(item: OptionsType | null) => {
                return item ? renderLabel(item) : "";
            }}
        >
            {({
                getInputProps,
                getItemProps,
                getToggleButtonProps,
                isOpen,
                highlightedIndex,
                selectedItem,
            }) => {
                // Returns a render which uses the above stateful
                // variables and prop generators
                return (
                    <div>
                        {
                            // MUI text field responsible for
                            // rendering/accepting search input
                        }
                        <TextField
                            fullWidth
                            // Shows the expand collapse and loading
                            // icon
                            InputProps={{
                                endAdornment: (
                                    <InputAdornment position="end">
                                        {anyLoading && (
                                            <IconButton>
                                                <CircularProgress />
                                            </IconButton>
                                        )}
                                        <IconButton {...getToggleButtonProps()}>
                                            {isOpen ? (
                                                <ExpandLessIcon fontSize="large" />
                                            ) : (
                                                <ExpandMoreIcon fontSize="large" />
                                            )}
                                        </IconButton>
                                    </InputAdornment>
                                ),
                                ...getInputProps(),
                            }}
                            label={`Search for a ${subtypeName} using name or ID`}
                            helperText={props.helperText}
                            FormHelperTextProps={{
                                className: classes.helperText,
                            }}
                        />
                        {
                            // conditionally show drop down elements
                            // (search results) - these are
                            // selectable due to the generated props
                            // from downshift
                        }
                        {isOpen && (
                            <div className={classes.downshiftDropdown}>
                                {options.length > 0
                                    ? options.map((option, index) => {
                                          return (
                                              <div
                                                  className={
                                                      classes.dropdownItem
                                                  }
                                                  style={{
                                                      backgroundColor:
                                                          highlightedIndex ===
                                                          index
                                                              ? "lightgray"
                                                              : "white",
                                                      fontWeight:
                                                          selectedItem?.id ===
                                                          option.id
                                                              ? "bold"
                                                              : "normal",
                                                  }}
                                                  key={option.id}
                                                  {...getItemProps({
                                                      item: option,
                                                      index: index,
                                                  })}
                                              >
                                                  {renderLabel(option)}
                                              </div>
                                          );
                                      })
                                    : // Show the no results if we are
                                      // not loading yet the entries
                                      // list is empty
                                      !loading && (
                                          <div className={classes.dropdownItem}>
                                              No results
                                          </div>
                                      )}
                            </div>
                        )}
                    </div>
                );
            }}
        </Downshift>
    );
};

const fallthroughDescription = "Use the search tool above to select an ID";
const fallthroughTitle = "Select an item from the registry";

const registryHelpLink =
    DOCUMENTATION_BASE_URL + "/information-system/provenance/registry/";

export interface SubtypeSearchAutoCompleteProps
    extends FieldProps<IdSelectionValue> {
    // What subtype?
    subtype: ItemSubType;
    // Should the title persist after selection?
    persistTitle?: boolean;
}

export const SubtypeSearchAutoComplete = (
    props: SubtypeSearchAutoCompleteProps
) => {
    const classes = useStyles();

    // Is the input confirmed?
    const selectionMade: boolean = !!props.formData && props.formData !== "";

    // Description from schema with default fall through
    const { title, description } = deriveTitleDescription<IdSelectionValue>({
        fallthroughDescription,
        fallthroughTitle,
        ...props,
    });

    // Has the user entered a manual term?
    const [manualInput, setManualInput] = useState<string>("");

    // Pretty name for subtype
    const subtypeName = mapSubTypeToPrettyName(props.subtype);
    const exploreDeepLink = generateRegistryDeepLink(props.subtype);

    // This is the header content which is always present whether search is
    // used or not
    const headerContent = (
        <Grid container justifyContent="space-between" alignItems="center">
            <Grid item xs={7}>
                <Stack spacing={1}>
                    <Typography variant="h6">{title}</Typography>
                    <Typography variant="subtitle1">{description}</Typography>
                </Stack>
            </Grid>
            <Grid item>
                <Button
                    onClick={() => {
                        // Clear the selection
                        window.open(
                            exploreDeepLink,
                            "_blank",
                            "noopener,noreferrer"
                        );
                    }}
                    variant="outlined"
                >
                    Explore {subtypeName}s in the Registry
                    <LaunchIcon style={{ marginLeft: "10px" }} />
                </Button>
            </Grid>
        </Grid>
    );

    // This is the loaded data for selected item - whether through search or
    // manually

    // If the value is selected, show the following content
    // Make sure we have loaded the item based on ID
    const loadedItem = useTypedLoadedItem({
        id: props.formData,
        subtype: props.subtype,
    });

    const typedItem =
        loadedItem.data?.item !== undefined
            ? (loadedItem.data?.item as ItemBase)
            : undefined;

    // parse the display name contents
    const itemDisplayNameContents = loadedItem.loading
        ? "Loading item..."
        : loadedItem.error
        ? `An error occurred while loading the ${subtypeName}. Error: ${
              loadedItem.errorMessage ?? "Unknown error..."
          }.`
        : typedItem?.display_name ?? "Unknown name...";

    const itemLoadedSuccessfully =
        !loadedItem.error && loadedItem.data !== undefined;

    // The following is shown when the user has made a selection - either
    // through search or manually - contains error fallback for the loaded
    // item
    const selectionContent = (
        <Stack>
            <p>
                Selected {subtypeName}: {itemDisplayNameContents} (
                <a
                    href={hdlPrefix + props.formData}
                    target="_blank"
                    rel="noreferrer"
                >
                    <b>{props.formData}</b>
                </a>
                ){" "}
                {itemLoadedSuccessfully && (
                    <Tooltip
                        title={"Successfully fetched item from the Registry"}
                    >
                        <CheckCircleIcon style={{ color: "green" }} />
                    </Tooltip>
                )}
                {loadedItem.error && (
                    <p>
                        {" "}
                        Please ensure that selected ID is a valid, registered{" "}
                        {subtypeName}. You can learn more about the registry{" "}
                        <a
                            href={registryHelpLink}
                            target="_blank"
                            rel="noreferrer"
                        >
                            here
                        </a>
                        .
                    </p>
                )}
            </p>
            <Stack direction="row" spacing={2} alignItems="center" padding={0}>
                <Button
                    className={classes.clearButton}
                    variant="outlined"
                    color="secondary"
                    onClick={() => {
                        // Clear the selection
                        window.open(
                            REGISTRY_LINK + "/item/" + props.formData,
                            "_blank",
                            "noopener,noreferrer"
                        );
                    }}
                >
                    view in registry{" "}
                    <LaunchIcon style={{ marginLeft: "10px" }} />
                </Button>
                <Button
                    className={classes.clearButton}
                    variant="outlined"
                    color="warning"
                    onClick={() => {
                        // Clear the selection
                        props.onChange(undefined);
                    }}
                >
                    Clear Selection
                </Button>
            </Stack>
        </Stack>
    );

    const searchSelectContent = (
        // Otherwise include a mention here that the publisher needs to be selected
        <React.Fragment>
            <Grid
                container
                justifyContent="space-evenly"
                alignItems="flex-start"
                spacing={2}
            >
                <Grid item flexGrow={1.5}>
                    {
                        // Search
                        // Uses downshift - see https://www.downshift-js.com/
                    }
                    <SearchSelectorComponent
                        selection={props.formData}
                        subtype={props.subtype}
                        setSelection={props.onChange}
                    />
                </Grid>
                <Grid item>
                    <p>Or</p>
                </Grid>
                <Grid item flexGrow={1}>
                    {
                        // Select manually
                    }
                    <Stack direction="row" spacing={2} alignItems="center">
                        <TextField
                            fullWidth
                            onChange={(e) => {
                                setManualInput(e.target.value);
                            }}
                            value={manualInput}
                            // Catch the enter key to quickly submit manual
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    // avoid firing to parent
                                    e.preventDefault();
                                    // Submit contents
                                    props.onChange(manualInput);
                                }
                            }}
                            label={`Manually enter the ID of a ${subtypeName}`}
                        />
                        <Button
                            variant={"contained"}
                            onClick={(e) => {
                                props.onChange(manualInput);
                            }}
                        >
                            Submit
                        </Button>
                    </Stack>
                </Grid>
            </Grid>
        </React.Fragment>
    );

    return (
        <Stack spacing={1.5}>
            {headerContent}
            {selectionMade ? selectionContent : searchSelectContent}
        </Stack>
    );
};
