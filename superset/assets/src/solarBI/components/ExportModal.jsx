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
// import Typography from '@material-ui/core/Typography';
// import IconButton from '@material-ui/core/IconButton';
// import Popover from '@material-ui/core/Popover';
// import HelpIcon from '@material-ui/icons/Help';
import DialogContent from '@material-ui/core/DialogContent';
import Chip from '@material-ui/core/Chip';
import Radio from '@material-ui/core/Radio';
import RadioGroup from '@material-ui/core/RadioGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormControl from '@material-ui/core/FormControl';
import FormLabel from '@material-ui/core/FormLabel';
import Switch from '@material-ui/core/Switch';
import Container from '@material-ui/core/Container';
import DateFnsUtils from '@date-io/date-fns';
import { MuiPickersUtilsProvider, KeyboardDatePicker } from '@material-ui/pickers';
import SolarStepper from './SolarStepper';
import CountdownDialog from './CountdownDialog';
import CheatSheet from './CheatSheet';
import RemainingRequests from './RemainingRequests';
import UnitSelection from './UnitSelection';
import CapacityInputs from './CapacityInputs';
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
    fontFamily: 'Montserrat',
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
    marginTop: 50,
    marginLeft: 0,
    width: '100%',
    transition: 'all 0.5s',
  },
  buttonsLeft: {
    marginTop: 50,
    marginLeft: 127,
    width: 500,
    transition: 'all 0.5s',
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
  ctn: {
    marginLeft: 0,
    transition: 'all 0.5s',
  },
  ctnLeft: {
    marginLeft: -160,
    transition: 'all 0.5s',
  },
  dates: {
    display: 'flex',
    width: 500,
    marginLeft: 127,
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
  endText: {
    marginLeft: '15px',
    '& fieldset': {
      borderRadius: 12,
    },
  },
  exportCard: {
    margin: '40px auto',
    width: 850,
    height: 700,
    position: 'relative',
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
    // marginBottom: '5px',
    width: 220,
    display: 'inline-block',
    // margin: theme.spacing(2),
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
    width: 120,
    float: 'left',
    borderBottom: 'none',
    marginTop: 25,
  },
  remainCount: {
    float: 'right',
  },
  selections: {
    display: 'flex',
    width: 460,
    marginLeft: 150,
  },
  startText: {
    marginLeft: '10px',
    '& fieldset': {
      borderRadius: 12,
    },
  },
  switch: {
    color: 'rgb(117, 117, 117)',
    display: 'inline-block',
  },
  title: {
    color: '#0063B0',
    fontSize: '1.6em',
    textAlign: 'center',
    paddingBottom: 0,
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
  typography: {
    margin: theme.spacing(2),
    fontSize: 15,
    width: 300,
  },
  resolutionGroup: {
    // flexDirection: 'row',
    width: 250,
    // float: 'left',
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
      pickerStart: new Date('2007-01-01T00:00:00'),
      pickerEnd: new Date('2019-07-01T00:00:00'),
      startDate: '2007-01-01',
      endDate: '2019-07-01',
      resolution: 'hourly',
      generation: true,
      // capacity: '1',
      countdown: false,
      opencs: false,
      unit: 'MWh',
      cap1: null,
      cap1Err: false,
      cap2: null,
      cap2Err: false,
    };

    this.handleStartDateChange = this.handleStartDateChange.bind(this);
    this.handleEndDateChange = this.handleEndDateChange.bind(this);
    this.handleResolutionChange = this.handleResolutionChange.bind(this);
    this.handleRequestData = this.handleRequestData.bind(this);
    this.handleQuestionClick = this.handleQuestionClick.bind(this);
    this.handleQuestionClose = this.handleQuestionClose.bind(this);
    this.handleGenerationChange = this.handleGenerationChange.bind(this);
    // this.handleCapacityChange = this.handleCapacityChange.bind(this);
    this.handleTrialClick = this.handleTrialClick.bind(this);
    this.toggleCSDrawer = this.toggleCSDrawer.bind(this);
    this.handleUnitChange = this.handleUnitChange.bind(this);
    this.handleCap1Change = this.handleCap1Change.bind(this);
    this.handleCap2Change = this.handleCap2Change.bind(this);
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

  // handleCapacityChange(event) {
  //   this.setState({ capacity: event.target.value });
  // }

  handleQuestionClick(event) {
    this.setState({ anchorEl: event.currentTarget });
  }

  handleQuestionClose() {
    this.setState({ anchorEl: null });
  }

  handleGenerationChange() {
    if (this.state.resolution === 'halfhourly') {
      this.setState({ resolution: 'hourly' });
    }

    this.setState({ generation: !this.state.generation });
  }

  handleUnitChange(event) {
    this.setState({ unit: event.target.value });
  }

  handleCap1Change(event) {
    this.setState({ cap1: event.target.value });
  }

  handleCap2Change(event) {
    this.setState({ cap2: event.target.value });
  }

  handleTrialClick() {
    this.props.startTrial();
  }

  handleRequestData() {
    this.setState({ cap1Err: false, cap2Err: false });

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
    } else if (this.state.cap1 === null || this.state.cap2 === null) {
      if (this.state.cap1 === null) this.setState({ cap1Err: true });
      if (this.state.cap2 === null) this.setState({ cap2Err: true });
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
        generation: this.state.generation ? '1' : '0',
        unit: this.state.unit,
        cap1: this.state.cap1,
        cap2: this.state.cap2,
      };

      this.props.requestSolarData(queryData)
        .then((json) => {
          if (json.type === 'REQEUST_SOLAR_DATA_SUCCEEDED') {
            this.setState({ countdown: true });
          }
        });
    }
  }

  toggleCSDrawer() {
    this.setState({ opencs: !this.state.opencs });
  }

  render() {
    const { classes, open, onHide, solarBI } = this.props;
    // const { startDate, endDate, anchorEl, pickerStart, pickerEnd } = this.state;
    const { pickerStart, pickerEnd, countdown,
      opencs, unit, cap1, cap1Err, cap2, cap2Err, generation } = this.state;
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
    let request = <Button className={classNames(classes.button, classes.requestBtn)} onClick={this.handleRequestData} color="primary" disabled={solarBI.remain_count === 0}>REQUEST</Button>;
    if (solarBI.sending) {
      request = <img className={classes.loading} alt="Loading..." src="/static/assets/images/loading.gif" />;
    } else if (solarBI.requestStatus === 'success') {
      request = <img className={classes.loading} alt="Request success!" src="/static/assets/images/tick_mark.gif" />;
    }

    // const openAnchor = Boolean(anchorEl);

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
                    <RemainingRequests requests={solarBI.remain_count} />
                    <p className={classes.addressText}>
                      {this.props.address.slice(0, -11)}
                    </p>
                    <hr style={{ display: 'block', width: 159, height: 1, border: 0, borderTop: '1px solid #808495', margin: '1em auto 2em', padding: 0 }} />
                  </div>
                  <Container className={!opencs ? classes.ctn : classes.ctnLeft} maxWidth="md">
                    <div className={classes.dates}>
                      <div className={classes.dateWrapper}>
                        <span className={classes.dateLabel}>Start</span>
                        <MuiPickersUtilsProvider utils={DateFnsUtils}>
                          <KeyboardDatePicker
                            // disableToolbar
                            variant="inline"
                            format="dd/MM/yyyy"
                            id="date-picker-start"
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
                      </div>

                      <div className={classes.dateWrapper}>
                        <span className={classes.dateLabel}>End</span>
                        <MuiPickersUtilsProvider utils={DateFnsUtils}>
                          <KeyboardDatePicker
                            // disableToolbar
                            animateYearScrolling
                            variant="inline"
                            format="dd/MM/yyyy"
                            id="date-picker-end"
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
                      </div>
                      {/* <IconButton
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
                      </Popover> */}
                    </div>
                    {/* <hr className={classes.contentHr} /> */}
                    <div className={classes.selections}>
                      <FormControl component="fieldset" className={classes.formControl}>
                        <FormLabel classes={{ root: classes.resolutionLabel, focused: classes.labelFocused }} component="legend">Generation</FormLabel>
                        <div style={{ marginTop: 15 }}>
                          <Switch
                            checked={generation}
                            // onChange={this.handleGenerationChange}
                            onClick={() => this.handleGenerationChange()}
                            value="generation"
                          />
                        </div>
                        {generation && (
                          <React.Fragment>
                            <UnitSelection unit={unit} handleUnitChange={this.handleUnitChange} />
                            <CapacityInputs
                              cap1={cap1}
                              cap1Err={cap1Err}
                              cap2={cap2}
                              cap2Err={cap2Err}
                              handleCap1Change={this.handleCap1Change}
                              handleCap2Change={this.handleCap2Change}
                            />
                          </React.Fragment>
                        )}

                      </FormControl>
                      <FormControl style={{ margin: '15px 0 0 25px' }} component="fieldset" className={classes.formControl}>
                        <RadioGroup
                          aria-label="resolution"
                          name="resolution"
                          className={classes.resolutionGroup}
                          value={this.state.resolution}
                          onChange={this.handleResolutionChange}
                        >
                          <FormControlLabel disabled={!generation} classes={{ label: classes.formControlLabel }} value="halfhourly" control={<Radio color="secondary" />} label="30 min (Generation only)" labelPlacement="end" />
                          <FormControlLabel classes={{ label: classes.formControlLabel }} value="hourly" control={<Radio color="secondary" />} label="Hourly" labelPlacement="end" />
                          <FormControlLabel classes={{ label: classes.formControlLabel }} value="daily" control={<Radio color="secondary" />} label="Daily" labelPlacement="end" />
                          <FormControlLabel classes={{ label: classes.formControlLabel }} value="weekly" control={<Radio color="secondary" />} label="Weekly" labelPlacement="end" />
                          <FormControlLabel classes={{ label: classes.formControlLabel }} value="monthly" control={<Radio color="secondary" />} label="Monthly" labelPlacement="end" />
                          <FormControlLabel classes={{ label: classes.formControlLabel }} value="annual" control={<Radio color="secondary" />} label="Annual" labelPlacement="end" />
                        </RadioGroup>
                      </FormControl>
                    </div>
                    <div className={!opencs ? classes.buttons : classes.buttonsLeft}>
                      <Button
                        className={classNames(classes.button, classes.closeBtn)}
                        disabled={solarBI.sending || solarBI.requestStatus === 'success'}
                        onClick={onHide}
                        color="primary"
                      >
                        Back
                      </Button>
                      {request}
                    </div>
                    <p className={classes.remainCount}>
                      {/* * Remaining request(s): {solarBI.remain_count} */}
                      {remainCount}
                    </p>
                  </Container>
                </CardContent>
                <CheatSheet open={opencs} toggleDrawer={this.toggleCSDrawer} />
              </Card>
            </DialogContent>
          </Dialog>
          <CountdownDialog open={countdown} />
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
