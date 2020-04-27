import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import IconButton from '@material-ui/core/IconButton';
import AddIcon from '@material-ui/icons/Add';
import DeleteIcon from '@material-ui/icons/Delete';
import TextField from '@material-ui/core/TextField';

const propTypes = {
  cap1: PropTypes.string,
  cap1Err: PropTypes.bool.isRequired,
  cap2: PropTypes.string,
  cap3: PropTypes.string,
  cap2Err: PropTypes.bool.isRequired,
  cap3Err: PropTypes.bool.isRequired,
  showCap2: PropTypes.bool.isRequired,
  showCap3: PropTypes.bool.isRequired,
  handleCap1Change: PropTypes.func.isRequired,
  handleCap2Change: PropTypes.func.isRequired,
  handleCap3Change: PropTypes.func.isRequired,
  handleCapDelete: PropTypes.func.isRequired,
  handleCapAdd: PropTypes.func.isRequired,
};

const useStyles = makeStyles({
  icon: {
    marginTop: -5,
    padding: 5,
  },
  inputs: {
    width: 230,
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
    width: 120,
    marginRight: 10,
  },
  input: {
    padding: 10,
    fontWeight: 500,
  },
  title: {
    width: 150,
    margin: '10 auto',
    fontFamily: 'Open Sans, sans-serif',
  },
  helperText: {
    width: 130,
  },
});

function CapacityInputs({
  cap1, cap1Err, cap2, showCap2, cap2Err, cap3, showCap3,
  cap3Err, handleCap1Change, handleCap2Change, handleCap3Change,
  handleCapDelete, handleCapAdd,
}) {
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
          FormHelperTextProps={{
            classes: { root: classes.helperText },
          }}
          type="number"
          error={cap1Err}
          variant="outlined"
          value={cap1}
          onChange={handleCap1Change}
          helperText={cap1Err ? 'Please provide an interger from 1 to 5' : null}
        />
        {!showCap2 && (
          <IconButton onClick={() => handleCapAdd(2)} className={classes.icon} aria-label="add">
            <AddIcon />
          </IconButton>
        )}
      </div>
      {showCap2 && (
        <div className={classes.inputs}>
          <span className={classes.id}>2</span>
          <TextField
            className={classes.textInput}
            InputProps={{
              classes: { input: classes.input },
            }}
            FormHelperTextProps={{
              classes: { root: classes.helperText },
            }}
            type="number"
            error={cap2Err}
            variant="outlined"
            value={cap2}
            onChange={handleCap2Change}
            helperText={cap2Err ? 'Please provide an interger from 1 to 5' : null}
          />
          {!showCap3 && (
            <React.Fragment>
              <IconButton onClick={() => handleCapAdd(3)} className={classes.icon} aria-label="add">
                <AddIcon />
              </IconButton>
              <IconButton onClick={() => handleCapDelete(2)} className={classes.icon} aria-label="delete">
                <DeleteIcon />
              </IconButton>
            </React.Fragment>
          )}
        </div>
      )}
      {showCap3 && (
        <div className={classes.inputs}>
          <span className={classes.id}>3</span>
          <TextField
            className={classes.textInput}
            InputProps={{
              classes: { input: classes.input },
            }}
            FormHelperTextProps={{
              classes: { root: classes.helperText },
            }}
            type="number"
            error={cap3Err}
            variant="outlined"
            value={cap3}
            onChange={handleCap3Change}
            helperText={cap3Err ? 'Please provide an interger from 1 to 5' : null}
          />
          <IconButton onClick={() => handleCapDelete(3)} className={classes.icon} aria-label="delete">
            <DeleteIcon />
          </IconButton>
        </div>
      )}
    </div>
  );
}

CapacityInputs.propTypes = propTypes;

export default CapacityInputs;
