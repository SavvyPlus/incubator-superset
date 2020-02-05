/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import classNames from 'classnames';
import { createMuiTheme } from '@material-ui/core/styles';
import { withStyles, ThemeProvider } from '@material-ui/styles';
import Slide from '@material-ui/core/Slide';
import Button from '@material-ui/core/Button';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Dialog from '@material-ui/core/Dialog';
import Typography from '@material-ui/core/Typography';
import IconButton from '@material-ui/core/IconButton';
import Popover from '@material-ui/core/Popover';
import HelpIcon from '@material-ui/icons/Help';
import DialogContent from '@material-ui/core/DialogContent';
import Chip from '@material-ui/core/Chip';
import Radio from '@material-ui/core/Radio';
import RadioGroup from '@material-ui/core/RadioGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormControl from '@material-ui/core/FormControl';
import FormLabel from '@material-ui/core/FormLabel';
// import InputAdornment from '@material-ui/core/InputAdornment';
import Container from '@material-ui/core/Container';
import DateFnsUtils from '@date-io/date-fns';
import { MuiPickersUtilsProvider, KeyboardDatePicker } from '@material-ui/pickers';
import SolarStepper from './SolarStepper';
import { requestSolarData, startTrial } from '../actions/solarActions';

const propTypes = {
  address: PropTypes.string.isRequired,
  classes: PropTypes.object.isRequired,
  solarBI: PropTypes.object,
  open: PropTypes.bool.isRequired,
  onHide: PropTypes.func.isRequired,
  requestSolarData: PropTypes.func.isRequired,
  startTrial: PropTypes.func.isRequired,
  solar_new: PropTypes.bool.isRequired,
};

const theme = createMuiTheme({
  typography: {
    useNextVariants: true,
  },
  palette: {
    primary: {
      main: '#0063B0',
    },
    secondary: {
      main: '#DBD800',
    },
  },
});


