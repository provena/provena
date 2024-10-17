import { ItemBase } from "../../provena-interfaces/RegistryModels";
import { getSwatchForSubtype } from "../../util/subtypeStyling";
import { prepareObject } from "../../util/util";
import {
  ColumnLayoutConfig,
  DetailLayoutOptions,
  JsonDetailViewComponent,
  JsonTypes,
} from "./JsonDetailView";

export interface JsonDetailViewWrapperComponentProps {
  item: ItemBase;
  layout: DetailLayoutOptions;
  layoutConfig?: ColumnLayoutConfig;
}
export const JsonDetailViewWrapperComponent = (
  props: JsonDetailViewWrapperComponentProps
) => {
  /**
    Component: JsonDetailViewWrapperComponent

    Wraps the JsonDetailViewComponent.

    Used to apply reordering and filtering of entity properties before more
    generic display.

    Also applies the color based on item subtype.

    Uses the undefined name to specify that we are rendering a top level JSON
    object.
    */
  const processed = prepareObject(props.item);
  const baseSwatch = getSwatchForSubtype(props.item?.item_subtype);

  return (
    <div style={{ width: "100%" }}>
      <JsonDetailViewComponent
        json={{
          // No name to start with
          name: undefined,
          // Cast the item to a JSON object base
          value: processed as unknown as { [k: string]: JsonTypes },
        }}
        style={{
          color: baseSwatch.colour,
          layout: props.layout,
          layoutConfig: props.layoutConfig,
        }}
        // Include the subtype as base context! This allows for
        // differentiation of subtypes in the paths override
        context={{ fields: [props.item.item_subtype] }}
        key={props.item.id + "display"}
      />
    </div>
  );
};
