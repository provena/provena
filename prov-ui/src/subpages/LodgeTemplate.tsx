import React from "react";
import { observer } from "mobx-react-lite";
import { ChangeEvent, useState } from "react";

import { useQuery } from "@tanstack/react-query";

import {
  Alert,
  Button,
  CircularProgress,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { submitModelRunRecords, uploadCSVTemplate } from "../queries/ingest";

import {
  ConvertModelRunsResponse,
  ModelRunRecord,
} from "../provena-interfaces/ProvenanceAPI";
import {
  BatchDetailedView,
  JOB_LIST_ROUTE,
  SingleJobDetailsComponent,
  useUserLinkEnforcer,
  userLinkEnforcerDocumentationLink,
  userLinkEnforcerProfileLink,
} from "react-libs";

import RegenerateCSV from "../components/RegenerateCSV";

import { RegisterBatchModelRunResponse } from "react-libs/provena-interfaces/ProvenanceAPI";
import {
  JobStatusTable,
  ProvLodgeBatchSubmitResult,
} from "react-libs/provena-interfaces/AsyncJobAPI";
import { Link } from "react-router-dom";

const overrideMissingLinkMessage = (
  <p>
    You cannot lodge Model Runs without linking your user account to a
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
    .
  </p>
);

interface SelectTemplateFileProps {
  file: File | undefined;
  setFile: (file?: File) => void;
  setFileId: (id?: string) => void;
  onReset: () => void;
}
const UploadTemplateFile = observer((props: SelectTemplateFileProps) => {
  /**
    Component: UploadTemplateFile
    
     */
  const fileUploaded = props.file !== undefined;

  const fileUploadedContent = (
    <Grid container xs={12} alignItems="center" justifyContent="space-between">
      <Grid item>
        Successfully selected file <b>{props.file?.name}</b>.
      </Grid>
      <Grid item>
        <Button color="error" variant="contained" onClick={props.onReset}>
          Reset
        </Button>
      </Grid>
    </Grid>
  );

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      props.setFile(e.target.files[0]);
      props.setFileId((e.target.files[0].name + Date.now()) as string);
    }
  };

  const requireUploadContent = (
    <Stack spacing={2}>
      <Typography variant="h6">
        Begin by uploading a CSV template file
      </Typography>
      <Alert style={{ width: "100%" }} severity="info">
        If you have already registered your model runs, you can review the
        status of your submission tasks by clicking{" "}
        <Link to={JOB_LIST_ROUTE}>here</Link>.
      </Alert>
      <Stack
        direction="row"
        spacing={2}
        divider={<Divider orientation="vertical" flexItem />}
        justifyContent="center"
        alignItems="center"
      >
        <Grid item>
          <Typography variant="subtitle1">
            Please select the CSV template file:
          </Typography>
        </Grid>
        <Grid item>
          <input type="file" onChange={handleFileChange} />
        </Grid>
      </Stack>
    </Stack>
  );

  if (fileUploaded) {
    return fileUploadedContent;
  } else {
    return requireUploadContent;
  }
});

interface SubmitTemplateFileProps {
  file: File;
  uploaded: boolean;
  queryId: string;
  setUploaded: (uploaded: boolean) => void;
  newRecords?: Array<ModelRunRecord>;
  setNewRecords: (records?: Array<ModelRunRecord>) => void;
}
const SubmitTemplateFile = observer((props: SubmitTemplateFileProps) => {
  /**
   * Component: SubmitTemplateFile
   *
   */
  const { isError, error, isSuccess, isFetching, data } = useQuery({
    queryKey: ["convert" + props.queryId],
    queryFn: () => uploadCSVTemplate(props.file),
    enabled: props.uploaded,
    onSuccess(data) {
      // When the data is received, set the prop
      const response = data as ConvertModelRunsResponse;
      props.setNewRecords(response.new_records!);
    },
  });

  if (isFetching) {
    return (
      <Stack direction="row" justifyContent="center" spacing={3}>
        <Typography>Submitting CSV template, please wait ...</Typography>
        <CircularProgress />
      </Stack>
    );
  }

  if (isSuccess) {
    const response = data as ConvertModelRunsResponse;
    props.setNewRecords(response.new_records!);
    return (
      <Typography variant="subtitle1">
        Successfully converted the provided CSV template into model run records.
        <ul>
          <li>
            <b>New records:</b> {response.new_records?.length ?? "Error..."}
          </li>
          <li>
            <b>Existing records:</b>{" "}
            {response.existing_records?.length ?? "Error..."}
          </li>
        </ul>
      </Typography>
    );
  }

  if (isError) {
    return <p>An error occurred, error: {error}.</p>;
  }

  // Awaiting upload
  return (
    <Stack spacing={2}>
      <Typography variant="h6">Upload your CSV file</Typography>
      <Stack
        direction="row"
        divider={<Divider orientation="vertical" flexItem />}
        alignItems="center"
        justifyContent="left"
        spacing={2}
      >
        <Grid item xs={6}>
          <Typography variant="subtitle1">
            Please click the upload button to convert your CSV template to
            validated model run records.
          </Typography>
        </Grid>
        <Grid item>
          <Button
            variant="contained"
            color="success"
            onClick={() => {
              props.setUploaded(true);
            }}
          >
            Upload
          </Button>
        </Grid>
      </Stack>
    </Stack>
  );
});

