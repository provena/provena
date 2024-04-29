import { Box, List, ListItem, ListItemText, Theme } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";

export interface NavListItem {
  listText: string;
  href: string;
}

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    margin: {
      margin: theme.spacing(1),
      color: "white",
    },
    extendedIcon: {
      marginRight: theme.spacing(1),
    },
    menuSliderContainer: {
      paddingTop: 200,
      width: 250,
      background: "#7c7c7c",
      height: "100%",
    },
    avatar: {
      margin: "0.5rem auto",
      padding: "1rem",
      width: theme.spacing(13),
      height: theme.spacing(13),
    },
    listItem: {
      color: "white",
    },
  }),
);

export interface SideNavBoxProps {
  navListItems: Array<NavListItem>;
}

export const SideNavBox = (props: SideNavBoxProps) => {
  const classes = useStyles();

  return (
    <Box className={classes.menuSliderContainer} component="div">
      <List>
        {props.navListItems.map((listItem, index) => (
          <ListItem
            className={classes.listItem}
            button
            key={index}
            component="a"
            href={listItem.href}
          >
            <ListItemText primary={listItem.listText} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};
