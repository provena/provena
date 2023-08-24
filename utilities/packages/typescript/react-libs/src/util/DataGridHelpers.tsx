// Data grid
import { GridRenderCellParams, GridToolbarContainer } from "@mui/x-data-grid";
import { JobStatus } from "../shared-interfaces/AsyncJobAPI";
import { STATUS_COLOR_MAP } from "../";

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
