import { PaletteColorOptions, Theme, createTheme } from "@mui/material";
import { DefaultTheme } from "@mui/styles";
import "../css/index.scss";
import { THEME_ID } from "../config";

// Default configurable files
import { defaultScssTheme } from "./defaultScssTheme";
import { defaultThemeConfig } from "../themes/default/themeConfig";
import { themeConfigMap } from "../themes/themeConfig";

export const validateScssColorFormat = (color: string | undefined): boolean => {
  // Validate the input color string is a valid color format #xxxxxx or #xxx
  if (!color) return false;
  const regex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/i;
  const testRegex = regex.test(color);
  return testRegex;
};

export const validatePaletteColor = (
  defaultScssMainColor: string,
  customScssMainColor: string
): PaletteColorOptions | undefined => {
  // Validate palette main colors, which cannot be undefined
  return validateScssColorFormat(customScssMainColor)
    ? {
        main: customScssMainColor,
      }
    : { main: defaultScssMainColor };
};

// Pages shared theme config
export interface PageBaseThemeConfig {
  pageTitle: string;
  appBarTitle?: string;
}

export interface LandingPortalThemeConfig extends PageBaseThemeConfig {
  introductionTitle?: string;
  introductionBodyHtml?: string | JSX.Element;
  lhCardTitle?: string;
  lhCardBodyHtml?: string | JSX.Element;
  lhCardActionsHtml?: string | JSX.Element;
  rhCardTitle?: string;
  rhCardBodyHtml?: string | JSX.Element;
  rhCardActionsHtml?: string | JSX.Element;
}

export interface DataStoreThemeConfig extends PageBaseThemeConfig {
  frontMatterTextHtml?: string | JSX.Element;
}

export interface ProvThemeConfig extends PageBaseThemeConfig {}

export interface RegistryThemeConfig extends PageBaseThemeConfig {}

export interface FooterThemeConfig {
  footerTitle?: string;
  footerDescriptionHtml?: string | JSX.Element;
  footerLhBodyHtml?: string | JSX.Element;
  footerRhBodyHtml?: string | JSX.Element;
}

export interface HamburgerNavigationConfig {
  docsName: string;
  docsLink: string;
}

export interface CompleteThemeConfig {
  // Structure for whole custom theme config

  // Global config
  backgroundImageURL?: string;
  faviconURL: string;
  appleTouchIconURL: string;
  footerConfig?: FooterThemeConfig;

  // Provide a way to override the docs display and link in the LH bar
  hamburgerNavigation: HamburgerNavigationConfig;

  // UI specific
  landingPortal: LandingPortalThemeConfig;
  dataStore: DataStoreThemeConfig;
  prov: ProvThemeConfig;
  registry: RegistryThemeConfig;
}

type CurrentPageThemeConfig =
  | LandingPortalThemeConfig
  | DataStoreThemeConfig
  | ProvThemeConfig
  | RegistryThemeConfig;

export type CurrentPage = "landingPortal" | "dataStore" | "prov" | "registry";

export interface PageThemeConfig {
  // For current page's output theme config
  backgroundImageURL?: string;
  faviconURL: string;
  appleTouchIconURL: string;
  footerConfig: FooterThemeConfig;

  // Provide a way to override the docs display and link in the LH bar
  hamburgerNavigation: HamburgerNavigationConfig;

  // Able to return for each page only
  // UI specific
  currentPageThemeConfig: CurrentPageThemeConfig;
}

export const getThemeConfig = (
  themeConfig: CompleteThemeConfig,
  currentPage: CurrentPage
): PageThemeConfig => {
  // For setting page title, app bar title and background image and UIs text content. -> themeCustomConfig.tsx / defaultThemeConfig

  // Pull out current page
  const currentPageConfig: CurrentPageThemeConfig = themeConfig[currentPage];

  return {
    backgroundImageURL: themeConfig.backgroundImageURL,
    faviconURL: themeConfig.faviconURL,
    appleTouchIconURL: themeConfig.appleTouchIconURL,
    footerConfig: themeConfig.footerConfig as FooterThemeConfig,
    hamburgerNavigation: themeConfig.hamburgerNavigation,
    currentPageThemeConfig: { ...currentPageConfig },
  };
};

export const getScssDefaultTheme = (
  themeConfig: Theme,
  backgroundImgURL: string | undefined
): DefaultTheme => {
  // For setting @mui/styles DefaultTheme, with our override properties.
  return {
    ...themeConfig,
    backgroundImgURL: backgroundImgURL,
  };
};

export const generateTheme = (scssModule: CSSModuleClasses): Theme =>
  createTheme({
    // For generating custom Theme with the scss config
    // Palette main colors cannot be undefined
    palette: {
      primary: validatePaletteColor(
        defaultScssTheme.palette.primary.main,
        scssModule.palettePrimaryMainColor
      ),
      secondary: validatePaletteColor(
        defaultScssTheme.palette.secondary.main,
        scssModule.paletteSecondaryMainColor
      ),
    },
    typography: {
      allVariants: { color: scssModule.basicFontColor },
      fontFamily: scssModule.globalFontFamily,
      fontSize: scssModule.globalFontSize as unknown as number,
      h1: { color: scssModule.h1Color },
      h2: { color: scssModule.h2Color },
      h3: { color: scssModule.h3Color },
      h4: { color: scssModule.h4Color },
      h5: { color: scssModule.h5Color },
    },
    components: {
      // Unite the button-contained colors
      MuiButtonBase: {
        styleOverrides: {
          root: {
            backgroundColor: "inherit",
            "&.MuiButton-contained": {
              color: defaultScssTheme.palette.common.white,
              background: scssModule.palettePrimaryMainColor,
            },
          },
        },
      },
      // Define the <a> text </a> link color
      MuiTypography: {
        styleOverrides: {
          root: {
            "& a:not([class])": {
              color: scssModule.globalALinkColor,
            },
            // Default drawer color
            "&.MuiListItemText-primary": {
              color: defaultScssTheme.palette.common.white,
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

export const mergeTheme = (customTheme?: Theme) => {
  // Merge custom theme based upon default theme
  if (customTheme === undefined) {
    return defaultScssTheme;
  } else {
    return createTheme({
      ...defaultScssTheme,
      ...customTheme,
    });
  }
};

// Map type for importing custom theme config
export interface ThemeConfigMapType {
  [themeName: string]: {
    scssConfig: CSSModuleClasses;
    themeConfig: CompleteThemeConfig;
  };
}

export const getCurrentThemeConfig = (
  currentPage: CurrentPage
): PageThemeConfig => {
  if (THEME_ID === "default" || themeConfigMap[THEME_ID] === undefined) {
    // return default theme config
    return getThemeConfig(defaultThemeConfig, currentPage);
  }
  // get custom theme config
  return getThemeConfig(themeConfigMap[THEME_ID].themeConfig, currentPage);
};

export const getCurrentScssTheme = (
  backgroundImgURL: string | undefined
): DefaultTheme => {
  if (THEME_ID === "default" || themeConfigMap[THEME_ID] === undefined) {
    // return default scss config as DefaultTheme
    return getScssDefaultTheme(defaultScssTheme, backgroundImgURL);
  }
  // For setting customized theme styles.
  const customTheme: Theme = generateTheme(themeConfigMap[THEME_ID].scssConfig);
  const mergedTheme: Theme = mergeTheme(customTheme);

  return getScssDefaultTheme(mergedTheme, backgroundImgURL);
};
