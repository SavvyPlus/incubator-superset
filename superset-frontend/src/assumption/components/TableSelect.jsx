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

export default function TableSelect({ table, setTable }) {
  const classes = useStyles();

  const handleChange = event => {
    setTable(event.target.value);
  };
  return (
    <>
      <h3 className="mt-50">Step 2: Select Table</h3>
      <FormControl variant="outlined" className={classes.formControl}>
        <Select value={table} onChange={handleChange}>
          <MenuItem value="RooftopSolarHistory">Rooftop Solar History</MenuItem>
          <MenuItem value="RooftopSolarForecast">
            Rooftop Solar Forecast
          </MenuItem>
          <MenuItem value="RenewableProportion">Renewable Proportion</MenuItem>
          <MenuItem value="DemandGrowth">Demand Growth</MenuItem>
          <MenuItem value="BehindTheMeterBattery">
            Behind The Meter Battery
          </MenuItem>
          <MenuItem value="ProjectProxy">Project Proxy</MenuItem>
          <MenuItem value="MPCCPT">MPC CPT</MenuItem>
          <MenuItem value="GasPriceEscalation">Gas Price Escalation</MenuItem>
          <MenuItem value="StrategicBehaviour">Strategic Behaviour</MenuItem>
          <MenuItem value="Retirement">Retirement</MenuItem>
          <MenuItem value="ProjectList">Project List</MenuItem>
        </Select>
      </FormControl>
    </>
  );
}
