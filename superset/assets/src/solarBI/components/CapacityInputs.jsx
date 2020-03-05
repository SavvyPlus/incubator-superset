import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import TextField from '@material-ui/core/TextField';

const propTypes = {
  cap1: PropTypes.number,
  cap1Err: PropTypes.bool.isRequired,
  cap2: PropTypes.number,
  cap2Err: PropTypes.bool.isRequired,
  handleCap1Change: PropTypes.func.isRequired,
  handleCap2Change: PropTypes.func.isRequired,
};

const useStyles = makeStyles({
  inputs: {
    width: 180,
    marginBottom: 20,
  },
  id: {
    marginTop: 10,
    display: 'inline-block',
    fontWeight: 500,
    marginRight: 10,
    width: 10,
  },
  textInput: {
    width: 150,
  },
  input: {
    padding: 10,
    fontWeight: 500,
  },
  title: {
    width: 150,
    margin: '10 auto',
    fontFamily: 'Montserrat',
  },
});

function CapacityInputs({ cap1, cap1Err, cap2, cap2Err, handleCap1Change, handleCap2Change }) {
  const classes = useStyles();

  return (
    <div>
      <h5 className={classes.title}>System Capacity</h5>
      <div className={classes.inputs}>
        <span className={classes.id}>1</span>
        <TextField
          className={classes.textInput}
          InputProps={{
            classes: { input: classes.input },
          }}
          type="number"
          error={cap1Err}
          variant="outlined"
          value={cap1}
          onChange={handleCap1Change}
          helperText={cap1Err ? 'Please provide a valid number' : null}
        />
      </div>
      <div className={classes.inputs}>
        <span className={classes.id}>2</span>
        <TextField
          className={classes.textInput}
          InputProps={{
            classes: { input: classes.input },
          }}
          type="number"
          error={cap2Err}
          variant="outlined"
          value={cap2}
          onChange={handleCap2Change}
          helperText={cap2Err ? 'Please provide a valid number' : null}
        />
      </div>
    </div>
  );
}

CapacityInputs.propTypes = propTypes;

export default CapacityInputs;
