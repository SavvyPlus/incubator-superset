import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

const useStyles = makeStyles(theme => ({
  formControl: {
    minWidth: 120,
    marginTop: 15,
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export default function ProjectListVersionSelect({
  version,
  setVersion,
  projectList,
}) {
  const classes = useStyles();

  const handleChange = event => {
    setVersion(event.target.value);
  };
  return (
    <FormControl variant="outlined" className={classes.formControl}>
      <Select value={version} onChange={handleChange}>
        {projectList.map(pl => (
          <MenuItem key={pl.version} value={pl.version}>
            {pl.note}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
