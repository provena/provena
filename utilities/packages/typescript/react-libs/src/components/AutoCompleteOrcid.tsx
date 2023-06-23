import { Button, TextField, Autocomplete } from "@mui/material";
import { makeStyles, createStyles } from "@mui/styles";
import { Theme } from "@mui/material";
import React, { useEffect, useState } from "react";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        helperText: {
            marginLeft: 0,
        },
        clearButton: {
            "margin-bottom": theme.spacing(2),
            "margin-top": theme.spacing(2),
        },
    })
);

//RawOrcidResponse but with underscores instead of "-"
interface OrcidItem {
    orcid_id: string;
    given_names: string;
    family_names: string;
    other_name: string[];
    email: string[];
    institution_name: string[];
}

interface RawOrcidItemResponse {
    "orcid-id": string;
    "given-names": string;
    "family-names": string;
    "other-name": string[];
    email: string[];
    "institution-name": string[];
}

// Definition of option in the list of options to pick from.
interface OptionsType {
    orcid_id: string;
    given_names?: string;
    family_names?: string;
    email?: string;
    institution_name?: string;

    error: boolean;
}

// Cuurent selection/value. (value is whaat is currently typede?)
type SelectionValue = string | undefined;

interface AutoCompleteOrcidPropType {
    formData: SelectionValue;
    // cant change formData values,
    // onChange() to change formData if need

    onChange: (data: SelectionValue) => void;

    // title and description for field.
    schema: {
        title: string;
        description: string;
    };

    // ui schema in case overrided
    uiSchema: {
        "ui:description"?: string;
    };

    required: boolean;
}

export const AutoCompleteOrcid = (props: AutoCompleteOrcidPropType) => {
    const classes = useStyles();

    // is loading?
    const [loading, setLoading] = useState<boolean>(true);

    // pick up input from the properties, if provided
    const [searchInput, setSearchInput] = useState<string>("");

    // Set the options as loading to begin with
    // This holds the list of options shown in the auto complete list
    const [options, setOptions] = useState<OptionsType[]>([]);

    // use this to let the form know a slection was made

    const submitChanges = (selectedOption: OptionsType) => {
        if (!selectedOption.error) {
            if (!selectedOption.orcid_id) {
                console.log("Selected option had no id!");
            }

            let selectedValue = "https://orcid.org/" + selectedOption.orcid_id;

            props.onChange(selectedValue);
        }
    };

    useEffect(() => {
        // if typing something
        if (searchInput.length >= 1) {
            let encodedSearchInput = encodeURIComponent(searchInput);
            setLoading(true);
            fetch(
                `https://pub.orcid.org/v3.0/expanded-search/?q=${encodedSearchInput}&start=0&rows=10`,

                {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            )
                .then((res) => res.json())
                .then((json) => {
                    //OrcidItemResponse[]

                    // get Orcids in OrcidItem format as opposed to rawformat with uses dashes (-).
                    let orcidResponseList = json["expanded-result"].map(
                        (json_item: { [k: string]: any }) => {
                            const raw_orcid = json_item as RawOrcidItemResponse;
                            const orcid_item: OrcidItem = {
                                orcid_id: raw_orcid["orcid-id"],
                                given_names: raw_orcid["given-names"],
                                family_names: raw_orcid["family-names"],
                                other_name: raw_orcid["other-name"],
                                email: raw_orcid["email"],
                                institution_name: raw_orcid["institution-name"],
                            };
                            return orcid_item;
                        }
                    ) as OrcidItem[];
                    const optionsList: OptionsType[] = orcidResponseList.map(
                        (orcidItem: OrcidItem) => {
                            // returning an OptionType
                            const optionItem: OptionsType = {
                                orcid_id: orcidItem.orcid_id, // will include as need it but dont render in the end.
                                given_names: orcidItem.given_names,
                                family_names: orcidItem.family_names,

                                institution_name: orcidItem.institution_name
                                    ? orcidItem.institution_name
                                          .slice(0, 4)
                                          .join(", ")
                                    : "",

                                error: false,
                            };
                            return optionItem;
                        }
                    );

                    setOptions(optionsList);
                })
                .catch((e) => {
                    setOptions([
                        {
                            orcid_id: "Experienced an error while loading ...",
                            error: true,
                        },
                    ]);
                })
                .finally(() => {
                    setLoading(false);
                });
        }
    }, [searchInput]);

    const renderLabel = (option: OptionsType) => {
        // Error label

        try {
            if (option.error) {
                return option.orcid_id;
            }

            // else, render properly as got some results.
            return `${option.family_names}, ${option.given_names} ${
                option.institution_name != ""
                    ? "- " + option.institution_name
                    : ""
            } - ${option.orcid_id}`;
        } catch {
            console.log("Render error");
            return "Error in rendering";
        }
    };

    return (
        <div className="">
            {
                // If there is existing formData include here
            }
            {props.formData && props.formData != "" ? (
                <React.Fragment>
                    <p>
                        <b>Selected Orcid : </b>
                        <a href={props.formData} target="_blank">
                            {props.formData}
                        </a>
                        <br />
                        <Button
                            className={classes.clearButton}
                            variant="outlined"
                            color="secondary"
                            onClick={() => {
                                // Clear the selection
                                props.onChange(undefined);
                            }}
                        >
                            Clear Selection
                        </Button>
                    </p>
                </React.Fragment>
            ) : (
                // Otherwise include a mention here that the publisher needs to be selected
                <React.Fragment>
                    <p>
                        <b>
                            Use the search tool below to select an{" "}
                            <a href="https://orcid.org" target="_blank">
                                ORCID
                            </a>
                            . {props.required && "*"}
                        </b>
                    </p>
                </React.Fragment>
            )}
            <Autocomplete
                filterOptions={(optionsList: OptionsType[]) => {
                    return optionsList;
                }}
                clearOnBlur={false}
                clearOnEscape={false}
                loading={loading}
                // freeSolo={true}
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
                        <li {...props} key={option.orcid_id}>
                            {renderLabel(option)}
                        </li>
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
                            setSearchInput(e.target.value);
                        }}
                        value={searchInput}
                        {...params}
                        label="Search for an orcid using names, institutions or your orcid ID in format XXXX-XXXX-XXXX-XXXX"
                        helperText={
                            props.uiSchema["ui:description"] ||
                            props.schema.description
                        }
                        FormHelperTextProps={{
                            className: classes.helperText,
                        }}
                    />
                )}
            />
        </div>
    );
};
