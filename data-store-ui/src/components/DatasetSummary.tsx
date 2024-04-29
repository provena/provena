import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Link } from "react-router-dom";
import { RenderLongTextExpand, timestampToLocalTime } from "react-libs";
import { ItemDataset } from "../provena-interfaces/RegistryAPI";
import { AuthorCompactDisplayComponent } from "./DatasetDisplayParts";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: "flex",
      flexWrap: "wrap",
      flexFlow: "column",
      justifyContent: "left",
      alignItems: "left",
      marginTop: 10,
      borderBottom: "1px solid gray",
    },
    button: {
      marginRight: theme.spacing(1),
    },
    instructions: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(1),
    },
    datasetHeader: {
      marginTop: theme.spacing(1),
      fontSize: 24,
    },
    datasetMeta: {
      fontSize: 14,
      color: "gray",
    },
  }),
);

type DatasetPropsType = {
  dataset: ItemDataset;
};

const Dataset = (props: DatasetPropsType) => {
  const classes = useStyles();
  const dataset = props.dataset;

  // How many characters need to be left as "View less" text for long dataset description
  const descriptionInitialCharNum = 500;

  const createdTime = timestampToLocalTime(props.dataset.created_timestamp);

  return (
    <div className={classes.root}>
      <div className={classes.datasetHeader}>
        <Link to={`/dataset/${dataset.id}`}>
          {" "}
          {dataset.collection_format.dataset_info.name}
          {!!dataset.versioning_info?.version &&
            ` (V${dataset.versioning_info?.version})`}
        </Link>
      </div>
      <div>
        <AuthorCompactDisplayComponent username={dataset.owner_username} />
      </div>
      <div>
        <RenderLongTextExpand
          text={dataset.collection_format.dataset_info.description}
          initialCharNum={descriptionInitialCharNum}
        />
      </div>
      <div className={classes.datasetMeta}>
        <div>Record creation time: {createdTime}</div>
      </div>
      <hr />
    </div>
  );
};

export default Dataset;
