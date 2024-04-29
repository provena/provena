import AccountCircle from "@mui/icons-material/AccountCircle";
import { Box, Button, IconButton, Theme, useTheme } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { useKeycloak } from "@react-keycloak/web";
import { Link as RouterLink } from "react-router-dom";

export const DEFAULT_PROFILE_POSTFIX = "/profile";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    username: {
      display: "flex",
      justifyContent: "center",
      alignContent: "center",
      flexDirection: "column",
      // Put some margin on left side
      // away from left border of box
      marginLeft: 5,
    },
  }),
);

interface ProfileIconProps {
  username?: string;
  isLoggedIn: boolean;
  profilePostfix?: string;
}

export const ProfileIcon = (props: ProfileIconProps) => {
  /**
     Designed to react to whether the user is logged in. When 
     logged in, a profile icon and link will be shown. When not 
     logged in a button to login to the system will be shown.
     */

  // Setup theming
  const classes = useStyles();
  const { keycloak } = useKeycloak();

  const profilePostfix = props.profilePostfix ?? DEFAULT_PROFILE_POSTFIX;

  if (props.isLoggedIn) {
    return (
      <Box
        sx={{
          display: { xs: "none", md: "flex" },
          borderLeft: 2,
        }}
      >
        <div className={classes.username}>{props.username ?? ""}</div>
        <IconButton
          to={profilePostfix}
          component={RouterLink}
          color="inherit"
          size="large"
          id="profile-button"
        >
          <AccountCircle />
        </IconButton>
      </Box>
    );
  } else {
    return (
      <Box sx={{ display: { xs: "none", md: "flex" } }}>
        <Button
          variant="contained"
          onClick={() => {
            keycloak.login();
          }}
          id="login-tab-button"
        >
          Click to login
        </Button>
      </Box>
    );
  }
};
