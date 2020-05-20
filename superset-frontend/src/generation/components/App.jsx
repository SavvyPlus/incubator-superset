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
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { Col, Row, Tabs, Tab, Panel } from 'react-bootstrap';
import { t } from '@superset-ui/translation';
import { ThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import RegionSelect from './RegionSelect';
import HeadSelect from './HeadSelect';
import Charts from './Charts';
import DataTable from './DataTable';
import * as Actions from '../actions/generation';
import '../App.less';

const theme = createMuiTheme({
  // palette: {
  //   primary: {
  //     main: '#c74523',
  //   },
  //   secondary: {
  //     main: '#fff',
  //   },
  // },
  typography: {
    button: {
      color: '#c74523',
    },
  },
});

function App({ actions, generation }) {
  return (
    <ThemeProvider theme={theme}>
      <div className="generation-container app">
        <Row>
          <RegionSelect
            region={generation.region}
            setRegion={actions.setRegion}
          />
        </Row>
        <Row>
          <HeadSelect
            range={generation.range}
            setRange={actions.setRange}
            granularity={generation.granularity}
            setGranularity={actions.setGranularity}
          />
        </Row>
        <Row>
          <Col md={8}>
            <Charts />
          </Col>
          <Col md={4}>
            <DataTable />
          </Col>
        </Row>
      </div>
    </ThemeProvider>
  );
}

function mapStateToProps(state) {
  const { generation } = state;
  return {
    generation,
  };
}

function mapDispatchToProps(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
  };
}

export { App };
export default connect(mapStateToProps, mapDispatchToProps)(App);
