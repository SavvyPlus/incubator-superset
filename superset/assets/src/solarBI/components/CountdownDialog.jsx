import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import DialogActions from '@material-ui/core/DialogActions';

const propTypes = {
  open: PropTypes.bool.isRequired,
};

function CountdownDialog({ open }) {
  const [count, setCount] = useState(8);

  useEffect(() => {
    let interval = null;
    if (open) {
      if (count === 0) {
        window.location.href = '/solar/list';
      }
      interval = window.setInterval(() => {
        setCount(c => c - 1);
      }, 1000);
    } else if (!open && count !== 0) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [open, count]);

  const handleRedirect = () => {
    window.location.href = '/solar/list';
  };

  return (
    <div>
      <Dialog
        open={open}
        disableBackdropClick
        disableEscapeKeyDown
      // onClose={handleClose}
      >
        <DialogTitle id="alert-dialog-title">THANK YOU!</DialogTitle>
        <DialogContent>
          <DialogContentText id="countdown-dialog-description">
            We’ve send our pigeons to fetch your data, you will be re-directed to My Data
            in a few seconds, sit tight we will have it deliver to you in a little bit.
          </DialogContentText>
          <DialogContentText>
            You will be redirected to My Data page in <strong>{count}</strong> seconds
          </DialogContentText>
          <DialogActions>
            <Button onClick={handleRedirect} color="primary">
              Redirect Now
            </Button>
          </DialogActions>
        </DialogContent>
      </Dialog>
    </div>
  );
}

CountdownDialog.propTypes = propTypes;

export default CountdownDialog;
