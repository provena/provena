import { FormGroup, FormControlLabel, Checkbox } from "@mui/material";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Theme } from "@mui/material/styles";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        addAnnotationsCheckBox: {
            margin: theme.spacing(0),
        },
    })
);

const WorkflowTemplateAnnotationsOverride = (props: any) => {
    const classes = useStyles();
    return (
        <FormGroup className={classes.addAnnotationsCheckBox}>
            <FormControlLabel
                control={
                    <Checkbox
                        onChange={() => {
                            props.onChange(props.value === 1 ? 0 : 1);
                        }}
                        checked={props.value === 1 ? false : true}
                    />
                }
                label="Add Required or Optional Annotations"
            />
        </FormGroup>
    );
};

export default WorkflowTemplateAnnotationsOverride;
