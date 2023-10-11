import {
    Alert,
    CircularProgress,
    Divider,
    Grid,
    Stack,
    Typography,
} from "@mui/material";
import { LoadedEntity } from "../interfaces";
import { ItemBase } from "../shared-interfaces/RegistryModels";
import { getSwatchForSubtype, mapSubTypeToPrettyName } from "../util";
import {
    ColumnLayoutConfig,
    DetailLayoutOptions,
    JsonDetailViewWrapperComponent,
} from "./JsonRenderer";

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

    const baseSwatch = getSwatchForSubtype(item?.item_subtype);

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
                        <Stack direction="column">
                            {/* Entity's subtype and its version number, if has  */}
                            <Stack direction="row">
                                <Typography variant="h6">
                                    {mapSubTypeToPrettyName(item.item_subtype)}
                                </Typography>
                                {!!item.versioning_info && (
                                    <Typography variant="h6">
                                        <span>
                                            &nbsp;(V
                                            {item.versioning_info.version})
                                        </span>
                                    </Typography>
                                )}
                            </Stack>
                            <Divider
                                sx={{
                                    borderColor: `${baseSwatch.colour}`,
                                    borderStyle: "dotted",
                                }}
                            />
                            {/* Entity details */}
                            <Grid paddingTop={2}>
                                <JsonDetailViewWrapperComponent
                                    item={item!}
                                    layout={props.layout}
                                    layoutConfig={props.columnLayout}
                                />
                            </Grid>
                        </Stack>
                    )
                ))}
        </div>
    );
};
