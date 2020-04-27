import React, { useState } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import { StripeProvider, Elements } from 'react-stripe-elements';
import ChangeConfirm from './ChangeConfirm';
import AddCreditCard from './AddCreditCard';
import { changePlan } from '../actions/billingActions';

const useStyles = makeStyles(tm => ({
  button: {
    float: 'right',
    width: 255,
    height: 80,
    color: '#024067',
    borderColor: '#024067',
    borderRadius: 10,
    fontSize: '1.2em',
  },
  notUse: {
    margin: tm.spacing(1),
  },
}));

function Plan({ billing, changePlanConnect }) {
  const classes = useStyles();
  const [openCC, setOpenCC] = useState(false);
  const [openACC, setOpenACC] = useState(false);
  const [planId, setPlanId] = useState('00');

  const handleCloseCC = () => {
    setOpenCC(false);
  };

  const handleCloseACC = () => {
    setOpenACC(false);
  };

  const handlePlanClick = (id) => {
    setPlanId(id);
    if (billing.need_update_cc === true) {
      setOpenACC(true);
    } else {
      setOpenCC(true);
    }
  };


  return (
    <React.Fragment>
      <div className="tab-pane" id="plan">
        <h1 id="select-plan">Select Plan</h1>
        <div className="plan-option-pane">
          <div className="option-name"><i className="fas fa-list-ul" /><span>Free</span></div>
          <div className="option-description">You can have unlimited search but cannot request any dataset.</div>
          <div className="option-submit">
            <Button variant="outlined" color="primary" className={classes.button} onClick={() => handlePlanClick('00')} disabled={billing.plan_id === '00'}>
              {billing.plan_id === '00' ? 'Current' : 'Choose'}
            </Button>
          </div>
        </div>
        <div className="plan-option-pane">
          <div className="option-name"><i className="fas fa-play-circle" /><span>Starter</span></div>
          <div className="option-description">$19 You can have unlimited search plus 7 requested dataset.</div>
          <div className="option-submit">
            <Button variant="outlined" color="primary" className={classes.button} onClick={() => handlePlanClick('01')} disabled={billing.plan_id === '01'}>
              {billing.plan_id === '01' ? 'Current' : 'Choose'}
            </Button>
          </div>
        </div>
        <div className="plan-option-pane">
          <div className="option-name"><i className="fas fa-project-diagram" /><span>Medium</span></div>
          <div className="option-description">$29 You can have unlimited search plus 15 requested dataset.</div>
          <div className="option-submit">
            <Button variant="outlined" color="primary" className={classes.button} onClick={() => handlePlanClick('02')} disabled={billing.plan_id === '02'}>
              {billing.plan_id === '02' ? 'Current' : 'Choose'}
            </Button>
          </div>
        </div>
        <div className="plan-option-pane">
          <div className="option-name"><i className="fas fa-infinity" /><span>Advance</span></div>
          <div className="option-description">$49 You can have unlimited search plus 30 requested dataset.</div>
          <div className="option-submit">
            <Button variant="outlined" color="primary" className={classes.button} onClick={() => handlePlanClick('03')} disabled={billing.plan_id === '03'}>
              {billing.plan_id === '03' ? 'Current' : 'Choose'}
            </Button>
          </div>
        </div>
        <strong className="free-credits">Remaining Free Credit: ${(billing.balance * -1 / 100).toFixed(2)}</strong>
      </div>

      <StripeProvider apiKey="pk_test_2CT1LvA7viLp1j7yCHJ2MezU00xXxxnRdM">
        <Elements>
          <AddCreditCard
            planId={planId}
            updateCC="1"
            openACC={openACC}
            handleCloseACC={handleCloseACC}
            changePlan={changePlanConnect}
            billing={billing}
          />
        </Elements>
      </StripeProvider>

      <ChangeConfirm
        planId={planId}
        updateCC="0"
        openCC={openCC}
        handleCloseCC={handleCloseCC}
        changePlan={changePlanConnect}
        billing={billing}
      />
    </React.Fragment>
  );
}

Plan.propTypes = {
  billing: PropTypes.object.isRequired,
  changePlanConnect: PropTypes.func.isRequired,
};

function mapStateToProps({ billing }) {
  return {
    billing,
  };
}

export default connect(
  mapStateToProps,
  { changePlanConnect: changePlan },
)(Plan);
