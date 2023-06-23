import { FormGroup, FormControlLabel, Checkbox } from "@mui/material";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Theme } from "@mui/material/styles";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        addDatasetTemplateCheckBox: {
            margin: 0,
        },
    })
);

const WorkflowDefinitionAutomationScheduleOverride = (props: any) => {
    const classes = useStyles();
    return (
        <FormGroup className={classes.addDatasetTemplateCheckBox}>
            <FormControlLabel
                control={
                    <Checkbox
                        onChange={() => {
                            props.onChange(props.value === 1 ? 0 : 1);
                        }}
                        checked={props.value === 1 ? false : true}
                    />
                }
                label="Add Automation Schedule"
            />
        </FormGroup>
    );
};

export default WorkflowDefinitionAutomationScheduleOverride;
