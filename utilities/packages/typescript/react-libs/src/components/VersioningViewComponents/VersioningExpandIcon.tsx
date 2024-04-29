import MoreHorizRounded from "@mui/icons-material/MoreHorizRounded";
import { CircularProgress, Theme, Tooltip } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import React from "react";
import { VerticalTimelineElement } from "react-vertical-timeline-component";
import { Swatch } from "../../util";

interface StyleProps {
  subtypeSwatch?: Swatch;
}

const useStyles = (props: StyleProps) =>
  makeStyles((theme: Theme) =>
    createStyles({
      // For load other versions
      loadIcon: {
        "&:hover": {
          background: `${props.subtypeSwatch?.tintColour} !important`,
          cursor: "pointer",
        },
      },
      loadingIconDisable: {
        opacity: 0.38,
      },
    }),
  );

interface VersioningExpandControlProps {
  subtypeSwatch: Swatch;
  subtypeIcon: JSX.Element | null;
  expand: boolean;
  setExpand: (expand: boolean) => void;
  // If loading, disable expand click functionality
  loading: boolean;
}

export const VersioningExpandIcon = (props: VersioningExpandControlProps) => {
  /**
    Component: VersioningLoadMore

    Expand icon and control the collapse.
    */

  const classes = useStyles({ subtypeSwatch: props.subtypeSwatch })();

  const loadMoreIcon = (
    <Tooltip
      title="Click to expand more versions"
      placement="right"
      arrow={true}
    >
      <MoreHorizRounded fontSize="large" />
    </Tooltip>
  );

  // Handler
  const handleIconClick = () => {
    if (!props.loading) {
      props.setExpand(true);
    }
  };

  return (
    <React.Fragment>
      {!props.expand && (
        <VerticalTimelineElement
          contentStyle={{
            boxShadow: "0 0",
          }}
          contentArrowStyle={{ borderRight: "0px solid" }}
          iconStyle={{
            background: `${props.subtypeSwatch.colour}`,
            color: "#ffffff",
            top: "16px",
          }}
          iconOnClick={handleIconClick}
          iconClassName={
            props.loading ? classes.loadingIconDisable : classes.loadIcon
          }
          icon={loadMoreIcon}
        >
          {props.loading && <CircularProgress />}
        </VerticalTimelineElement>
      )}
    </React.Fragment>
  );
};
