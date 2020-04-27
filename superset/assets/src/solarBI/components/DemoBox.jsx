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
import { withStyles } from '@material-ui/styles';
import withWidth from '@material-ui/core/withWidth';
import Card from '@material-ui/core/Card';
import Button from '@material-ui/core/Button';
import CardContent from '@material-ui/core/CardContent';

const propTypes = {
  classes: PropTypes.object.isRequired,
  width: PropTypes.string.isRequired,
};

const styles = tm => ({
  textField: {
    marginLeft: tm.spacing(1),
    marginRight: tm.spacing(1),
    width: 750,
  },
  button: {
    width: 240,
    height: 60,
    border: 'none',
    backgroundColor: '#EDEEEF',
    borderRadius: 10,
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0063B0',
    '&:hover': {
      backgroundColor: '#b8b8b8',
    },
    // '&:focus': {
    //   outline: 'none !important',
    // },
    // '&:active': {
    //   color: '#FFB2B2',
    // },
  },
  cardFlex: {
    marginTop: 160,
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
    fontFamily: 'Open Sans, sans-serif',
  },
  contentFlex: {
    display: 'flex',
  },
  contentInitial: {
    display: 'initial',
  },
  demo: {
    marginTop: 20,
    marginLeft: 10,
    textAlign: 'center',
  },
  fab: {
    width: 60,
    height: 60,
    marginLeft: 20,
  },
  introLarge: {
    width: 260,
    marginTop: 30,
    fontSize: 16,
    color: '#0063B0',
  },
  introSmall: {
    marginTop: 30,
    fontSize: 14,
    color: '#0063B0',
  },
  saved: {
    display: 'block',
    margin: 'auto',
    marginTop: -10,
    width: 180,
    fontFamily: 'Open Sans, sans-serif',
    fontSize: 16,
    color: '#0063B0',
  },
  vl: {
    borderLeft: '1px solid #C7C9CB',
    height: 100,
    width: 3,
    margin: '110 10 0 20',
  },
});

class DemoBox extends React.Component {
  constructor(props) {
    super(props);
    this.state = {

    };
  }

  render() {
    const { classes, width } = this.props;
    const isSmallScreen = /xs|sm|md/.test(width);

    return (
      <div>
        {!isSmallScreen ?
          <Card className={isSmallScreen ? classes.cardInitial : classes.cardFlex}>
            <CardContent
              className={isSmallScreen ? classes.contentInital : classes.contentFlex}
            >
              <div className={classes.demo}>
                <Button className={classes.button}>
                  Search
                </Button>
                <p className={isSmallScreen ? classes.introSmall : classes.introLarge} >
                  Search for any address, <br /> suburb or region
                   in Australia
                </p>
              </div>

              {isSmallScreen ? null : <div className={classes.vl} />}
              <div className={classes.demo}>
                <Button className={classes.button}>
                  Quick Result
                </Button>
                <p className={isSmallScreen ? classes.introSmall : classes.introLarge}>
                  We look for the closest point <br />
                  to your seach and give you <br />
                  12 months of data
                </p>
              </div>
              {isSmallScreen ? null : <div className={classes.vl} />}
              <div className={classes.demo}>
                <Button className={classes.button}>
                  Get More Data
                </Button>
                <p className={isSmallScreen ? classes.introSmall : classes.introLarge}>
                  Go deeper and define type, <br />
                  timeframe and resolution <br />
                  Your .CSV export will wait on <br />
                  <br />
                  <a className={classes.saved} href="/solar/list">My Data</a>
                </p>
              </div>
            </CardContent>
          </Card>
          : null
        }
      </div>
    );
  }
}

DemoBox.propTypes = propTypes;

export default withWidth()(withStyles(styles)(DemoBox));
