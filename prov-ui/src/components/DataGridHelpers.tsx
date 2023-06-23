// Data grid
import {
    GridRenderCellParams,
    GridToolbarContainer,
    GridToolbarQuickFilter,
} from "@mui/x-data-grid";

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
