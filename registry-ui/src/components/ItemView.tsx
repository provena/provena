import { CircularProgress, Grid, Stack } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import {
  JsonDetailViewWrapperComponent,
  SubtypeHeaderComponent,
} from "react-libs";
import { lockedResourceContent } from "../pages/Item";
import { ItemBase } from "../provena-interfaces/RegistryModels";
import unset from "lodash.unset";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    loadingIndicatorContainer: {
      display: "flex",
      flexDirection: "row",
      justifyContent: "center",
      alignItems: "start",
      padding: theme.spacing(5),
    },
  }),
);

interface ItemViewProps {
  locked: boolean;
  isUser: boolean;
  item: ItemBase | undefined;
}
const ItemView = (props: ItemViewProps) => {
  const classes = useStyles();

  // Catch for avoiding id resolution on Person type
  if (props.item !== undefined && props.item.item_subtype === "PERSON") {
    // This avoids the owner username being linked/resolved
    unset(props.item, "owner_username");
  }

  return props.item ? (
    <Stack direction="column" spacing={1}>
      <SubtypeHeaderComponent
        item={props.item}
        isUser={props.isUser}
        locked={props.locked}
        lockedContent={lockedResourceContent}
      />

      <JsonDetailViewWrapperComponent item={props.item} layout={"column"} />
    </Stack>
  ) : (
    <Grid container item xs={12} className={classes.loadingIndicatorContainer}>
      <CircularProgress />
    </Grid>
  );
};

export default ItemView;
