import { Alert, CircularProgress, Grid } from "@mui/material";
import {
    ColumnLayoutConfig,
    DetailLayoutOptions, JsonDetailViewWrapperComponent, LoadedEntity
} from "react-libs";
import { ItemBase } from "../shared-interfaces/RegistryModels";

interface ItemDisplayWithStatusComponentProps {
    // Always need to provide the id as a fallback for unloaded items
    id: string;

    // This should be used to control if the underlying load has started
    disabled: boolean;

    // Contains the status of the fetched item
    status: LoadedEntity<ItemBase>;

    // Layout config
    layout: DetailLayoutOptions;
    columnLayout?: ColumnLayoutConfig;
}
export const ItemDisplayWithStatusComponent = (
    props: ItemDisplayWithStatusComponentProps
) => {
    /**
    Component: ItemDisplayWithStatusComponent

    Displays an item which contains status as well. Uses the record detailed
    view with the specified layout passed through.
    */
    const item = props.status.data;
    const readyToDisplay = item !== undefined;

    return (
        <div style={{ width: "100%" }}>
            {!props.disabled &&
                (props.status.loading ? (
                    <Grid container justifyContent="center">
                        <Grid item>
                            <CircularProgress />
                        </Grid>
                    </Grid>
                ) : props.status.error ? (
                    <Alert variant="outlined" color="error" severity="error">
                        <b>An error occurred while loading: {props.id}.</b>
                        <br /> <br />
                        Error: {props.status.errorMessage ??
                            "Unknown error"}. <br />
                        <br />
                        Ensure you have access to view this item and try
                        refreshing the page.
                    </Alert>
                ) : (
                    readyToDisplay && (
                        <JsonDetailViewWrapperComponent
                            item={item!}
                            layout={props.layout}
                            layoutConfig={props.columnLayout}
                        />
                    )
                ))}
        </div>
    );
};
