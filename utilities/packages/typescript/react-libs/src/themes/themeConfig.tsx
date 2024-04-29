// File for importing custom configs
import { ThemeConfigMapType } from "../util/themeValidation";

// Custom themes
import rrapScssTheme from "./rrap/scssConfig.module.scss";
import { rrapThemeConfig } from "./rrap/themeConfig";

import exampleScssTheme from "./example/scssConfig.module.scss";
import { exampleThemeConfig } from "./example/themeConfig";

/*
Map for importing custom theme config

The themeConfigMap is imported and used in other files, 
so please be careful when changing the map's name and type.

interface ThemeConfigMapType {
    [themeName: string]: {
        scssConfig: CSSModuleClasses;
        themeConfig: CompleteThemeConfig;
    };
}

Default theme is named as themeName: "default",
we can directly use "default" in UI's index.tsx
*/

export const themeConfigMap: ThemeConfigMapType = {
  rrap: {
    scssConfig: rrapScssTheme,
    themeConfig: rrapThemeConfig,
  },
  example: {
    scssConfig: exampleScssTheme,
    themeConfig: exampleThemeConfig,
  },
};
