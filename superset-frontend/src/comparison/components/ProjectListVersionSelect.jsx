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

export default function ProjectListVersionSelect({ version, setVersion }) {
  const classes = useStyles();

  const handleChange = event => {
    setVersion(event.target.value);
  };
  return (
    <FormControl variant="outlined" className={classes.formControl}>
      <Select value={version} onChange={handleChange}>
        <MenuItem value="1">1</MenuItem>
        <MenuItem value="2">2</MenuItem>
        <MenuItem value="3">3</MenuItem>
        <MenuItem value="4">4</MenuItem>
      </Select>
    </FormControl>
  );
}
