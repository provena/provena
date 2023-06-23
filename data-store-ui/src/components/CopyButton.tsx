import { Button } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useState } from "react";

interface CopyButtonProps {
    clipboardText: string;
    readyToCopyText: string;
    copiedText: string;
    buttonWidth?: string;
}

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        copy: {
            fontSize: 12,
            "&:hover": {
                cursor: "pointer",
            },
        },
    })
);

export const CopyButton = (props: CopyButtonProps) => {
    /**
     * A simple copy button - returns a basic styled button which
     * when pressed changes color and shows a special message. It
     * copies the specified content to the clipboard.
     */

    // Setup theming
    const classes = useStyles();
    // Is the text copied?
    const [copied, setCopied] = useState<boolean>(false);
    // How long to wait before resetting copied logo
    const copiedTimeout = 1000; //ms

    return (
        <Button
            style={{ width: props.buttonWidth }}
            className={classes.copy}
            variant="contained"
            color={`${copied ? "success" : "primary"}`}
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
            {copied ? props.copiedText : props.readyToCopyText}
        </Button>
    );
};
