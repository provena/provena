import { Stack, Typography } from "@mui/material";
import { FieldProps } from "@rjsf/utils";
import { useTypedLoadedItem } from "../hooks";
import { ItemBase, ItemSubType } from "../provena-interfaces/RegistryModels";
import { mapSubTypeToPrettyName } from "../util/subtypeStyling";
import { deriveTitleDescription } from "../util/util";
import { BoxedItemDisplayComponent } from "./BoxedItemDisplay";
import { IdSelectionValue } from "./SubtypeSearchOrManualFormOverride";

/**
 * Filters the keys of an object based on a predicate function.
 *
 * @template T The type of the input object
 * @template K The type of the keys in the object (must be a subset of keyof T)
 *
 * @param {T} obj - The input object to filter
 * @param {(key: K) => boolean} predicate - A function that takes a key and returns true if the key should be included in the result
 *
 * @returns {Pick<T, K>} A new object containing only the key-value pairs where the key satisfies the predicate
 *
 * @example
 * const input = { a: 1, b: 2, c: 3, d: 4 };
 * const result = filterObjectKeys(input, key => ['a', 'c'].includes(key));
 * // result is { a: 1, c: 3 }
 *
 * @throws {TypeError} If the input is not an object or the predicate is not a function
 */
function filterObjectKeys<T extends object, K extends keyof T>(
  obj: T,
  predicate: (key: K) => boolean
): Pick<T, K> {
  return Object.fromEntries(
    Object.entries(obj).filter(([key]) => predicate(key as K))
  ) as Pick<T, K>;
}

// Current selection/value
export interface FixedFormDisplayProps extends FieldProps<IdSelectionValue> {
  // What subtype?
  subtype: ItemSubType;
  // Field selection (in addition to id, item_subtype which are required)
  fieldDisplayFilter: string[];
}

const fallthroughDescription = "View details about your selected item below";
const fallthroughTitle = "Selected item";

export const FixedFormDisplay = (props: FixedFormDisplayProps) => {
  // Is the input confirmed?
  const selectionMade: boolean = !!props.formData && props.formData !== "";

  // Description from schema with default fall through
  const { title, description } = deriveTitleDescription<IdSelectionValue>({
    fallthroughDescription,
    fallthroughTitle,
    ...props,
  });

  // Pretty name for subtype
  const subtypeName = mapSubTypeToPrettyName(props.subtype);

  // This is the header content which is always present whether search is
  // used or not
  const headerContent = (
    <>
      <Typography variant="h6">{title}</Typography>
      <Typography variant="subtitle1">{description}</Typography>
    </>
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

  const totalFilterList = ["id", "item_subtype"].concat(
    props.fieldDisplayFilter
  );
  const filteredItem =
    typedItem &&
    filterObjectKeys(typedItem, (key) => totalFilterList.includes(key));

  const displayContent = !!filteredItem ? (
    <BoxedItemDisplayComponent item={filteredItem} layout="column" />
  ) : null;

  return (
    <Stack spacing={1.5}>
      {headerContent}
      {selectionMade && displayContent}
    </Stack>
  );
};

type FormProps = FieldProps<IdSelectionValue>;

export const DatasetTemplateDisplay = (props: FormProps) => {
  return (
    <FixedFormDisplay
      {...props}
      subtype={"DATASET_TEMPLATE"}
      fieldDisplayFilter={[
        "description",
        "display_name",
        "deferred_resources",
        "defined_resources",
      ]}
    />
  );
};
