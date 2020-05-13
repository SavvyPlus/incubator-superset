import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

const useStyles = makeStyles(theme => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 120,
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export default function RegionSelect() {
  const classes = useStyles();
  const [region, setRegion] = React.useState('nem');

  const handleChange = event => {
    setRegion(event.target.value);
  };
  return (
    <FormControl variant="outlined" className={classes.formControl}>
      <Select value={region} onChange={handleChange}>
        <MenuItem value="nem">NEM</MenuItem>
        <MenuItem value="nsw">New South Wales</MenuItem>
        <MenuItem value="qld">Queensland</MenuItem>
        <MenuItem value="sa">South Australia</MenuItem>
        <MenuItem value="tas">Tasmania</MenuItem>
        <MenuItem value="vic">Victoria</MenuItem>
      </Select>
    </FormControl>
  );
}
