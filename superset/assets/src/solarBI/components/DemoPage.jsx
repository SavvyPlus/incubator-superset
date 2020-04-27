/* eslint-disable max-len */
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
import { withStyles, createMuiTheme, MuiThemeProvider } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
// import Button from '@material-ui/core/Button';
import CardContent from '@material-ui/core/CardContent';
import AppBar from '@material-ui/core/AppBar';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Typography from '@material-ui/core/Typography';
import DemoChart from './DemoChart';

function TabContainer(props) {
  return (
    <Typography component="div" style={{ padding: 8 * 3 }}>
      {props.children}
    </Typography>
  );
}

TabContainer.propTypes = {
  children: PropTypes.node.isRequired,
};


const propTypes = {
  classes: PropTypes.object.isRequired,
};

const theme = createMuiTheme({
  typography: {
    useNextVariants: true,
  },
  palette: {
    primary: {
      main: '#EDEEEF',
    },
    secondary: {
      main: '#0165AE',
      background: 'linear-gradient(.25turn, #10998C, #09809D, #0063B0)',
    },
  },
});

const styles = tm => ({
  button: {
    // fontSize: '1.2em',
    // width: '18%',
    margin: '10 10',
    height: 40,
    padding: '0 16px',
    minWidth: 115,
    borderRadius: 60,
    color: 'white',
    backgroundColor: '#0063B0',
    border: 'none',
    fontSize: 16,
    fontFamily: 'Open Sans, sans-serif',
    fontWeight: 'bold',
    '&:hover': {
      color: 'white',
      backgroundColor: '#034980',
    },
  },
  cardFlex: {
    marginTop: 90,
    minHeight: 290,
    height: 290,
    borderRadius: 12,
    fontFamily: 'Open Sans, sans-serif',
  },
  cardInitial: {
    marginTop: 160,
    marginBottom: 30,
    minHeight: 290,
    height: 530,
    borderRadius: 12,
  },
  chartCard: {
    marginTop: 90,
    minHeight: 400,
    height: 400,
    borderRadius: 12,
    fontFamily: 'Open Sans, sans-serif',
  },
  chartCardContent: {
    padding: 0,
  },
  contentFlex: {
    display: 'flex',
    padding: 0,
  },
  contentInitial: {
    display: 'initial',
  },
  head: {
    textAlign: 'center',
    height: 50,
    background: 'linear-gradient(.25turn, #10998C, #09809D, #0063B0)',
    backgroundColor: 'white',
    width: '100%',
    color: 'white',
    fontWeight: 'bold',
    paddingTop: 15,
  },
  indicator: {
    background: 'linear-gradient(.25turn, #10998C, #09809D, #0063B0)',
  },
  tab: {
    fontSize: 18,
    fontFamily: 'Open Sans, sans-serif',
    fontWeight: 'bold',
    minWidth: 50,
    width: 120, // a number of your choice
  },
  tabActive: {
    color: 'white',
    background: 'linear-gradient(.25turn, #10998C, #09809D, #0063B0)',
  },
  tabDefault: {
    color: '#abadb0',
    backgroundColor: '#EDEEEF',
  },
  textWrapper: {
    display: 'flex',

  },
  text: {
    color: '#0063B0',
    fontSize: 16,
    fontFamily: 'Open Sans, sans-serif',
    fontWeight: 500,

  },
  textField: {
    marginLeft: tm.spacing(1),
    marginRight: tm.spacing(1),
    width: 750,
  },
});

class DemoPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      value: 0,
    };

    this.handleChange = this.handleChange.bind(this);
  }

  handleChange(event, value) {
    this.setState({ value });
  }

  render() {
    const { classes } = this.props;
    const { value } = this.state;
    const stateFullName = {
      WA: 'Western Australia',
      NT: 'Northern Territory',
      QLD: 'Queensland',
      NSW: 'New South Wales',
      ACT: 'Australian Capital Territory',
      VIC: 'Victoria',
      SA: 'South Australia',
      TAS: 'Tasmania',
    };
    const ausStates = ['VIC', 'NSW', 'QLD', 'NT', 'SA', 'WA', 'TAS'];

    return (
      <MuiThemeProvider theme={theme}>
        <Card className={classes.cardFlex}>
          <CardContent className={classes.contentFlex}>
            <div className={classes.demo}>
              <AppBar position="static">
                <Tabs
                  value={value}
                  onChange={this.handleChange}
                  classes={{ indicator: classes.indicator }}
                >
                  <Tab className={value === 0 ? classes.tabActive : classes.tabDefault} classes={{ root: classes.tab }} label="VIC" />
                  <Tab className={value === 1 ? classes.tabActive : classes.tabDefault} classes={{ root: classes.tab }} label="NSW" />
                  <Tab className={value === 2 ? classes.tabActive : classes.tabDefault} classes={{ root: classes.tab }} label="QLD" />
                  <Tab className={value === 3 ? classes.tabActive : classes.tabDefault} classes={{ root: classes.tab }} label="NT" />
                  <Tab className={value === 4 ? classes.tabActive : classes.tabDefault} classes={{ root: classes.tab }} label="SA" />
                  <Tab className={value === 5 ? classes.tabActive : classes.tabDefault} classes={{ root: classes.tab }} label="WA" />
                  <Tab className={value === 6 ? classes.tabActive : classes.tabDefault} classes={{ root: classes.tab }} label="TAS" />
                </Tabs>
              </AppBar>
              {value === 0 && <TabContainer>
                <div className={classes.textWrapper}>
                  <p className={classes.text}>
                    Located around 10km south-south-east of Bendigo, the centre of Victoria <br />
                    might be considered to be on the steps of the Mandurang Uniting Church.<br />
                    No longer in use, the church sits on the site that corresponds with centroid<br />
                    calculations from a number of different organisations, including Geoscience <br />
                    Australia, the Department of Natural Resources and Environment (DNRE), and <br />
                    the Department of Geospatial Science, Royal Melbourne Institute of Technology (RMIT).<br />
                    <br />
                    <br />
                    Location: 42° 01' 17" South, 146° 35' 36" East
                  </p>
                </div>
              </TabContainer>}
              {value === 1 && <TabContainer>
                <div className={classes.textWrapper}>
                  <p className={classes.text}>
                    One possible definition of the centre for New South Wales is located just off Cockies Road, <br />
                    33km west-north-west of Tottenham (Tottenham is 110km west of Dubbo). This spot, <br />
                    south of the Fiveways Intersection, is marked by a large sign, constructed for Australia's <br />
                    Bicentennial celebrations.<br />
                    <br />
                    Location: 32° 09' 48" South, 147° 01' 00" East</p>
                </div>
              </TabContainer>}
              {value === 2 && <TabContainer>
                <p className={classes.text}>
                  In Queensland, the geographical centre is located 17km north-west of Muttaburra. <br />
                  Also famous from a paleontological perspective, this region was once a pre-historic inland sea.<br />
                  A wealth of fossilized remains has been uncovered here, and when a previously <br />
                  undiscovered species was found, it was became known as the Muttaburrasaurus.<br />
                  <br />
                  <br />
                  Location: 22° 29' 13" South, 144° 25' 54" East</p>
              </TabContainer>}
              {value === 3 && <TabContainer>
                <p className={classes.text}>
                  Using the method described earlier, one estimate of where the centre of the<br />
                  Northern Territory lies can be found approximately 91 km west-north-west of<br />
                  Tennant Creek. A short distance past the Kartijirarrakanya Claypan, <br />
                  this centre is in a particularly harsh, arid part of the territory.<br />
                  <br />
                  Location: 19° 23' 00" South, 133° 21' 28" East</p>
              </TabContainer>}
              {value === 4 && <TabContainer>
                <p className={classes.text}>
                  Despite three sides of its border being straight lines, defining the centre of<br />
                  South Australia is no easier thanks to an irregular shaped coastline.<br />
                  According to one method, the centre is near the Churchill Smith bore, <br />
                  which is approximately 12km north-east of the Mt Eba cattle station.<br />
                  In relation to more commonly known landmarks, the centre of <br />
                  South Australia is located some distance south-west of Lake Eyre.<br />
                  <br />
                  <br />
                  Location: 30° 03' 30" South, 135° 45' 48" East</p>
              </TabContainer>}
              {value === 5 && <TabContainer>
                <p className={classes.text}>
                  In Western Australia, what could be called the centre is found in the<br />
                  Gascoyne Region, east south-east of the Glenayle Homestead and north<br />
                  east of the Glenayle - Carnegie Road.<br />
                  <br />
                  <br />
                  Location: 25° 19' 41" South, 122° 17' 54" East</p>
              </TabContainer>}
              {value === 6 && <TabContainer>
                <p className={classes.text}>
                  One possible centre for Tasmania is found on the western shore of Little Pine Lagoon.<br />
                  This small lake lies next to the Marlborough Highway, between the towns of Bronte and Miena.<br />
                  On the Lyell Highway, just a short distance east of Bronte, lies a cairn which was erected<br />
                  in 1983 by members of the Institution of Surveyors (Australian Tasmanian Division). <br />
                  This marker commemorates the early surveyors who explored and mapped the state, <br />
                  and marks Trig Point 715 - said to be near the geographical centre.<br />
                  <br />
                  <br />
                  Location: 42° 01' 17" South, 146° 35' 36" East</p>
              </TabContainer>}
            </div>
          </CardContent>
        </Card>

        <Card className={classes.chartCard}>
          <CardContent className={classes.chartCardContent}>
            <div className={classes.head}>{stateFullName[ausStates[value]]}</div>
            <div style={{ width: '100%' }}>
              <DemoChart ausState={ausStates[value]} />
            </div>
          </CardContent>
        </Card>
      </MuiThemeProvider>
    );
  }
}

DemoPage.propTypes = propTypes;

export default withStyles(styles)(DemoPage);
