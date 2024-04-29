import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import { observer } from "mobx-react-lite";
import React from "react";
import { CopyFloatingButton } from "react-libs";

interface TokenProps {}

const useStyles = makeStyles((theme: Theme) => createStyles({}));

export const TokenOverview = observer((props: TokenProps) => {
  // Setup theming
  const classes = useStyles();
  const { keycloak } = useKeycloak();

  return (
    <React.Fragment>
      <h3>Token</h3>
      <div
        style={{
          wordWrap: "break-word",
          color: "#333",
          padding: "10px",
          backgroundColor: "#F5F5F5",
          border: "1px solid #ccc",
          borderRadius: "4px",
        }}
      >
        {" "}
        <CopyFloatingButton clipboardText={keycloak.token || ""} />
        {keycloak.token || "None"}
      </div>
    </React.Fragment>
  );
});