const styles = tm => ({
  addressText: {
    fontFamily: 'Montserrat',
    fontSize: 21,
    textAlign: 'center',
    color: '024067',
    fontWeight: 'normal',
    marginTop: 25,
  },
  backdrop: {
    backgroundColor: 'transparent',
  },
  border: {
    border: '1px solid #0063B0',
    borderRadius: 12,
    width: '55%',
    margin: '140 auto 10px',
  },
  button: {
    margin: '10 0',
    height: 40,
    padding: '0 16px',
    minWidth: 115,
    borderRadius: 60,
    color: 'white',
    backgroundColor: '#0063B0',
    border: 'none',
    fontSize: 16,
    fontFamily: 'Montserrat, sans-serif',
    fontWeight: 'bold',
    '&:hover': {
      color: 'white',
      backgroundColor: '#034980',
    },
    '&:disabled': {
      backgroundColor: 'lightgray',
    },
  },
  buttons: {
    width: '80%',
    marginLeft: '50',
    display: 'inline-block',
  },
  requestBtn: {
    float: 'right',
  },
  contentHr: {
    display: 'block',
    width: '95%',
    height: 1,
    border: 0,
    borderTop: '1px solid #AFDEDF',
    margin: '2em auto 0',
    padding: 0,
  },
  costOutput: {
    fontFamily: 'Montserrat',
    fontSize: '16px',
    fontWeight: 500,
    backgroundColor: '#EEEFF0',
    borderRadius: 12,
    lineHeight: '18px',
    marginTop: '25px',
    marginLeft: '30px',
    marginBottom: '40px',
    '& fieldset': {
      borderRadius: 12,
    },
  },
  dates: {
    display: 'flex',
  },
  dateLabel: {
    color: '#0063B0',
    display: 'block',
    marginBottom: 5,
  },
  dateWrapper: {
    width: 220,
    textAlign: 'center',
    marginLeft: 20,
  },
  dialog: {
    padding: 10,
    fontFamily: 'Montserrat',
    fontWeight: 'bold',
    marginLeft: '15em',
    backgroundColor: '#f5f5f5',
    ['@media (max-width:68em)']: { // eslint-disable-line no-useless-computed-key
      marginLeft: '4em',
    },
  },
  dollar: {
    '& p': {
      fontSize: 16,
    },
  },
  endText: {
    marginLeft: '15px',
    '& fieldset': {
      borderRadius: 12,
    },
  },
  exportCard: {
    margin: '40px auto',
    width: '70%',
    // height: 680,
  },
  lengthLabel: {
    fontSize: '1.3rem',
    color: '#0063B0',
    width: '10%',
    float: 'left',
    borderBottom: 'none',
    marginLeft: '15px',
    marginRight: '30px',
    marginTop: '45px',
  },
  formControl: {
    marginBottom: '5px',
    width: '90%',
    display: 'inline-block',
    margin: theme.spacing(2),
    '& svg': {
      fontSize: '1.2em',
    },
  },
  formControlLabel: {
    fontSize: '1rem',
    color: '#0063B0',
    fontFamily: 'Montserrat',
    fontWeight: 500,
  },
  head: {
    textAlign: 'center',
    height: 50,
    background: 'linear-gradient(.25turn, #10998C, #09809D, #0063B0)',
    backgroundColor: 'white',
    marginTop: -10,
    marginLeft: -10,
    width: '105%',
    color: 'white',
    paddingTop: 15,
  },
  helperText: {
    fontSize: '0.9em',
  },
  iconButton: {
    padding: '5 12',
    height: 40,
    marginLeft: 20,
    marginTop: 15,
  },
  labelFocused: {
    color: '#0063B0 !important',
  },
  loading: {
    width: 60,
    margin: 0,
    float: 'right',
  },
  resolutionLabel: {
    fontSize: '1.3rem',
    color: '#0063B0',
    width: '10%',
    float: 'left',
    borderBottom: 'none',
    marginTop: '35px',
    marginRight: '45px',
  },
  remainCount: {
    float: 'right',
  },
  // costLabel: {
  //   fontSize: '1.3rem',
  //   color: '#0063B0',
  //   width: '10%',
  //   float: 'left',
  //   borderBottom: 'none',
  //   marginTop: '35px',
  //   marginLeft: '15px',
  // },
  startText: {
    marginLeft: '10px',
    '& fieldset': {
      borderRadius: 12,
    },
  },
  title: {
    color: '#0063B0',
    fontSize: '1.6em',
    textAlign: 'center',
    paddingBottom: 0,
  },
  titleHr: {
    display: 'block',
    width: 159,
    height: 1,
    border: 0,
    borderTop: '1px solid #AFDEDF',
    margin: '1em auto 2em',
    padding: 0,
  },
  textLabel: {
    fontSize: '16px',
  },
  textInput: {
    fontFamily: 'Montserrat',
    fontSize: '16px',
    fontWeight: 500,
    // backgroundColor: '#EEEFF0',
    borderRadius: 12,
    lineHeight: '18px',
    textAlign: 'center',
  },
  trialLink: {
    marginLeft: 20,
    color: '#0063B0',
  },
  typeGroup: {
    flexDirection: 'row',
    width: '70%',
    float: 'left',
  },
  typeLabel: {
    fontSize: '1.3rem',
    color: '#0063B0',
    width: '10%',
    float: 'left',
    borderBottom: 'none',
    marginTop: '35px',
    marginRight: '45px',
  },
  typography: {
    margin: theme.spacing(2),
    fontSize: 15,
    width: 300,
  },
  resolutionGroup: {
    flexDirection: 'row',
    width: '80%',
    float: 'left',
  },
  notUse: {
    margin: tm.spacing(1),
  },
});

const Transition = React.forwardRef(function Transition(props, ref) {
  return <Slide direction="left" ref={ref} {...props} />;
});

