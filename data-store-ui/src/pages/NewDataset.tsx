import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import { observer } from "mobx-react-lite";
import { useEffect } from "react";
import {
  Form,
  useUserLinkEnforcer,
  userLinkEnforcerDocumentationLink,
  userLinkEnforcerProfileLink,
} from "react-libs";
import { useHistory } from "react-router-dom";
import newDatasetStore from "../stores/registerOrModifyStore";
import { fields, uiSchema } from "../util/formUtil";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: "flex",
      flexWrap: "wrap",
      flexFlow: "column",
      justifyContent: "center",
      alignItems: "center",
      backgroundColor: "white",
      padding: theme.spacing(4),
      marginBottom: 20,
      minHeight: "60vh",
      borderRadius: 5,
    },
    button: {
      marginRight: theme.spacing(1),
    },
    instructions: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(1),
    },
    centerLoading: {
      display: "flex",
      justifyContent: "center",
    },
  }),
);

const overrideMissingLinkMessage = (
  <p>
    You cannot register a Dataset without linking your user account to a
    registered Person in the Registry. For more information, visit{" "}
    <a
      href={userLinkEnforcerDocumentationLink}
      target="_blank"
      rel="noreferrer"
    >
      our documentation
    </a>
    . You can link your user account to a Person by visiting your{" "}
    <a href={userLinkEnforcerProfileLink} target="_blank" rel="noreferrer">
      user profile
    </a>
    . If you believe you have already linked your user account to a Person in
    the registry, try refreshing this page.
  </p>
);

export interface NewDatasetProps {}
const NewDataset = observer((props: NewDatasetProps) => {
  const classes = useStyles();
  const history = useHistory();

  useEffect(() => {
    newDatasetStore.loadSchemaFirstTime();
  }, []);

  // user id link enforcer (enabled for Datasets)
  const linkEnforcer = useUserLinkEnforcer({
    blockEnabled: true,
    blockOnError: true,
    missingLinkMessage: overrideMissingLinkMessage,
  });

  // display error if link is not established
  if (linkEnforcer.blocked) {
    return (
      <div className={classes.root} style={{ width: "100%" }}>
        {linkEnforcer.render}
      </div>
    );
  }

  if (newDatasetStore.schemaReady) {
    // Display the schema
    return (
      <div className={classes.root}>
        <Grid container>
          <Form
            schema={newDatasetStore.schema as RJSFSchema}
            uiSchema={uiSchema}
            validator={validator}
            fields={fields}
            onError={(errors) => {
              console.log("Errors");
              console.log(JSON.stringify(newDatasetStore.currentValue));
            }}
            onSubmit={({ formData }) => {
              newDatasetStore.registerDatasetAction(
                formData as unknown as JSON,
                history,
              );
            }}
            onChange={({ formData }) => {
              newDatasetStore.onFormChange(formData as JSON);
            }}
            formData={newDatasetStore.currentValue}
            id="registration-form"
          ></Form>
        </Grid>
        <Dialog open={newDatasetStore.processing}>
          <DialogTitle>{newDatasetStore.processing}</DialogTitle>
          <DialogContent>
            <DialogContent>
              <p>{newDatasetStore.processingMessage}</p>
            </DialogContent>
          </DialogContent>
        </Dialog>
        <Dialog open={newDatasetStore.error}>
          <DialogTitle> An Error Occurred!</DialogTitle>
          <DialogContent>
            <DialogContent>
              <p>{newDatasetStore.errorMessage}</p>
            </DialogContent>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => newDatasetStore.closeErrorDialog()}>
              Acknowledge
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    );
  } else {
    // Otherwise get the schema
    return (
      <div className={classes.root}>Please wait... retrieving schema form.</div>
    );
  }
});

export default NewDataset;
