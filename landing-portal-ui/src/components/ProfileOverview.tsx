import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import { observer } from "mobx-react-lite";
import React from "react";
import { DOCUMENTATION_BASE_URL } from "react-libs";

interface ProfileOverviewProps {}

const useStyles = makeStyles((theme: Theme) => createStyles({}));

export const ProfileOverview = observer((props: ProfileOverviewProps) => {
  // Setup theming
  const classes = useStyles();
  const { keycloak } = useKeycloak();

  return (
    <React.Fragment>
      <h3>User Name</h3>
      {keycloak.tokenParsed!.name}
      <h3>User Email</h3>
      {keycloak.tokenParsed!.email}
      <h3>Authorization</h3>
      You can use the <i>Roles</i> tab on the left to request authorisation. For
      more information, visit{" "}
      <a
        href={
          DOCUMENTATION_BASE_URL +
          "/getting-started-is/requesting-access-is.html"
        }
        target="_blank"
      >
        our documentation
      </a>
      .
    </React.Fragment>
  );
});