class ExportModal extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      anchorEl: null,
      // type: 'dni',
      pickerStart: new Date('2007-01-01T00:00:00'),
      pickerEnd: new Date('2019-07-01T00:00:00'),
      startDate: '2007-01-01',
      endDate: '2019-07-01',
      resolution: 'hourly',
      cost: (16).toFixed(2),
    };

    // this.handleTypeChange = this.handleTypeChange.bind(this);
    this.handleStartDateChange = this.handleStartDateChange.bind(this);
    this.handleEndDateChange = this.handleEndDateChange.bind(this);
    this.handleResolutionChange = this.handleResolutionChange.bind(this);
    this.handleRequestData = this.handleRequestData.bind(this);
    this.handleQuestionClick = this.handleQuestionClick.bind(this);
    this.handleQuestionClose = this.handleQuestionClose.bind(this);
    this.handleTrialClick = this.handleTrialClick.bind(this);
    // this.calculateCost = this.calculateCost.bind(this);
    // this.dateDiff = this.dateDiff.bind(this);
    this.onUnload = this.onUnload.bind(this);
  }

  componentDidMount() {
    window.addEventListener('beforeunload', this.onUnload);
  }

  componentWillUnmount() {
    window.removeEventListener('beforeunload', this.onUnload);
  }

  onUnload(event) { // the method that will be used for both add and remove event
    if (!(this.props.solarBI.requestStatus === 'success' ||
      this.props.solarBI.saveStatus === 'success' ||
      this.props.solar_new === false)) {
      // eslint-disable-next-line no-param-reassign
      event.returnValue = 'This will go back to search page, are you sure?';
    }
  }


  // calculateCost() {
  //   const timeCost = {
  //     years: 5,
  //     months: 0.42,
  //     days: 0.01,
  //   };
  //   const gran = {
  //     monthly: 5,
  //     weekly: 7.5,
  //     daily: 9,
  //     hourly: 11,
  //   };
  //   const type = {
  //     dni: 0,
  //     ghi: 0,
  //     both: 0,
  //   };
  //   const dt1 = new Date(this.state.startDate);
  //   const dt2 = new Date(this.state.endDate);
  //   const diff = this.dateDiff(dt1, dt2);
  //   let result = diff.days * timeCost.days + diff.months * timeCost.months +
  //     diff.years * timeCost.years;
  //   let granularity;
  //   switch (this.state.resolution) {
  //     case 'hourly':
  //       granularity = gran.hourly;
  //       break;
  //     case 'daily':
  //       granularity = gran.daily;
  //       break;
  //     case 'weekly':
  //       granularity = gran.weekly;
  //       break;
  //     case 'monthly':
  //       granularity = gran.monthly;
  //       break;
  //     default:
  //       granularity = 0;
  //   }
  //   let t;
  //   switch (this.state.type) {
  //     case 'dni':
  //       t = type.dni;
  //       break;
  //     case 'ghi':
  //       t = type.ghi;
  //       break;
  //     case 'both':
  //       t = type.both;
  //       break;
  //     default:
  //       t = 0;
  //   }
  //   result = result + granularity + t;
  //   result = result.toFixed(2);
  //   // console.log(result)
  //   this.setState({ cost: result });
  // }

  // dateDiff(dt1, dt2) {
  //   const ret = { days: 0, months: 0, years: 0 };
  //   if (dt1 === dt2) return ret;
  //   if (dt1 > dt2) {
  //     const dtmp = dt2;
  //     // eslint-disable-next-line no-param-reassign
  //     dt2 = dt1;
  //     // eslint-disable-next-line no-param-reassign
  //     dt1 = dtmp;
  //   }

  //   /*
  //    * First get the number of full years
  //    */

  //   const year1 = dt1.getFullYear();
  //   const year2 = dt2.getFullYear();

  //   const month1 = dt1.getMonth();
  //   const month2 = dt2.getMonth();

  //   const day1 = dt1.getDate();
  //   const day2 = dt2.getDate();

  //   /*
  //    * Set initial values bearing in mind the months or days may be negative
  //    */
  //   ret.years = year2 - year1;
  //   ret.months = month2 - month1;
  //   ret.days = day2 - day1;

  //   /*
  //    * Now we deal with the negatives
  //    */

  //   /*
  //    * First if the day difference is negative
  //    * eg dt2 = 13 oct, dt1 = 25 sept
  //    */
  //   if (ret.days < 0) {
  //     /*
  //      * Use temporary dates to get the number of days remaining in the month
  //      */
  //     const dtmp1 = new Date(dt1.getFullYear(), dt1.getMonth() + 1, 1, 0, 0, -1);

  //     const numDays = dtmp1.getDate();

  //     ret.months -= 1;
  //     ret.days += numDays;

  //   }

  //   /*
  //    * Now if the month difference is negative
  //    */
  //   if (ret.months < 0) {
  //     ret.months += 12;
  //     ret.years -= 1;
  //   }

  //   return ret;
  // }

  // handleTypeChange(event) {
  //   this.setState({ type: event.target.value });
  // }

  // handleStartDateChange(event) {
  //   this.setState({ startDate: event.target.value });
  // }

  handleStartDateChange(date) {
    this.setState({ pickerStart: date });
    try {
      const tzoffset = (new Date()).getTimezoneOffset() * 60000;
      this.setState({
        startDate: new Date(Date.parse(date) - tzoffset).toISOString().slice(0, 10),
      });
    } catch (e) {
      this.setState({ startDate: '' });
    }
  }

  // handleEndDateChange(event) {
  //   this.setState({ endDate: event.target.value });
  // }
  handleEndDateChange(date) {
    this.setState({ pickerEnd: date });
    try {
      const tzoffset = (new Date()).getTimezoneOffset() * 60000;
      this.setState({
        endDate: new Date(Date.parse(date) - tzoffset).toISOString().slice(0, 10),
      });
    } catch (e) {
      this.setState({ endDate: '' });
    }
  }

  handleResolutionChange(event) {
    this.setState({ resolution: event.target.value });

  }

  handleQuestionClick(event) {
    this.setState({ anchorEl: event.currentTarget });
  }

  handleQuestionClose() {
    this.setState({ anchorEl: null });
  }

  handleTrialClick() {
    this.props.startTrial();
  }

  handleRequestData() {
    const sDate = new Date(this.state.startDate);
    const eDate = new Date(this.state.endDate);
    if (this.state.startDate === '') {
      alert('Please provide a valid start date!'); // eslint-disable-line no-alert
    } else if (this.state.endDate === '') {
      alert('Please provide a valid end date!'); // eslint-disable-line no-alert
    } else if (sDate > eDate) {
      alert('Start date cannot be later than end date!'); // eslint-disable-line no-alert
    } else if (new Date(sDate) < new Date('1990-01-01') ||
      new Date(eDate) > new Date('2019-07-31')) {
      alert('Available date: 01/01/1990 ~ 31/07/2019.'); // eslint-disable-line no-alert
    } else {
      const queryData = {
        lat: this.props.solarBI.queryResponse.data.lat.toFixed(7) + '',
        lng: this.props.solarBI.queryResponse.data.lng.toFixed(7) + '',
        startDate: this.state.startDate,
        endDate: this.state.endDate,
        // type: this.state.type,
        resolution: this.state.resolution,
        datasource_id: this.props.solarBI.queryResponse.form_data.datasource_id,
        datasource_type: this.props.solarBI.queryResponse.form_data.datasource_type,
        viz_type: this.props.solarBI.queryResponse.form_data.viz_type,
        radius: this.props.solarBI.queryResponse.radius,
        spatial_address: { ...this.props.solarBI.queryResponse.form_data.spatial_address },
        address_name: this.props.address.slice(0, -11),
      };
      // this.props.onHide();
      this.props.requestSolarData(queryData)
        .then((json) => {
          if (json.type === 'REQEUST_SOLAR_DATA_SUCCEEDED') {
            window.location = '/solar/list';
          }
        });
    }
  }

  render() {
    const { classes, open, onHide, solarBI } = this.props;
    // const { startDate, endDate, anchorEl, pickerStart, pickerEnd } = this.state;
    const { anchorEl, pickerStart, pickerEnd } = this.state;
    let remainCount = null;
    if (solarBI.can_trial && solarBI.start_trial === 'starting') {
      remainCount = <img style={{ width: 30, marginLeft: 20 }} alt="Loading..." src="/static/assets/images/loading.gif" />;
    } else if (solarBI.can_trial && solarBI.start_trial !== 'starting') {
      remainCount = (<a
        onClick={this.handleTrialClick}
        className={classes.trialLink}
      >
        Start trial
      </a>);
    }

    const openAnchor = Boolean(anchorEl);

    return (
      <div>
        <ThemeProvider theme={theme}>
          <Dialog
            classes={{ paper: classes.dialog }}
            fullScreen
            fullWidth
            open={open || solarBI.sending}
            onClose={onHide}
            TransitionComponent={Transition}
            keepMounted
            BackdropProps={{
              classes: {
                root: classes.backdrop,
              },
            }}
          >
            <div style={{ padding: 0, width: 800, margin: 'auto' }}>
              <SolarStepper activeStep={2} />
            </div>
            <DialogContent>
              <Card className={classes.exportCard}>
                <CardContent>
                  <div>
                    {solarBI.remain_days >= 0 && solarBI.plan_id !== 1 && <Chip style={{ fontSize: '1.05em' }} label={`Current subscription remains ${solarBI.remain_days} days left`} />}
                    {solarBI.plan_id === 1 && <Chip style={{ fontSize: '1.05em' }} label="You are in the free plan" />}
                    {solarBI.remain_days < 0 && solarBI.plan_id !== 1 && <Chip style={{ fontSize: '1.05em' }} label={`Your plan has passed due for ${-solarBI.remain_days} days`} />}
                    <p className={classes.addressText}>
                      {this.props.address.slice(0, -11)}
                    </p>
                    <hr style={{ display: 'block', width: 159, height: 1, border: 0, borderTop: '1px solid #808495', margin: '1em auto 2em', padding: 0 }} />
                  </div>
                  <Container maxWidth="md">
                    <FormLabel classes={{ root: classes.lengthLabel, focused: classes.labelFocused }} component="legend">Length</FormLabel>
                    <div className={classes.dates}>
                      <div className={classes.dateWrapper}>
                        <span className={classes.dateLabel}>Start</span>
                        <MuiPickersUtilsProvider utils={DateFnsUtils}>
                          <KeyboardDatePicker
                            // disableToolbar
                            variant="inline"
                            format="dd/MM/yyyy"
                            id="date-picker-inline"
                            inputVariant="outlined"
                            value={pickerStart}
                            minDate={new Date('1990-01-01')}
                            minDateMessage="Minimal date is 01/01/1990"
                            maxDate={new Date(pickerEnd)}
                            maxDateMessage="Date should not be after End date"
                            onChange={this.handleStartDateChange}
                            InputProps={{
                              classes: { input: classes.textInput },
                            }}
                            FormHelperTextProps={{ classes: { root: classes.helperText } }}
                            KeyboardButtonProps={{
                              'aria-label': 'change date',
                            }}
                          />
                        </MuiPickersUtilsProvider>
                        {/* <TextField
                          error={new Date(startDate) > new Date(endDate) ||
                            new Date(startDate) < new Date('1990-01-01')}
                          id="date"
                          type="date"
                          value={startDate}
                          placeholder="yyyy-mm-dd"
                          variant="outlined"
                          onChange={this.handleStartDateChange}
                          className={classes.startText}
                          InputProps={{
                            classes: { input: classes.textInput },
                          }}
                        /> */}
                      </div>

                      <div className={classes.dateWrapper}>
                        <span className={classes.dateLabel}>End</span>
                        <MuiPickersUtilsProvider utils={DateFnsUtils}>
                          <KeyboardDatePicker
                            // disableToolbar
                            animateYearScrolling
                            variant="inline"
                            format="dd/MM/yyyy"
                            id="date-picker-inline"
                            inputVariant="outlined"
                            value={pickerEnd}
                            minDate={new Date(pickerStart)}
                            minDateMessage="Date should not be before Start date"
                            maxDate={new Date('2019-07-31')}
                            maxDateMessage="Maximum date is 31/07/2019"
                            onChange={this.handleEndDateChange}
                            InputProps={{
                              classes: { input: classes.textInput },
                            }}
                            FormHelperTextProps={{ classes: { root: classes.helperText } }}
                            KeyboardButtonProps={{
                              'aria-label': 'change date',
                            }}
                          />
                        </MuiPickersUtilsProvider>
                        {/* <TextField
                          error={new Date(startDate) > new Date(endDate) ||
                            new Date(endDate) > new Date('2019-07-31')}
                          id="date"
                          type="date"
                          value={endDate}
                          placeholder="yyyy-mm-dd"
                          variant="outlined"
                          onChange={this.handleEndDateChange}
                          className={classes.endText}
                          InputProps={{
                            classes: { input: classes.textInput },
                          }}
                        /> */}
                      </div>
                      <IconButton
                        aria-label="More"
                        className={classes.iconButton}
                        onClick={this.handleQuestionClick}
                      >
                        <HelpIcon />
                      </IconButton>
                      <Popover
                        id="heatmap-popper"
                        open={openAnchor}
                        anchorEl={anchorEl}
                        onClose={this.handleQuestionClose}
                        anchorOrigin={{
                          vertical: 'bottom',
                          horizontal: 'center',
                        }}
                        transformOrigin={{
                          vertical: 'top',
                          horizontal: 'center',
                        }}
                      >
                        <Typography className={classes.typography}>
                          Available date: 01/01/1990 ~ 31/07/2019.
                          Both Start and End date are inclusive.
                        </Typography>
                      </Popover>
                    </div>
                    {/* <hr className={classes.contentHr} />
                    <FormControl component="fieldset" className={classes.formControl}>
                      <FormLabel classes={{ root: classes.typeLabel, focused: classes.labelFocused }} component="legend">Type</FormLabel>
                      <RadioGroup
                        aria-label="type"
                        name="type"
                        className={classes.typeGroup}
                        value={this.state.type}
                        onChange={this.handleTypeChange}
                      >
                        <FormControlLabel classes={{ label: classes.formControlLabel }} value="dni" control={<Radio color="secondary" />} label="DNI" labelPlacement="bottom" />
                        <FormControlLabel classes={{ label: classes.formControlLabel }} value="ghi" control={<Radio color="secondary" />} label="GHI" labelPlacement="bottom" />
                        <FormControlLabel classes={{ label: classes.formControlLabel }} value="both" control={<Radio color="secondary" />} label="Download both" labelPlacement="bottom" />
                      </RadioGroup>
                    </FormControl> */}
                    <hr className={classes.contentHr} />
                    <FormControl component="fieldset" className={classes.formControl}>
                      <FormLabel classes={{ root: classes.resolutionLabel, focused: classes.labelFocused }} component="legend">Resolution</FormLabel>
                      <RadioGroup
                        aria-label="resolution"
                        name="resolution"
                        className={classes.resolutionGroup}
                        value={this.state.resolution}
                        onChange={this.handleResolutionChange}
                      >
                        <FormControlLabel classes={{ label: classes.formControlLabel }} value="hourly" control={<Radio color="secondary" />} label="Hourly" labelPlacement="bottom" />
                        <FormControlLabel classes={{ label: classes.formControlLabel }} value="daily" control={<Radio color="secondary" />} label="Daily" labelPlacement="bottom" />
                        <FormControlLabel classes={{ label: classes.formControlLabel }} value="weekly" control={<Radio color="secondary" />} label="Weekly" labelPlacement="bottom" />
                        <FormControlLabel classes={{ label: classes.formControlLabel }} value="monthly" control={<Radio color="secondary" />} label="Monthly" labelPlacement="bottom" />
                        <FormControlLabel classes={{ label: classes.formControlLabel }} value="annual" control={<Radio color="secondary" />} label="Annual" labelPlacement="bottom" />
                      </RadioGroup>
                    </FormControl>
                    <div style={{ marginTop: 50 }}>
                      <Button
                        className={classNames(classes.button, classes.closeBtn)}
                        disabled={solarBI.sending || solarBI.requestStatus === 'success'}
                        onClick={onHide}
                        color="primary"
                      >
                        Back
                      </Button>
                      {(solarBI.sending || solarBI.requestStatus === 'success') ?
                        (<img className={classes.loading} alt="Loading..." src="/static/assets/images/loading.gif" />) :
                        (<Button className={classNames(classes.button, classes.requestBtn)} onClick={this.handleRequestData} color="primary" disabled={solarBI.remain_count === 0}>REQUEST</Button>)
                      }
                    </div>
                    <p className={classes.remainCount}>
                      * Remaining request(s): {solarBI.remain_count}
                      {remainCount}
                    </p>
                  </Container>
                </CardContent>
              </Card>
            </DialogContent>
          </Dialog>
        </ThemeProvider>
      </div>
    );
  }
}

ExportModal.propTypes = propTypes;

const mapStateToProps = state => ({
  solarBI: state.solarBI,
});

export default withStyles(styles)(
  connect(
    mapStateToProps,
    { requestSolarData, startTrial },
  )(ExportModal),
);
