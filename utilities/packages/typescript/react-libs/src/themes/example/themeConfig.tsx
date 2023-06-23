// Custom Theme Config

import { CompleteThemeConfig } from "../../util/themeValidation";

export const exampleThemeConfig: CompleteThemeConfig = {
    // backgroundImageURL is used for setting UI DefaultTheme config, only landing portal doesn't have background image
    backgroundImageURL: "url/to/backgroundImage",
    faviconURL: "url/to/favivon.ico",
    appleTouchIconURL: "url/to/favicon.png",
    footerConfig: {
        footerTitle: "footer title",
        footerDescriptionHtml: "footer description",
        footerLhBodyHtml: "footer left-hand-side text",
        footerRhBodyHtml: "footer right-hand-side text",
    },
    landingPortal: {
        pageTitle: "landing page title",
        appBarTitle: "landing app bar title",
        introductionTitle: "landing description title",
        introductionBodyHtml: "landing introduction text",
        lhCardTitle: "landing left-hand-side card title",
        lhCardBodyHtml: "landing left-hand-side card body",
        lhCardActionsHtml: "landing left-hand-side card actions",
        rhCardTitle: "landing right-hand-side card title",
        rhCardBodyHtml: "landing right-hand-side card body",
        rhCardActionsHtml: "landing right-hand-side card actions",
    },
    dataStore: {
        pageTitle: "data store page title",
        appBarTitle: "data store app bar title",
        frontMatterTextHtml: "data store front matter text",
    },
    prov: {
        pageTitle: "provenance store page title",
        appBarTitle: "provenance store app bar title",
    },
    registry: {
        pageTitle: "entity registry page title",
        appBarTitle: "entity registry app bar title",
    },
};
