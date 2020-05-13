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
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { Col, Row, Tabs, Tab, Panel } from 'react-bootstrap';
import { t } from '@superset-ui/translation';
import { ThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import RegionSelect from './RegionSelect';
import HeadSelect from './HeadSelect';
import Charts from './Charts';

const theme = createMuiTheme({
  palette: {
    primary: {
      main: '#c74523',
    },
    secondary: {
      main: '#fff',
    },
  },
  typography: {
    button: {
      color: '#c74523',
    },
  },
});

function App({ username, firstName, lastName }) {
  return (
    <ThemeProvider theme={theme}>
      <div className="container app">
        <Row>
          <RegionSelect />
        </Row>
        <Row>
          <HeadSelect />
        </Row>
        <Row>
          <Charts />
        </Row>
      </div>
    </ThemeProvider>
  );
}

function mapStateToProps(state) {
  const { user } = state;

  return {
    username: user.username,
    firstName: user.firstName,
    lastName: user.lastName,
  };
}

export default connect(mapStateToProps)(App);
