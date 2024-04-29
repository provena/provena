import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import { filterableEntityTypes, registerableEntityTypes } from "../entityLists";
import { ItemSubType } from "../provena-interfaces/RegistryModels";
import { mapSubTypeToPrettyName } from "react-libs";

type SubtypeListType = "REGISTERABLE" | "FILTERABLE";

interface ItemSubtypeSelectorProps {
  selectedItemSubType: ItemSubType;
  onChange: (subtype: ItemSubType) => void;
  listType: SubtypeListType;
  disabled?: boolean;
  subtitle?: string;
}
export const ItemSubtypeSelector = (props: ItemSubtypeSelectorProps) => {
  /**
    Component: ItemSubtypeSelector
    */

  const typeList: ItemSubType[] =
    props.listType === "FILTERABLE"
      ? filterableEntityTypes
      : registerableEntityTypes;

  return (
    <FormControl fullWidth>
      <InputLabel>{props.subtitle}</InputLabel>
      <Select
        notched={true}
        id="filter-dropdown"
        labelId="filter-label"
        label={props.subtitle}
        renderValue={(selected: ItemSubType) => {
          return mapSubTypeToPrettyName(selected);
        }}
        defaultValue={registerableEntityTypes[0]}
        value={props.selectedItemSubType}
        onChange={(event: SelectChangeEvent<any>) => {
          let selectedSubType = event.target.value as ItemSubType;

          props.onChange(selectedSubType);
        }}
        fullWidth={true}
        multiple={false}
        displayEmpty={true}
        disabled={props.disabled ?? false}
      >
        {typeList.map((e) => {
          return (
            <MenuItem key={e} value={e}>
              {mapSubTypeToPrettyName(e)}
            </MenuItem>
          );
        })}
      </Select>
    </FormControl>
  );
};
