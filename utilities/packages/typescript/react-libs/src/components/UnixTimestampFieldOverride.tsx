import { AdapterMoment } from "@mui/x-date-pickers/AdapterMoment";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { Button, Stack, TextField, Typography } from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { FieldProps } from "@rjsf/utils";
import moment from "moment";
import { useEffect, useState } from "react";
import { deriveTitleDescription } from "../util";

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
    <Stack spacing={2}>
      <LocalizationProvider dateAdapter={AdapterMoment}>
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
      </LocalizationProvider>
    </Stack>
  );
};

export default UnixTimestampField;
