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

import * as Actions from '../actions/assumption';
import UpsertSelect from './UpsertSelect';
import TableSelect from './TableSelect';
import VersionSelect from './VersionSelect';
import Dropzone from './Dropzone';
import ToastPresenter from '../../messageToasts/containers/ToastPresenter';
import '../App.less';
import AssumptionTable from './AssumptionTable';

function App({ username, firstName, lastName, assumption, actions }) {
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
        <Col md={8}>
          <UpsertSelect
            upsert={assumption.upsert}
            setUpsert={actions.setUpsert}
          />
        </Col>
      </Row>
      <Row>
        <Col md={8}>
          <TableSelect table={assumption.table} setTable={actions.setTable} />
        </Col>
      </Row>
      <Row>
        <Col md={8}>
          {assumption.upsert === 'upload' ? (
            <Dropzone
              table={assumption.table}
              uploadFile={actions.uploadFile}
            />
          ) : (
            <>
              <VersionSelect
                versions={assumption.versions}
                upsert={assumption.upsert}
                table={assumption.table}
                version={assumption.version}
                fetching={assumption.fetchingVersions}
                setVersion={actions.setVersions}
                fetchTableVersions={actions.fetchTableVersions}
              />
              <AssumptionTable
                upsert={assumption.upsert}
                table={assumption.table}
                tableData={assumption.tableData}
                version={assumption.version}
                fetchTableVersions={actions.fetchTableVersions}
              />
            </>
          )}
        </Col>
      </Row>
      <ToastPresenter />
    </div>
  );
}

function mapStateToProps(state) {
  const { user, assumption } = state;

  return {
    username: user.username,
    firstName: user.firstName,
    lastName: user.lastName,
    assumption,
  };
}

function mapDispatchToProps(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
  };
}

export { App };
export default connect(mapStateToProps, mapDispatchToProps)(App);
