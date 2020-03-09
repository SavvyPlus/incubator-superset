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

function ChangeCreditCard({ stripe, openCCC, handleCloseCCC, changeCreditCard, billing }) {
  const classes = useStyles();
  const [showError, setShowError] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = (ev) => {
    ev.preventDefault();
    if (stripe) {
      stripe.createToken().then((payload) => {
        if (payload.error) {
          setErrorMsg(payload.error.message);
          setShowError(true);
        } else {
          changeCreditCard(payload.token.id).then(() => {
            // handleCloseCCC();
            window.location.reload();
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
      <Dialog open={openCCC} onClose={handleCloseCCC} aria-labelledby="form-dialog-title">
        <DialogTitle className={classes.title}>Change Credit Card</DialogTitle>
        <DialogContent>
          <DialogContentText className={classes.contentText}>
            Please input your new credit card details
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
          <Button onClick={handleCloseCCC} color="primary" className={classes.button}>
            Cancel
          </Button>
          {billing.change_cc === 'changing' || billing.change_cc === 'success' ?
            (<img className={classes.loading} alt="Loading..." src="/static/assets/images/loading.gif" />) :
            (<Button onClick={handleSubmit} color="primary" className={classes.button}>Submit</Button>)
          }
        </DialogActions>
      </Dialog>
    </div>
  );
}

ChangeCreditCard.propTypes = {
  billing: PropTypes.object.isRequired,
  openCCC: PropTypes.bool.isRequired,
  handleCloseCCC: PropTypes.func.isRequired,
  stripe: PropTypes.object.isRequired,
  changeCreditCard: PropTypes.func.isRequired,
};

export default injectStripe(ChangeCreditCard);
