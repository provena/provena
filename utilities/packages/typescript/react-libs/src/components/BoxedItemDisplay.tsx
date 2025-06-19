import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import {
  JsonDetailViewWrapperComponent,
  JsonDetailViewWrapperComponentProps,
} from "./JsonRenderer";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    displayBox: {
      padding: theme.spacing(3),
      maxHeight: "30vh",
      overflowY: "auto",
      border: `1px solid ${theme.palette.divider}`,
      borderRadius: theme.shape.borderRadius,
      backgroundColor: theme.palette.background.paper,
      boxShadow: theme.shadows[1],
    },
  })
);

type BoxedItemDisplayComponentProps = JsonDetailViewWrapperComponentProps;
export const BoxedItemDisplayComponent = (
  props: BoxedItemDisplayComponentProps
) => {
  /**
    Component: BoxedItemDisplayComponent

    Stylish scrollable box with detailed renderer
    */
  const classes = useStyles();
  return (
    <div className={classes.displayBox}>
      <JsonDetailViewWrapperComponent
        item={props.item}
        layout={props.layout}
        layoutConfig={props.layoutConfig}
      ></JsonDetailViewWrapperComponent>
    </div>
  );
};
