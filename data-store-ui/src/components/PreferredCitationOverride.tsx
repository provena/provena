import { FieldProps } from "@rjsf/utils";
import {
  OptionalStringFieldOverrideComponent,
  OptionalStringDataType,
} from "react-libs";

export const PreferredCitationOverride = (
  props: FieldProps<OptionalStringDataType>,
) => {
  return (
    <OptionalStringFieldOverrideComponent
      tickboxMessage="Provide preferred citation?"
      inputPlaceholderText="Enter your preferred citation"
      {...props}
    />
  );
};
