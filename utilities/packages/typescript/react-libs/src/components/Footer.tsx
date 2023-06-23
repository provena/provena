import { FooterThemeConfig } from "../util/themeValidation";
import "../css/Footer.scss";

export const Footer = (footerConfig: FooterThemeConfig) => (
    <div className="footer">
        <div className="footer-container">
            <div>
                <div>
                    <h3>{footerConfig.footerTitle}</h3>
                </div>
                <div>{footerConfig.footerDescriptionHtml}</div>
            </div>
            <div className="footer-divider">
                <span></span>
            </div>
            <div className="footer-acknowledge">
                <div>{footerConfig.footerLhBodyHtml}</div>
                <div>{footerConfig.footerRhBodyHtml}</div>
            </div>
        </div>
    </div>
);
