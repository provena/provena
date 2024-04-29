import { MenuItem, Select } from "@mui/material";
import { SortOptions, SortType } from "../provena-interfaces/RegistryAPI";

const displayNameMap: Map<string, SortOptions> = new Map([
  [
    "Created Time (Oldest First)",
    { sort_type: "CREATED_TIME", ascending: true },
  ],
  [
    "Created Time (Newest First)",
    { sort_type: "CREATED_TIME", ascending: false },
  ],
  [
    "Updated Time (Oldest First)",
    { sort_type: "UPDATED_TIME", ascending: true },
  ],
  [
    "Updated Time (Newest First)",
    { sort_type: "UPDATED_TIME", ascending: false },
  ],
  ["Display Name (A-Z)", { sort_type: "DISPLAY_NAME", ascending: true }],
  ["Display Name (Z-A)", { sort_type: "DISPLAY_NAME", ascending: false }],
]);

const sortOptionsMap: Map<string, string> = new Map([
  [
    JSON.stringify({ sort_type: "CREATED_TIME", ascending: true }),
    "Created Time (Oldest First)",
  ],
  [
    JSON.stringify({ sort_type: "CREATED_TIME", ascending: false }),
    "Created Time (Newest First)",
  ],
  [
    JSON.stringify({ sort_type: "UPDATED_TIME", ascending: true }),
    "Updated Time (Oldest First)",
  ],
  [
    JSON.stringify({ sort_type: "UPDATED_TIME", ascending: false }),
    "Updated Time (Newest First)",
  ],
  [
    JSON.stringify({ sort_type: "DISPLAY_NAME", ascending: true }),
    "Display Name (A-Z)",
  ],
  [
    JSON.stringify({ sort_type: "DISPLAY_NAME", ascending: false }),
    "Display Name (Z-A)",
  ],
]);

interface SortOptionsSelectorProps {
  selectedType: SortType;
  setSelectedType: (type: SortType) => void;
  ascending: boolean;
  setAscending: (ascending: boolean) => void;
  disabled?: boolean;
}
export const SortOptionsSelector = (props: SortOptionsSelectorProps) => {
  /**
    Component: SortOptionsSelector

    Combines the sort type ascending/descending into a single combined selector
    which has customised display names for each combination
    */

  const sortTypeAscendingToDisplayName = (sortOptions: SortOptions): string => {
    return (
      sortOptionsMap.get(JSON.stringify(sortOptions)) ??
      "Unknown options. Contact Admin"
    );
  };

  const displayNameToSortOptions = (
    displayName: string,
  ): SortOptions | undefined => {
    return displayNameMap.get(displayName);
  };

  const selectOptions: string[] = Array.from(displayNameMap.keys());

  return (
    <Select
      notched={true}
      id="sort-dropdown"
      labelId="sort-label"
      label="Sort by"
      disabled={!!props.disabled}
      value={sortTypeAscendingToDisplayName({
        sort_type: props.selectedType,
        ascending: props.ascending,
      })}
      fullWidth={true}
      onChange={(event) => {
        const selectedSortOptions = displayNameToSortOptions(
          event.target.value,
        );
        if (selectedSortOptions === undefined) {
          console.log(
            "User clicked on unexpected displayname in sort type selector: " +
              event.target.value,
          );
        } else {
          props.setSelectedType(selectedSortOptions.sort_type!);
          props.setAscending(selectedSortOptions.ascending!);
        }
      }}
    >
      {selectOptions.map((displayName: string) => {
        return <MenuItem value={displayName}>{displayName}</MenuItem>;
      })}
    </Select>
  );
};