interface MonitorBatchSubmissionComponentProps {
  setBatchId: (id: string) => void;
  batchJobSessionId: string;
}
const MonitorBatchSubmissionComponent = (
  props: MonitorBatchSubmissionComponentProps,
) => {
  /**
    Component: MonitorBatchSubmissionComponent

    Renders a non compact status display of a job. 

    Monitors for a successful job to pull the batch id from the job result.    
    */
  const onJobSuccess = (data: JobStatusTable) => {
    const result = data.result as unknown as ProvLodgeBatchSubmitResult;
    props.setBatchId(result.batch_id);
  };

  return (
    <SingleJobDetailsComponent
      refetchOnError={true}
      sessionId={props.batchJobSessionId}
      showIO={false}
      key={props.batchJobSessionId}
      onJobSuccess={onJobSuccess}
      adminMode={false}
    ></SingleJobDetailsComponent>
  );
};

interface LodgeJobsProps {
  submitted: boolean;
  queryId: string;
  setSubmitted: (submitted: boolean) => void;
  records: Array<ModelRunRecord>;
  batchJobSessionId?: string;
  setBatchJobSessionId: (id: string) => void;
}
const LodgeJobs = observer((props: LodgeJobsProps) => {
  /**
   * Component: LodgeJobs
   *
   */

  const { isError, error, isSuccess, isFetching } = useQuery({
    queryKey: ["submit" + props.queryId],
    queryFn: () => submitModelRunRecords(props.records),
    enabled: props.submitted,
    onSuccess(data) {
      // When the data is received, set the prop
      const response = data as RegisterBatchModelRunResponse;
      props.setBatchJobSessionId(response.session_id!);
    },
  });

  if (isFetching) {
    return (
      <Stack direction="row" justifyContent="center" spacing={3}>
        <Typography>Submitting CSV template, please wait ...</Typography>
        <CircularProgress />
      </Stack>
    );
  }

  if (isSuccess) {
    return (
      <Typography variant="subtitle1">
        Successfully initiated batch task. You can monitor the task below.
      </Typography>
    );
  }

  if (isError) {
    return (
      <p>An error occurred while lodging model run records, error: {error}.</p>
    );
  }

  if (props.records.length === 0) {
    return (
      <Stack spacing={2}>
        <Typography variant={"h6"}>No new records</Typography>
        <Typography variant={"subtitle1"}>
          The provided CSV file contained <b>no new records</b> to lodge. No
          action is required. If you would like to register additional model
          runs, you should add new rows to your CSV file.
        </Typography>
      </Stack>
    );
  }

  // Awaiting submission
  return (
    <Stack direction="column" spacing={2}>
      <Typography variant="h6">Lodge model run records in bulk</Typography>

      <Stack
        direction="row"
        divider={<Divider orientation="vertical" flexItem />}
        spacing={3}
        justifyContent="center"
        alignItems="center"
      >
        <Grid item xs={6}>
          <Typography variant="subtitle1">
            You have {props.records.length} new records to submit. Click the
            submit button to register the records.
          </Typography>
        </Grid>
        <Grid item>
          <Button
            variant="contained"
            color="success"
            onClick={() => {
              props.setSubmitted(true);
            }}
          >
            Submit
          </Button>
        </Grid>
      </Stack>
    </Stack>
  );
});

export interface SingleJobFocusComponentProps {
  sessionId: string;
  onExit: () => void;
  backMessage?: string;
}
export const SingleJobFocusComponent = (
  props: SingleJobFocusComponentProps,
) => {
  /**
    Component: SingleJobFocusComponent

    Controls and focussed on single standalone session 
    */
  return (
    <Stack spacing={2}>
      <Stack direction="row" justifyContent={"flex-start"}>
        <Button variant="contained" onClick={props.onExit}>
          {props.backMessage ?? "Back"}
        </Button>
      </Stack>
      <SingleJobDetailsComponent
        refetchOnError={false}
        sessionId={props.sessionId}
        showIO={true}
        key={props.sessionId}
        adminMode={false}
      ></SingleJobDetailsComponent>
    </Stack>
  );
};

