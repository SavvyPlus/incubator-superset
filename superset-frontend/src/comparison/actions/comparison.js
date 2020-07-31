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
import { t } from '@superset-ui/translation';
import { SupersetClient } from '@superset-ui/connection';
import { addSuccessToast, addDangerToast } from '../../messageToasts/actions';

export const SET_REGION = 'SET_REGION';
export function setRegion(region) {
  return { type: SET_REGION, region };
}

export const SET_FUEL = 'SET_FUEL';
export function setFuel(fuel) {
  return { type: SET_FUEL, fuel };
}

export const SET_VERSION = 'SET_VERSION';
export function setVersion(version) {
  return { type: SET_VERSION, version };
}

export const SET_ISP = 'SET_ISP';
export function setIsp(isp) {
  return { type: SET_ISP, isp };
}

export const SET_SCENARIO = 'SET_SCENARIO';
export function setScenario(scenario) {
  return { type: SET_SCENARIO, scenario };
}

export const FETCH_TABLE_DATA_STARTED = 'FETCH_TABLE_DATA_STARTED';
export function fetchTableDataStarted() {
  return { type: FETCH_TABLE_DATA_STARTED };
}

export const FETCH_TABLE_DATA_SUCCESS = 'FETCH_TABLE_DATA_SUCCESS';
export function fetchTableDataSuccuss(res) {
  return { type: FETCH_TABLE_DATA_SUCCESS, res };
}

export const FETCH_TABLE_DATA_FAILED = 'FETCH_TABLE_DATA_FAILED';
export function fetchTableDataFailed(data) {
  return { type: FETCH_TABLE_DATA_FAILED, data };
}

export function fetchTableData(table, version) {
  return dispatch => {
    return SupersetClient.get({
      endpoint: `/edit-assumption/get-data/${table}/data/${version}`,
    })
      .then(({ json }) => {
        dispatch(fetchTableDataSuccuss(json));
        dispatch(addSuccessToast(t('Table data was fetched successfully')));
      })
      .catch(() => {
        dispatch(fetchTableDataFailed());
        dispatch(
          addDangerToast(t('Sorry, there was an error fetching the data')),
        );
      });
  };
}
