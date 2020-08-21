import React from 'react';
import { makeStyles, Theme } from '@material-ui/core/styles';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

type Scenario = {
  name: string;
  scenario: string;
};

interface ScenarioSelectProps {
  scenario: Scenario;
  setScenario: (value: string) => void;
  scenarioList: Scenario[];
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

export default function ScenarioSelect({
  scenario,
  setScenario,
  scenarioList,
}: ScenarioSelectProps) {
  const classes = useStyles();

  const handleChange = (event: React.ChangeEvent<{ value: string }>) => {
    setScenario(event.target.value);
  };
  return (
    <FormControl variant="outlined" className={classes.formControl}>
      <Select value={scenario} onChange={handleChange}>
        {scenarioList.map(sl => (
          <MenuItem key={sl.name} value={sl.name}>
            {sl.scenario}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
