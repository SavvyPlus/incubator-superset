import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import Radio from '@material-ui/core/Radio';
import RadioGroup from '@material-ui/core/RadioGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormControl from '@material-ui/core/FormControl';

const propTypes = {
  unit: PropTypes.string.isRequired,
  handleUnitChange: PropTypes.func.isRequired,
};

const useStyles = makeStyles({
  unit: {
    flexDirection: 'initial',
  },
});

function UnitSelection({ unit, handleUnitChange }) {
  const classes = useStyles();

  return (
    <div>
      <FormControl component="fieldset">
        <RadioGroup aria-label="unit" className={classes.unit} name="unit" value={unit} onChange={handleUnitChange}>
          <FormControlLabel value="MWh" control={<Radio />} label="MWh" />
          <FormControlLabel value="KWh" control={<Radio />} label="KWh" />
        </RadioGroup>
      </FormControl>
    </div>
  );
}

UnitSelection.propTypes = propTypes;

export default UnitSelection;
