// Default Theme Config

import { Button } from "@mui/material";
import { CompleteThemeConfig } from "../../util/themeValidation";
import React from "react";
import { defaultScssTheme } from "../../util/defaultScssTheme";
import { DOCUMENTATION_BASE_URL } from "../../queries";

export const defaultThemeConfig: CompleteThemeConfig = {
    faviconURL: "/favicon_csiro.ico",
    appleTouchIconURL: "/favicon_csiro.png",
    footerConfig: {
        footerTitle: "Acknowledgement of Country",
        footerDescriptionHtml:
            "Provena respects and recognises all Traditional Owners of the land, sea and waters, on which we live and work on across Australia as First Nations Peoples holding the hopes, dreams, traditions and cultures of the region.",
        footerLhBodyHtml: "© Provena. All rights reserved.",
        footerRhBodyHtml: (
            <React.Fragment>
                <a href="https://gbrrestoration.org/terms-and-conditions/">
                    Terms &amp; Conditions
                    {/* // TODO, Link needs to be updated Terms &amp; Conditions */}
                </a>
                <a href="https://gbrrestoration.org/privacy-policy/">
                    Privacy Policy
                    {/* // TODO, Link needs to be updated Privacy Policy */}
                </a>
            </React.Fragment>
        ),
    },
    landingPortal: {
        pageTitle: "Provena",
        appBarTitle: "Provena",
        introductionTitle:
            "Discover, access, register, and explore Provena Data, Code, Provenance and Knowledge.",
        introductionBodyHtml: (
            <React.Fragment>
                To use Provena, begin by logging in and requesting access roles.
                Once you are logged in, you will need to request access to the
                system components you want to use. Information on this process
                is available. For more information on how to login and
                requesting access roles, visit our documentation.
            </React.Fragment>
        ),
        lhCardTitle: "About Provena",
        lhCardBodyHtml: (
            <React.Fragment>
                Provena aims to facilitate:
                <ul>
                    <li>Data and information capture and access.</li>
                    <li>
                        Information flows between modelling and decision support
                        teams.
                    </li>
                    <li>
                        Provision of information to support management
                        decisions.
                    </li>
                </ul>
                Learn more about in the Provena Documentation.
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
                    href={DOCUMENTATION_BASE_URL}
                    target="_blank"
                >
                    Provena Documentation
                </Button>
            </React.Fragment>
        ),
        rhCardTitle: "Provena Support",
        rhCardBodyHtml: (
            <React.Fragment>
                <p>
                    As an open-source system, Provena values transparency and
                    community support. Discover a wealth of information and
                    assistance in our support resources, accessible via the
                    Provena Resources.
                </p>
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
                    href="https://github.com/provena"
                    target="_blank"
                >
                    Provena Resources
                </Button>
            </React.Fragment>
        ),
    },
    dataStore: {
        pageTitle: "Provena Data Store",
        appBarTitle: "Provena Data Store",
        frontMatterTextHtml:
            "Discover, access and register Provena Modelling and Decision Support data",
    },
    prov: {
        pageTitle: "Provena Provenance Store",
        appBarTitle: "Provena Provenance Store",
    },
    registry: {
        pageTitle: "Provena Entity Registry",
        appBarTitle: "Provena Entity Registry",
    },
};
