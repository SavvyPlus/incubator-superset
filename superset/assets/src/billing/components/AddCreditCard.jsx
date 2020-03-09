/* eslint-disable jsx-a11y/label-has-for */
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import { makeStyles } from '@material-ui/core/styles';
import {
  injectStripe,
  CardNumberElement,
  CardExpiryElement,
  CardCVCElement,
} from 'react-stripe-elements';

const useStyles = makeStyles(theme => ({
  button: {
    fontSize: '1.2em',
  },
  contentText: {
    fontSize: '1.2em',
  },
  loading: {
    width: 40,
    margin: 0,
  },
  title: {
    '& h2': {
      fontSize: '1.6em',
    },
  },
  notUse: {
    margin: theme.spacing(1),
  },
}));

const createOptions = () => ({
  style: {
    base: {
      fontSize: '18px',
      color: '#424770',
      letterSpacing: '0.025em',
      fontFamily: 'Source Code Pro, monospace',
      '::placeholder': {
        color: '#aab7c4',
      },
      // padding: 0,
    },
    invalid: {
      color: '#dc3545',
    },
  },
});

function AddCreditCard({ planId, updateCC, stripe, openACC, handleCloseACC, changePlan, billing }) {
  const classes = useStyles();
  const [showError, setShowError] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = (ev) => {
    ev.preventDefault();
    if (stripe) {
      stripe.createToken().then((payload) => {
        if (payload.error) {
          if (payload.error.code === 'card_declined') {
            setErrorMsg('Your card was declined.');
            setShowError(true);
          } else {
            setErrorMsg(payload.error.message);
            setShowError(true);
          }

        } else {
          changePlan(planId, updateCC, payload).then(() => {
            handleCloseACC();
          });
        }

      });
    } else {
      // eslint-disable-next-line no-alert
      alert("Stripe.js hasn't loaded yet.");
    }
  };

  const closeErrorMsg = () => {
    setErrorMsg('');
    setShowError(false);
  };

  return (
    <div>
      <Dialog open={openACC} onClose={handleCloseACC} aria-labelledby="form-dialog-title">
        <DialogTitle className={classes.title}>Add Credit Card</DialogTitle>
        <DialogContent>
          <DialogContentText className={classes.contentText}>
            Seems like you have not added a credit card yet.
          </DialogContentText>
          <div>
            {showError && <div className="error-message">
              {errorMsg}
              <button onClick={closeErrorMsg}><span>&times;</span></button>
            </div>}
            <label className="card-elm-label">
              Card number
              <CardNumberElement {...createOptions()} />
            </label>
            <label className="card-elm-label">
              Expiration date
              <CardExpiryElement {...createOptions()} />
            </label>
            <label className="card-elm-label">
              CVC
              <CardCVCElement {...createOptions()} />
            </label>
          </div>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseACC} color="primary" className={classes.button}>
            Cancel
          </Button>
          {billing.plan_change === 'changing' ?
            (<img className={classes.loading} alt="Loading..." src="/static/assets/images/loading.gif" />) :
            (<Button onClick={handleSubmit} color="primary" className={classes.button}>Submit</Button>)
          }
        </DialogActions>
      </Dialog>
    </div>
  );
}

AddCreditCard.propTypes = {
  billing: PropTypes.object.isRequired,
  planId: PropTypes.string.isRequired,
  openACC: PropTypes.bool.isRequired,
  handleCloseACC: PropTypes.func.isRequired,
  changePlan: PropTypes.func.isRequired,
  updateCC: PropTypes.string.isRequired,
  stripe: PropTypes.object.isRequired,
};

export default injectStripe(AddCreditCard);
