import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import Stepper from '@material-ui/core/Stepper';
import Step from '@material-ui/core/Step';
import StepLabel from '@material-ui/core/StepLabel';

const propTypes = {
  activeStep: PropTypes.number.isRequired,
  classes: PropTypes.object,
};

const useStyles = makeStyles({
  stepLabel: {
    '& svg': {
      fontSize: 25,
    },
    '& svg text': {
      fontSize: 15,
      fontFamily: 'Open Sans, sans-serif',
    },
    '& span': {
      fontSize: 15,
      fontFamily: 'Open Sans, sans-serif',
    },
  },
  stepper: {
    background: 'transparent',
  },
});


function SolarStepper({ activeStep }) {
  const classes = useStyles();
  return (
    <Stepper className={classes.stepper} activeStep={activeStep} alternativeLabel>
      {['Search', 'Quick Result', 'Advance'].map(label => (
        <Step key={label}>
          <StepLabel className={classes.stepLabel}>{label}</StepLabel>
        </Step>
      ))}
    </Stepper>
  );
}

SolarStepper.propTypes = propTypes;

export default SolarStepper;
