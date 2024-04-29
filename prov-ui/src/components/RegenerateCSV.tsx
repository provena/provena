import { observer } from "mobx-react-lite";
import React from "react";

import { useQuery } from "@tanstack/react-query";

import { Button, Grid, CircularProgress } from "@mui/material";
import { generateCsvFromBatchId } from "../queries/ingest";

interface RegenerateCSVProps {
  batchId: string;
  downloaded: boolean;
  setDownloaded: (downloaded: boolean) => void;
  queryId: string;
}

const RegenerateCSV = observer((props: RegenerateCSVProps) => {
  /**
    Component: RegenerateCSV
    
    */
  const { isError, error, isSuccess, isFetching } = useQuery({
    queryKey: ["regenerate" + props.queryId],
    queryFn: () => generateCsvFromBatchId(props.batchId),
    enabled: props.downloaded,
  });

  const isDownloadedContent = (
    <Grid
      container
      xs={12}
      spacing={3}
      justifyContent="flex-start"
      alignItems="center"
    >
      <Grid item xs={12}>
        Your CSV template with updated job status entries has been downloaded.
      </Grid>
      <Grid item>
        <Button
          variant="outlined"
          color="warning"
          onClick={() => {
            props.setDownloaded(false);
          }}
        >
          Download again
        </Button>
      </Grid>
    </Grid>
  );

  const requiresDownloadContent = (
    <Grid
      container
      xs={12}
      justifyContent="flex-start"
      spacing={2}
      alignContent="center"
    >
      <Grid item>
        Click here to download an updated CSV template which includes an update
        to the job status headers:
      </Grid>
      <Grid item>
        <Button
          variant="outlined"
          color="success"
          onClick={() => {
            props.setDownloaded(true);
          }}
        >
          Click to download
        </Button>
      </Grid>
    </Grid>
  );

  return (
    <Grid item xs={12}>
      {isFetching ? (
        <CircularProgress></CircularProgress>
      ) : isError ? (
        <React.Fragment>
          An error occurred while requesting an updated CSV template, error
          message: {error}.
        </React.Fragment>
      ) : props.downloaded && isSuccess ? (
        isDownloadedContent
      ) : (
        requiresDownloadContent
      )}
    </Grid>
  );
});

export default RegenerateCSV;
