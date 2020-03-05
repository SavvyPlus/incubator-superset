import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';

const propTypes = {
  requests: PropTypes.number.isRequired,
};

const useStyles = makeStyles({
  remain: {
    float: 'right',
    position: 'absolute',
    right: 20,
    top: 10,
  },
  left: {
    fontSize: '0.9em',
  },
  block: {
    width: 70,
    height: 70,
    textAlign: 'center',
    backgroundColor: '#f2f2f2',
    paddingTop: 15,
    margin: 'auto',
    border: '1px solid #797979',
  },
  requestsText: {
    fontSize: '1.7em',
    fontWeight: 500,
  },
});

function RemainingRequests({ requests }) {
  const classes = useStyles();
  return (
    <div className={classes.remain}>
      <p className={classes.left}>Requests Left</p>
      <div className={classes.block}><span className={classes.requestsText}>{requests}</span></div>
    </div>
  );
}

RemainingRequests.propTypes = propTypes;

export default RemainingRequests;
