import { Breakpoint, Theme } from "@mui/material";
import { makeStyles, createStyles } from "@mui/styles";

/*
This Component is to set a maxWidth for the inside children node, and center it to the page.
*/

const useStyles = (breakpointKey: Breakpoint) =>
  makeStyles((theme: Theme) => ({
    boundedWidth: {
      width: "100%",
      maxWidth: theme.breakpoints.values[breakpointKey],
      margin: "0 auto",
    },
  }));

interface BoundedContainerProps {
  breakpointKey: Breakpoint;
}

export const BoundedContainer = (
  props: React.PropsWithChildren<BoundedContainerProps>,
) => {
  // The maxWidth value depends on the input props breakpointKey: "xs" | "sm" | "md" | "lg" | "xl",
  // so that we can control the maxWidth for different needs.
  const classes = useStyles(props.breakpointKey)();

  return <div className={classes.boundedWidth}>{props.children}</div>;
};
