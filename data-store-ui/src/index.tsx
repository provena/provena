import ReactDOM from "react-dom";
import { BrowserRouter } from "react-router-dom";
import {
    ThemeProvider,
    Theme,
    StyledEngineProvider,
    Typography,
} from "@mui/material";
import App from "./App";
import { createContext } from "react";
import CustomThemeStore from "react-libs/stores/customThemeStore";
import { PageThemeConfig } from "react-libs/util/themeValidation";
import { Warmer } from "react-libs";

// Initiate warmer
console.log("Initiating lambda warmer.");
const warmer = new Warmer();

declare module "@mui/styles" {
    interface DefaultTheme extends Theme {
        backgroundImgURL?: string;
    }
}

// false for using default scss theme, titles and backgrounds, true for using customized ones.
const themeStore = new CustomThemeStore({
    currentPage: "dataStore",
});

// for exporting other custom theme config only
export const themeStoreConfig = themeStore.currentThemeConfig;

// Set page title
document.title = themeStoreConfig.currentPageThemeConfig.pageTitle;
// Set page favicon
const faviconElement = document.querySelector(
    "link[rel=icon]"
) as HTMLLinkElement;
faviconElement.href = themeStoreConfig.faviconURL;
// Set apple touch favicon
const appleTouchFaviconElement = document.querySelector(
    "link[rel=apple-touch-icon]"
) as HTMLLinkElement;
appleTouchFaviconElement.href = themeStoreConfig.appleTouchIconURL;

// Setup a theme config provider
export const ThemeConfigContext =
    createContext<PageThemeConfig>(themeStoreConfig);

ReactDOM.render(
    <BrowserRouter>
        <ThemeConfigContext.Provider value={themeStoreConfig}>
            <StyledEngineProvider injectFirst>
                <ThemeProvider theme={themeStore.currentTheme}>
                    <Typography>
                        <App />
                    </Typography>
                </ThemeProvider>
            </StyledEngineProvider>
        </ThemeConfigContext.Provider>
    </BrowserRouter>,
    document.getElementById("root")
);
