import { Button, CircularProgress, Theme } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { useKeycloak } from "@react-keycloak/web";
import { Route, RouteProps } from "react-router-dom";
import { BoundedContainer } from "../components";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            display: "flex",
            flexFlow: "column",
            minHeight: "60vh",
            backgroundColor: "white",
            justifyContent: "top",
            alignItems: "center",
            marginBottom: theme.spacing(10),
            padding: theme.spacing(4),
            borderRadius: 5,
        },
        margin: {
            margin: theme.spacing(1),
            width: 400,
        },
        button: {
            margin: 20,
        },
    })
);

export const ProtectedRoute: React.FC<RouteProps> = ({
    children,
    ...props
}) => {
    const classes = useStyles();
    const { keycloak } = useKeycloak();
    if (keycloak.authenticated !== undefined) {
        if (keycloak.authenticated) {
            return <Route {...props}>{children}</Route>;
        } else {
            return (
                <Route
                    {...props}
                    render={(props) => {
                        return (
                            <BoundedContainer breakpointKey={"lg"}>
                                <div className={classes.root}>
                                    <p>
                                        You are not authorized to view this
                                        content, please click the following
                                        button to login.{" "}
                                    </p>
                                    <Button
                                        className={classes.button}
                                        color="primary"
                                        variant="contained"
                                        id="prompt-login-button"
                                        onClick={() => keycloak.login()}
                                    >
                                        Login
                                    </Button>
                                </div>
                            </BoundedContainer>
                        );
                    }}
                />
            );
        }
    } else {
        return (
            <Route
                {...props}
                render={(props) => {
                    return (
                        <div className={classes.root}>
                            <p>
                                You are trying to access a protected resource,
                                please wait while the system logs you in.
                            </p>
                            <CircularProgress />
                        </div>
                    );
                }}
            />
        );
    }
};
