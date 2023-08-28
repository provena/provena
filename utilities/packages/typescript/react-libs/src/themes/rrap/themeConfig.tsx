// Default Theme Config

import { Button } from "@mui/material";
import React from "react";
import { defaultScssTheme } from "../../util/defaultScssTheme";
import { CompleteThemeConfig } from "../../util/themeValidation";
import { DOCUMENTATION_BASE_URL } from "../../queries";

export const rrapThemeConfig: CompleteThemeConfig = {
    backgroundImageURL: "https://static.rrap-is.com/image/imgHeaderHome.jpg",
    faviconURL: "/favicon.ico",
    appleTouchIconURL: "/logo192.png",
    footerConfig: {
        footerTitle: "Acknowledgement of Country",
        footerDescriptionHtml:
            "The Reef Restoration and Adaptation Program respects and recognises all Traditional Owners of the Great Barrier Reef as First Nations Peoples holding the hopes, dreams, traditions and cultures of the Reef.",
        footerLhBodyHtml:
            "© Reef Restoration and Adaptation Program. All rights reserved.",
        footerRhBodyHtml: (
            <React.Fragment>
                <a href="https://gbrrestoration.org/terms-and-conditions/">
                    Terms &amp; Conditions
                </a>
                <a href="https://gbrrestoration.org/privacy-policy/">
                    Privacy Policy
                </a>
            </React.Fragment>
        ),
    },
    landingPortal: {
        pageTitle: "RRAP M&DS Information System",
        appBarTitle: "RRAP M&DS Information System",
        introductionTitle:
            "Discover, access, register, and explore RRAP M&DS Data, Code, Provenance and Knowledge.",
        introductionBodyHtml: (
            <React.Fragment>
                To use the RRAP M&DS IS, begin by logging in and requesting
                access roles. Once you are logged in, you will need to request
                access to the system components you want to use. Information on
                this process is available. For more information on how to login
                and requesting access roles, visit our documentation.
            </React.Fragment>
        ),
        lhCardTitle: "About the RRAP M&DS",
        lhCardBodyHtml: (
            <React.Fragment>
                The Reef Restoration and Adaptation Program (RRAP) is a
                collaboration of Australia's leading experts to create a suite
                of innovative and targeted measures to help preserve and restore
                the Great Barrier Reef. These interventions must have strong
                potential for positive impact, be socially and culturally
                acceptable, ecologically-sound, ethical and financially
                responsible. They would be implemented if, when and where it is
                decided action is needed - and only after rigorous assessment
                and testing. Learn more about the Reef Restoration and
                Adaptation Program{" "}
                <a href="https://gbrrestoration.org/" target="_blank">
                    here
                </a>
                .
            </React.Fragment>
        ),
        lhCardActionsHtml: (
            <React.Fragment>
                <Button
                    style={
                        {
                            marginTop: defaultScssTheme.spacing(3),
                            marginBottom: defaultScssTheme.spacing(4),
                            marginRight: defaultScssTheme.spacing(1),
                        } as React.CSSProperties
                    }
                    variant="outlined"
                    href="https://gbrrestoration.org/"
                    target="_blank"
                >
                    About RRAP
                </Button>
                <Button
                    style={
                        {
                            marginTop: defaultScssTheme.spacing(3),
                            marginBottom: defaultScssTheme.spacing(4),
                            marginRight: defaultScssTheme.spacing(1),
                        } as React.CSSProperties
                    }
                    variant="outlined"
                    href="https://gbrrestoration.org/program/modelling-and-decision-support/"
                    target="_blank"
                >
                    About RRAP M&DS
                </Button>
            </React.Fragment>
        ),
        rhCardTitle: "About the RRAP M&DS IS",
        rhCardBodyHtml: (
            <React.Fragment>
                The RRAP M&DS Information System (IS) aims to facilitate:
                <ul>
                    <li>Data and information capture and access,</li>
                    <li>
                        Information flows between modelling and decision support
                        teams,
                    </li>
                    <li>
                        Provision of information to support management decisions
                        in RRAP
                    </li>
                </ul>
                Learn more about in the M&DS IS Specification.
            </React.Fragment>
        ),
        rhCardActionsHtml: (
            <React.Fragment>
                <Button
                    style={
                        {
                            marginTop: defaultScssTheme.spacing(3),
                            marginBottom: defaultScssTheme.spacing(4),
                            marginRight: defaultScssTheme.spacing(1),
                        } as React.CSSProperties
                    }
                    variant="outlined"
                    href="https://static.rrap-is.com/assets/RRAP+M%26DS-02+Information+System+Specification+high+level+view.pdf"
                    target="_blank"
                >
                    RRAP M&DS IS Specification
                </Button>
                <Button
                    style={
                        {
                            marginTop: defaultScssTheme.spacing(3),
                            marginBottom: defaultScssTheme.spacing(4),
                            marginRight: defaultScssTheme.spacing(1),
                        } as React.CSSProperties
                    }
                    variant="outlined"
                    href={DOCUMENTATION_BASE_URL + "/information-system/"}
                    target="_blank"
                >
                    User docs
                </Button>
            </React.Fragment>
        ),
    },
    dataStore: {
        pageTitle: "RRAP M&DS IS Data Store",
        appBarTitle: "RRAP M&DS Data Store",
        frontMatterTextHtml:
            "Discover, access and register Reef Restoration and Adaptation Program Modelling and Decision Support data",
    },
    prov: {
        pageTitle: "RRAP Provenance Store",
        appBarTitle: "RRAP M&DS Provenance Store",
    },
    registry: {
        pageTitle: "RRAP Entity Registry",
        appBarTitle: "RRAP M&DS Entity Registry",
    },
};
