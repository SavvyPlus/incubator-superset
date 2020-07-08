import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

const useStyles = makeStyles(theme => ({
  formControl: {
    minWidth: 120,
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export default function UpsertSelect({ upsert, setUpsert }) {
  const classes = useStyles();

  const handleChange = event => {
    setUpsert(event.target.value);
  };
  return (
    <>
      <h3 className="mt-50">Step 1: Select Upload or Modify</h3>
      <FormControl variant="outlined" className={classes.formControl}>
        <Select value={upsert} onChange={handleChange}>
          <MenuItem value="upload">Upload</MenuItem>
          <MenuItem value="modify">Modify</MenuItem>
        </Select>
      </FormControl>
    </>
  );
}
