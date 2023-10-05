import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";
import { IconButton, Input } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { observer } from "mobx-react-lite";
import { Link } from "react-router-dom";
import { SEARCH_QUERY_STRING_KEY } from "../hooks/searchQueryString";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            height: theme.spacing(8),
            display: "flex",
            justifyContent: "space-between",
            boxShadow: "rgba(99, 99, 99, 0.2) 0px 2px 8px 0px",
            marginTop: theme.spacing(3),
            marginBottom: theme.spacing(3),
            "&:hover": {
                boxShadow: "rgba(120, 120, 120, 0.3) 0px 3px 10px 0px",
            },
        },
        iconButton: {
            color: theme.palette.action.active,
            marginRight: theme.spacing(1),
        },

        icon: {
            width: theme.spacing(6),
        },
        input: {
            fontSize: 24,
            width: "100%",
            color: "gray",
        },
        searchContainer: {
            margin: "auto 16px",
            width: "100%", // 6 button + 4 margin
        },
    })
);

interface DatasetSearchLinkedProps {
    query: string;
    setQuery: (query: string) => void;
    needClearIcon: boolean;
}
export const DatasetSearchLinked = observer(
    (props: DatasetSearchLinkedProps) => {
        const classes = useStyles();
        const link = `/datasets?${SEARCH_QUERY_STRING_KEY}=${props.query}`;
        return (
            <div className={classes.root}>
                <div className={classes.searchContainer}>
                    <Input
                        className={classes.input}
                        fullWidth
                        disableUnderline
                        value={props.query}
                        onChange={(ele) => {
                            props.setQuery(ele.currentTarget.value);
                        }}
                        placeholder="Search Datasets ..."
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                // Enter key down
                                window.open(link, "_self");
                            }
                        }}
                    ></Input>
                </div>

                {/* if need to show clear icon: show no button for empty input,
                    for non-empty input, show clear icon and clear the input string when pressed the icon;
                    While if no need to show clear icon: always show the magnify glass icon,
                    and search for query when pressed the icon, even for an empty input.
                */}
                {props.needClearIcon ? (
                    props.query !== "" && (
                        <IconButton
                            className={classes.iconButton}
                            size="large"
                            onClick={() => {
                                props.setQuery("");
                            }}
                        >
                            <ClearIcon className={classes.icon} />
                        </IconButton>
                    )
                ) : (
                    <IconButton
                        className={classes.iconButton}
                        size="large"
                        component={Link}
                        to={link}
                    >
                        <SearchIcon className={classes.icon} />
                    </IconButton>
                )}
            </div>
        );
    }
);
