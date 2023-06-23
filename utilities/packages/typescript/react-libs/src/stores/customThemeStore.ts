import { DefaultTheme } from "@mui/styles";
import {
    CurrentPage,
    PageThemeConfig,
    getCurrentThemeConfig,
    getCurrentScssTheme,
} from "../util/themeValidation";

export interface CustomThemeProps {
    currentPage: CurrentPage;
}
export class CustomThemeStore {
    // distinguish between different ui pages
    private currentPage: CurrentPage;

    private _currentTheme: DefaultTheme;
    private _currentThemeConfig: PageThemeConfig;

    // constructor(customJsonPath: string, customScssPath: string, customMode: boolean, currentPage: CurrentPage) {
    constructor(props: CustomThemeProps) {
        this.currentPage = props.currentPage;

        this._currentThemeConfig = getCurrentThemeConfig(
            this.currentPage
        );
        this._currentTheme = getCurrentScssTheme(
            this._currentThemeConfig.backgroundImageURL
        );
    }

    get currentTheme() {
        return this._currentTheme;
    }

    get currentThemeConfig() {
        return this._currentThemeConfig;
    }
}

export default CustomThemeStore;
