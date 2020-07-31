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
import { Col, Row } from 'react-bootstrap';
// import { t } from '@superset-ui/translation';

import * as Actions from '../actions/comparison';
import CustomToggle from './CustomToggle';
import ProjectListVersionSelect from './ProjectListVersionSelect';
import BarChart from './BarChart';

const regions = ['NSW', 'QLD', 'SA', 'TAS', 'VIC'];
const fuels = ['Wind', 'Solar'];
const isps = ['Counterfactual', 'Optimal'];
const scenarios = ['Central', 'High DER'];

function App({ username, firstName, lastName, comparison, actions }) {
  return (
    <div className="container app">
      <Row>
        <Col md={9}>
          <h1>{username}</h1>
          <h3>
            {firstName} {lastName}
          </h3>
        </Col>
      </Row>
      <Row>
        <Col sm={1}></Col>
        <Col sm={3}>
          <CustomToggle
            name="region"
            value={comparison.region}
            setValue={actions.setRegion}
            values={regions}
          />
        </Col>
        <Col sm={3}>
          <CustomToggle
            name="fuels"
            value={comparison.fuel}
            setValue={actions.setFuel}
            values={fuels}
          />
        </Col>
        <Col sm={5}>
          <ProjectListVersionSelect
            version={comparison.version}
            setVersion={actions.setVersion}
          />
        </Col>
      </Row>
      <Row>
        <Col sm={1}></Col>
        <Col sm={6}>
          <CustomToggle
            name="isps"
            value={comparison.isp}
            setValue={actions.setIsp}
            values={isps}
          />
        </Col>
        <Col sm={5}>
          <CustomToggle
            name="scenario"
            value={comparison.scenario}
            setValue={actions.setScenario}
            values={scenarios}
          />
        </Col>
      </Row>
      <Row>
        <Col md={12}>
          <BarChart />
        </Col>
      </Row>
    </div>
  );
}

function mapStateToProps(state) {
  const { user, comparison } = state;

  return {
    username: user.username,
    firstName: user.firstName,
    lastName: user.lastName,
    comparison,
  };
}

function mapDispatchToProps(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
  };
}

export { App };
export default connect(mapStateToProps, mapDispatchToProps)(App);
