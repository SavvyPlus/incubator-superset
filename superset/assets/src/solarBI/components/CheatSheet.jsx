import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';

const propTypes = {
  open: PropTypes.bool.isRequired,
  toggleDrawer: PropTypes.func.isRequired,
};

const useStyles = makeStyles({
  csopen: {
    position: 'absolute',
    top: 0,
    width: 400,
    height: 680,
    transition: '0.5s',
    right: 0,
  },
  csclose: {
    position: 'absolute',
    top: 0,
    width: 450,
    height: 680,
    transition: '0.5s',
    right: -374,
  },
  btn: {
    top: '45%',
    zIndex: 300,
    position: 'absolute',
    transform: 'rotate(-90deg)',
    backgroundColor: '#0063B0',
    color: 'white',
    padding: 10,
    fontWeight: 500,
    border: '1px solid #0063B3',
    '&:focus': {
      outline: 0,
    },
  },
  cs: {
    height: '100%',
    background: 'white',
    marginLeft: 75,
    padding: 40,
    borderLeft: '0.5px solid',
  },
  explains: {
    margin: 40,
    color: '#757575',
  },
});

function CheatSheet({ open, toggleDrawer }) {
  const classes = useStyles();

  return (
    <div className={open ? classes.csopen : classes.csclose}>
      <button className={classes.btn} onClick={toggleDrawer}>Cheat Sheet</button>
      <div className={classes.cs}>
        <p className={classes.explains}>Explains coming soon</p>
      </div>
    </div>
  );
}

CheatSheet.propTypes = propTypes;

export default CheatSheet;
