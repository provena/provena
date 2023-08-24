import { Theme } from "@mui/material";

// Override typing of default style
declare module "@mui/styles" {
    interface DefaultTheme extends Theme {
        backgroundImgURL?: string;
    }
}

export * from "./components";
export * from "./hooks";
export * from "./interfaces";
export * from "./queries";
export * from "./stores";
export * from "./util";
export * from "./layout";
export * from "./tasks";
export * from "./config";
export * from "./routes";