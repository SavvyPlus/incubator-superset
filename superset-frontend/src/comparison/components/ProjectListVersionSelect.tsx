import React from 'react';
import { makeStyles, Theme } from '@material-ui/core/styles';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

type ProjectListVersion = {
  version: number;
  note: string;
};

interface ProjectListVersionProps {
  version: number;
  setVersion: (value: number) => void;
  projectList: ProjectListVersion[];
}

const useStyles = makeStyles((theme: Theme) => ({
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
}: ProjectListVersionProps) {
  const classes = useStyles();

  const handleChange = (event: React.ChangeEvent<{ value: number }>) => {
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