interface MonitorJobsProps {
  batchId: string;
}

const MonitorJobs = observer((props: MonitorJobsProps) => {
  /**
   * Component: MonitorJobs
   *
   */

  const [focusedSessionId, setFocusedSessionId] = useState<string | undefined>(
    undefined,
  );

  // Reset this control state
  const reset = () => {
    setFocusedSessionId(undefined);
  };

  // Render a data grid with the jobs and status
  return (
    <Stack spacing={2}>
      <Typography variant="h6">
        Your jobs were lodged successfully, you can explore them below.
      </Typography>
      {focusedSessionId === undefined ? (
        <React.Fragment>
          <Typography variant="subtitle2">
            It may take some time for the records to appear below. Try using the
            refresh button after a few seconds.
          </Typography>
          <BatchDetailedView
            batchId={props.batchId}
            onJobSelected={(id) => {
              setFocusedSessionId(id);
            }}
            adminMode={false}
          ></BatchDetailedView>
        </React.Fragment>
      ) : (
        <SingleJobFocusComponent onExit={reset} sessionId={focusedSessionId} />
      )}
    </Stack>
  );
});

interface LodgeTemplateProps {}

const LodgeTemplate = observer((props: LodgeTemplateProps) => {
  /**
   * Component: LodgeTemplate
   *
   */
  const [uploadedFile, setUploadedFile] = useState<File | undefined>(undefined);
  const [queryId, setQueryId] = useState<string | undefined>(undefined);
  const [modelRunRecords, setModelRunRecords] = useState<
    Array<ModelRunRecord> | undefined
  >(undefined);
  const [uploaded, setUploaded] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [batchId, setBatchId] = useState<string | undefined>(undefined);
  const [batchJobSessionId, setBatchJobSessionId] = useState<
    string | undefined
  >(undefined);
  const [generateDownloaded, setGenerateDownloaded] = useState<boolean>(false);

  const clearAll = () => {
    // This method resets the state of the current workflow
    setUploadedFile(undefined);
    setQueryId(undefined);
    setModelRunRecords(undefined);
    setBatchJobSessionId(undefined);
    setUploaded(false);
    setSubmitted(false);
    setBatchId(undefined);
    setGenerateDownloaded(false);
  };

  // User link enforcement
  const linkEnforcer = useUserLinkEnforcer({
    // TODO re-enable when ready
    blockEnabled: false,
    // TODO re-enable when ready
    blockOnError: false,
    missingLinkMessage: overrideMissingLinkMessage,
  });

  // display error if link is not established
  if (linkEnforcer.blocked) {
    return <div style={{ width: "100%" }}>{linkEnforcer.render}</div>;
  }
  return (
    <Stack spacing={2} divider={<Divider flexItem />}>
      {
        // Upload file
      }
      <UploadTemplateFile
        file={uploadedFile}
        setFileId={setQueryId}
        setFile={(file?: File) => {
          setUploadedFile(file);
          setUploaded(false);
          setModelRunRecords(undefined);
          setSubmitted(false);
        }}
        onReset={clearAll}
      />
      {
        // Submit file
      }
      {uploadedFile !== undefined && (
        <SubmitTemplateFile
          file={uploadedFile}
          queryId={queryId ?? "NA"}
          newRecords={modelRunRecords}
          uploaded={uploaded}
          setUploaded={setUploaded}
          setNewRecords={setModelRunRecords}
        />
      )}
      {
        // Lodge records
      }
      {modelRunRecords !== undefined && (
        <LodgeJobs
          records={modelRunRecords}
          setSubmitted={setSubmitted}
          submitted={submitted}
          queryId={queryId ?? "NA"}
          // These are the actual controlled state in this step
          batchJobSessionId={batchJobSessionId}
          setBatchJobSessionId={setBatchJobSessionId}
        />
      )}
      {
        // Monitor the batch submission job
      }
      {batchJobSessionId !== undefined && (
        <MonitorBatchSubmissionComponent
          setBatchId={setBatchId}
          // These are the actual controlled state in this step
          batchJobSessionId={batchJobSessionId!}
        />
      )}
      {
        // Monitor the collection of jobs
      }
      {batchId !== undefined && <MonitorJobs batchId={batchId} />}
      {batchId !== undefined && (
        <RegenerateCSV
          downloaded={generateDownloaded}
          setDownloaded={setGenerateDownloaded}
          queryId={queryId ?? "NA"}
          batchId={batchId}
        />
      )}
    </Stack>
  );
});

export default LodgeTemplate;
