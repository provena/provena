// Data grid
import {
  Box,
  Button,
  Link,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { GridRenderCellParams, GridToolbarContainer } from "@mui/x-data-grid";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";
import {
  CopyableLinkedHandleComponent,
  RenderLongTextExpand,
  STATUS_COLOR_MAP,
  releaseStateStylePicker,
  timestampToLocalTime,
  useTypedLoadedItem,
} from "../";
import { JobStatus } from "../provena-interfaces/AsyncJobAPI";
import { ItemSubType } from "../provena-interfaces/RegistryAPI";

export const renderJobStatus = (params: GridRenderCellParams) => {
  // Catch the empty ID case
  if (params.value === "") {
    return <p></p>;
  }

  const status = params.value as JobStatus;
  var color = STATUS_COLOR_MAP.get(status);

  if (color === undefined) {
    color = "blue";
  }

  return <p style={{ color: color }}>{params.value}</p>;
};

export const renderHandleIdLink = (params: GridRenderCellParams) => {
  // Catch the empty ID case
  if (params.value === "") {
    return <p></p>;
  }

  // Render the link properly based on field value
  const link = "http://hdl.handle.net/" + params.value;

  return (
    <a href={link} target="outside">
      {params.value}
    </a>
  );
};

export const searchOnlyDataToolbar = () => {
  //Refer to https://mui.com/x/react-data-grid/filtering/ and
  //https://mui.com/x/react-data-grid/components/#toolbar
  return (
    <GridToolbarContainer>
      {
        //<GridToolbarQuickFilter />
      }
    </GridToolbarContainer>
  );
};

// For approvals history

export const renderHandleId = (params: GridRenderCellParams) => {
  if (params.value === "" || !params.value) return <p></p>;
  return <CopyableLinkedHandleComponent handleId={params.value} />;
};

export interface RenderCellTextExpand {
  params: GridRenderCellParams;
  // How many characters need to be left as "View less" text
  // undefined for showing the whole text, with no expand function
  initialCharNum?: number;
}

export const renderCellTextExpand = (props: RenderCellTextExpand) => {
  // For long Text render, can collapse text.
  if (props.params.value === "" || !props.params.value) return <p></p>;

  if (props.initialCharNum === undefined)
    return <Box>{props.params.value}</Box>;

  return (
    <Box>
      <RenderLongTextExpand
        text={props.params.value}
        initialCharNum={props.initialCharNum}
      />
    </Box>
  );
};

export const renderApprovalActionStatus = (params: GridRenderCellParams) => {
  // Render approval action status colours to data grid cells
  if (params.value === "" || !params.value) return <p></p>;

  const actionStateColour = releaseStateStylePicker(params.value).colour;
  const actionStateText = releaseStateStylePicker(params.value).text;

  return (
    <Typography sx={{ color: actionStateColour }}>{actionStateText}</Typography>
  );
};

interface RenderNameAndIdByIdProps {
  // params.value input should be item id
  params: GridRenderCellParams;
  subtype: ItemSubType;
}

const RenderNameAndIdById = (props: RenderNameAndIdByIdProps) => {
  // Render entity's display name and id sthrough it's id
  const loadedItem = useTypedLoadedItem({
    id: props.params.value,
    subtype: props.subtype,
  });

  if (loadedItem.error) {
    console.error(loadedItem.errorMessage);
    return <Box>Error: An Error Occurred While Fetching the Item.</Box>;
  }

  if (loadedItem.loading) {
    return <Box>Loading...</Box>;
  }

  if (!props.params.value)
    return (
      <Box padding={1}>
        <p></p>
      </Box>
    );

  return (
    <Box padding={1}>
      {loadedItem.item?.display_name}{" "}
      <span style={{ whiteSpace: "nowrap" }}>
        {/* Make sure things below are always in the same line */}
        {" ("}
        <CopyableLinkedHandleComponent handleId={props.params.value} />
        {")"}
      </span>
    </Box>
  );
};

export const renderNameAndIdById = (props: RenderNameAndIdByIdProps) => {
  // Use for cell render
  return <RenderNameAndIdById {...props} />;
};

export interface RenderCellButtonProps {
  // Button name text
  text: string;
  // Button link
  link: string;
  // Button disable
  disabled: boolean;
  // Button disabled tooltip text
  tooltipText?: string;
  // Button styles
  buttonVariant?: "contained" | "outlined";
  // Any other styles?
  className?: string;
}

const RenderCellButton = (input: RenderCellButtonProps) => {
  // Render button for data grid cell
  // Dedirect to input.Link

  const history = useHistory();

  return (
    <Tooltip title={(input.disabled && input.tooltipText) ?? ""}>
      <Box>
        <Button
          variant={input.buttonVariant}
          onClick={() => {
            history.push(input.link);
          }}
          disabled={input.disabled}
          className={input.className ?? undefined}
        >
          {input.text}
        </Button>
      </Box>
    </Tooltip>
  );
};

export const renderCellButton = (input: RenderCellButtonProps) => {
  // Use for cell render
  return <RenderCellButton {...input} />;
};

export const renderDatasetCombinedNameAndId = (
  params: GridRenderCellParams,
) => {
  // Render Combined dataset name and id for the cell

  return (
    <Box padding={1}>
      {!!params.value.display_name ? params.value.display_name : ""}{" "}
      {!!params.value.id && (
        <span style={{ whiteSpace: "nowrap" }}>
          {/* Make sure things below are always in the same line */}
          {" ("}
          <CopyableLinkedHandleComponent handleId={params.value.id} />
          {")"}
        </span>
      )}
    </Box>
  );
};
