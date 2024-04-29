import { Breadcrumbs, Link } from "@mui/material";
import { Link as RouteLink } from "react-router-dom";
import { LinkType } from "../types/types";
type BreadcrumbLinksPropsType = {
  links: Array<LinkType>;
};
const BreadcrumbLinks = (props: BreadcrumbLinksPropsType) => {
  const links = props.links;
  return (
    <Breadcrumbs>
      {links.map((link) => (
        <Link
          underline="hover"
          color="inherit"
          component={RouteLink}
          to={link.link}
        >
          {link.label}
        </Link>
      ))}
    </Breadcrumbs>
  );
};

export default BreadcrumbLinks;
