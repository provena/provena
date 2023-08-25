import {
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    SelectChangeEvent,
} from "@mui/material";

type SortingOptions =
    | "Created Time (Oldest First)"
    | "Created Time (Newest First)";

// For getting true/false value from selected sorting options text name
const sortOptionsMap = new Map<SortingOptions, boolean>([
    ["Created Time (Oldest First)", true],
    ["Created Time (Newest First)", false],
]);

// For getting the sorting text option name from true/false value
const sortNamesMap = new Map<boolean, SortingOptions>([
    [true, "Created Time (Oldest First)"],
    [false, "Created Time (Newest First)"],
]);

interface VersioningSortingSelectorProps {
    ascending: boolean;
    setAscending: (ascending: boolean) => void;
    disabled?: boolean;
}

export const VersioningSortingSelector = (
    props: VersioningSortingSelectorProps
) => {
    /**
    Component: VersioningSortingSelector

    Versioning view sorting component
    */

    const initialSelection = sortNamesMap.get(props.ascending);

    const sortOptionKeys = Array.from(sortOptionsMap.keys());

    const handleSortingChange = (event: SelectChangeEvent) => {
        event.preventDefault();
        const currentSelection = event.target.value;
        const currentSortOption = sortOptionsMap.get(
            currentSelection as SortingOptions
        );
        if (currentSortOption !== undefined) {
            // Successful clicked
            props.setAscending(currentSortOption);
        }
    };

    const sortingSelector = (
        <FormControl fullWidth size="small">
            <InputLabel id="versioning-select-label">Sort by</InputLabel>
            <Select
                labelId="versioning-select-label"
                id="versioning-select"
                value={initialSelection ?? "Sort by"}
                label="Sort by"
                onChange={handleSortingChange}
                disabled={props.disabled}
            >
                {sortOptionKeys.map((item: string) => {
                    return <MenuItem value={item}>{item}</MenuItem>;
                })}
            </Select>
        </FormControl>
    );

    return sortingSelector;
};
