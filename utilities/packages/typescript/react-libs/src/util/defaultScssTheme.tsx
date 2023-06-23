// Default Scss Theme config

import defaultScss from "../themes/default/style.module.scss";
import { createTheme } from "@mui/material";

export const defaultScssTheme = createTheme({
    palette: {
        primary: {
            main: defaultScss.palettePrimaryMainColor,
        },
        secondary: {
            main: defaultScss.paletteSecondaryMainColor,
        },
    },
    typography: {
        allVariants: { color: defaultScss.basicFontColor },
        fontFamily: defaultScss.globalFontFamily,
        fontSize: defaultScss.globalFontSize as unknown as number,
        h1: { color: defaultScss.palettePrimaryMainColor },
        h2: { color: defaultScss.palettePrimaryMainColor },
        h3: { color: defaultScss.palettePrimaryMainColor },
        h4: { color: defaultScss.palettePrimaryMainColor },
        h5: { color: defaultScss.palettePrimaryMainColor },
    },
    components: {
        // Unite the button-contained colors
        MuiButtonBase: {
            styleOverrides: {
                root: {
                    backgroundColor: "inherit",
                    "&.MuiButton-contained": {
                        color: "#FFFFFF",
                        background: defaultScss.palettePrimaryMainColor,
                    },
                },
            },
        },
        // Define the <a> text </a> link color
        MuiTypography: {
            styleOverrides: {
                root: {
                    "& a:not([class])": {
                        color: defaultScss.globalALinkColor,
                    },
                    // Default drawer color
                    "&.MuiListItemText-primary": {
                        color: "#FFFFFF",
                    },
                },
            },
        },
        // Disable default maxWidth
        MuiContainer: {
            defaultProps: {
                maxWidth: false,
                sx: {
                    width: "90%",
                },
            },
        },
    },
});
