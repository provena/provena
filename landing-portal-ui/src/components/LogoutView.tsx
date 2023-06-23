import React from "react";
import makeStyles from "@mui/styles/makeStyles";
import createStyles from "@mui/styles/createStyles";
import { Theme } from "@mui/material/styles";
import { Button } from "@mui/material";
import { observer } from "mobx-react-lite";
import { useKeycloak } from "@react-keycloak/web";

interface Props {}

const useStyles = makeStyles((theme: Theme) => createStyles({}));

export const LogoutView = observer((props: Props) => {
    // Setup theming
    const classes = useStyles();
    const { keycloak } = useKeycloak();

    return (
        <React.Fragment>
            <h3>Logout</h3>
            <Button variant="outlined" onClick={() => keycloak.logout()}>
                Logout
            </Button>
        </React.Fragment>
    );
});
