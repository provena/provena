import { Swatches } from "../../util/subtypeStyling";
import { prepareObject } from "../../util/util";
import {
    ColumnLayoutConfig,
    DetailLayoutOptions,
    JsonDetailViewComponent,
    JsonTypes,
} from "./JsonDetailView";

interface GenericDetailViewWrapperComponentProps {
    item: { [k: string]: any };
    layout: DetailLayoutOptions;
    layoutConfig?: ColumnLayoutConfig;
}
export const GenericDetailViewWrapperComponent = (
    props: GenericDetailViewWrapperComponentProps
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
    const baseSwatch = Swatches.defaultSwatch;

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
            />
        </div>
    );
};
