import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { Grid, Theme, Typography } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import React, { useState } from "react";
import { hdlPrefix } from "../config";

interface CopyFloatingButtonProps {
  clipboardText: string;
  iconOnly?: boolean;
  withConfirmationText?: boolean;
}

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    copy: {
      float: "right",
      color: "white",
      fontSize: 12,
      margin: "-12px -12px 1px 1px",
      padding: "0 2px",
      backgroundColor: "gray",
      "&:hover": {
        cursor: "pointer",
      },
    },
    copyIcon: {
      //height: "12px",
      marginLeft: "12px",
      display: "inline-block",
      "&:hover": {
        cursor: "pointer",
      },
    },
    copiedCheck: {
      color: "green",
      marginRight: ".1em",
    },
    copiedText: {
      display: "inline-block",
      position: "relative",
      top: "-6px",
    },
  }),
);

export const CopyFloatingButton = (props: CopyFloatingButtonProps) => {
  // Setup theming
  const classes = useStyles();
  // Is the text copied?
  const [copied, setCopied] = useState<boolean>(false);
  // How long to wait before resetting copied logo
  const copiedTimeout = 1000; //ms

  return (
    <>
      {props.iconOnly ? (
        <div className={classes.copyIcon}>
          {copied ? (
            <Grid
              container
              direction="row"
              sx={{ display: "inline-block", width: "auto" }}
            >
              <CheckCircleIcon className={classes.copiedCheck} />
              {props.withConfirmationText ? (
                <Typography variant="body2" className={classes.copiedText}>
                  Copied!
                </Typography>
              ) : null}
            </Grid>
          ) : (
            <ContentCopyIcon
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                navigator.clipboard.writeText(props.clipboardText);
                if (!copied) {
                  setTimeout(() => {
                    setCopied(false);
                  }, copiedTimeout);
                  setCopied(true);
                }
              }}
            />
          )}
        </div>
      ) : (
        <div
          className={classes.copy}
          style={{
            backgroundColor: `${copied ? "green" : "gray"}`,
          }}
          onClick={() => {
            navigator.clipboard.writeText(props.clipboardText);
            if (!copied) {
              setTimeout(() => {
                setCopied(false);
              }, copiedTimeout);
              setCopied(true);
            }
          }}
        >
          {copied ? "Copied" : "Click to copy"}
        </div>
      )}
    </>
  );
};

export interface CopyableLinkedHandleComponentProps {
  handleId: string;
}
export const CopyableLinkedHandleComponent = (
  props: CopyableLinkedHandleComponentProps,
) => {
  /**
    Component: CopyableLinkedHandleComponent
    
    */
  const link = hdlPrefix + props.handleId;
  return (
    <React.Fragment>
      <a href={link} target="_blank" rel="noreferrer">
        {props.handleId}
      </a>
      <CopyFloatingButton
        clipboardText={props.handleId}
        iconOnly={true}
        withConfirmationText={true}
      />
    </React.Fragment>
  );
};

export interface CopyableLinkProps {
  link: string;
  content?: string;
}
export const CopyableLinkComponent = (props: CopyableLinkProps) => {
  /**
    Component: CopyableLinkComponent
    
    */
  const link = props.link;
  return (
    <React.Fragment>
      <a href={link} target="_blank" rel="noreferrer">
        {props.content ?? props.link}
      </a>
      <CopyFloatingButton
        clipboardText={props.link}
        iconOnly={true}
        withConfirmationText={true}
      />
    </React.Fragment>
  );
};

export interface CopyableTextProps {
  text: string;
  clipBoard: string;
}
export const CopyableTextComponent = (props: CopyableTextProps) => {
  /**
    Component: CopyableTextComponent
    
    * This component only do copy and put to clipboard, doen't have href link to the text
    */
  return (
    <React.Fragment>
      {props.text}
      <CopyFloatingButton
        clipboardText={props.clipBoard}
        iconOnly={true}
        withConfirmationText={true}
      />
    </React.Fragment>
  );
};
