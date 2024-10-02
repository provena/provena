import { useEffect, useState } from "react";
import { FieldProps } from "@rjsf/utils";
import { Button, Stack, TextField, Typography } from "@mui/material";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { deriveTitleDescription } from "../util";
import { AdapterMoment } from "@mui/x-date-pickers/AdapterMoment";
import moment from "moment";

export interface UnixTimestampFieldProps extends FieldProps<number> {}

export const UnixTimestampField = (props: UnixTimestampFieldProps) => {
  const [selectedDate, setSelectedDate] = useState<moment.Moment | null>(
    props.formData ? moment.unix(props.formData) : null
  );

  useEffect(() => {
    setSelectedDate(props.formData ? moment.unix(props.formData) : null);
  }, [props.formData]);

  // Get title and description
  const { title, description } = deriveTitleDescription(props);

  const handleDateChange = (date: moment.Moment | null) => {
    setSelectedDate(date);
    if (date && date.isValid()) {
      props.onChange(date.unix());
    } else {
      props.onChange(undefined);
    }
  };

  const handleSetNow = () => {
    const now = moment();
    setSelectedDate(now);
    props.onChange(now.unix());
  };

  return (
    <LocalizationProvider dateAdapter={AdapterMoment}>
      <Stack spacing={2}>
        <Typography variant="h6">{title}</Typography>
        {description && <Typography variant="body2">{description}</Typography>}
        <Stack direction="row" spacing={2}>
          <DateTimePicker
            label="Select Date and Time"
            value={selectedDate}
            onChange={handleDateChange}
            renderInput={(params) => <TextField {...params} fullWidth />}
          />
          <Button variant="contained" onClick={handleSetNow}>
            Set to Current Time
          </Button>
        </Stack>
      </Stack>
    </LocalizationProvider>
  );
};

export default UnixTimestampField;
