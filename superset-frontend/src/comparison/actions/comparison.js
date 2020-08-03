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

export const FETCH_CHART_DATA_STARTED = 'FETCH_CHART_DATA_STARTED';
export function fetchChartDataStarted() {
  return { type: FETCH_CHART_DATA_STARTED };
}

export const FETCH_CHART_DATA_SUCCESS = 'FETCH_CHART_DATA_SUCCESS';
export function fetchChartDataSuccuss(res) {
  return { type: FETCH_CHART_DATA_SUCCESS, res };
}

export const FETCH_CHART_DATA_FAILED = 'FETCH_CHART_DATA_FAILED';
export function fetchChartDataFailed() {
  return { type: FETCH_CHART_DATA_FAILED };
}

export function fetchChartData(region, fuel, version) {
  console.log(region, fuel, version);
  return dispatch => {
    return SupersetClient.get({
      endpoint: `/assumption-book/get-data/`,
    })
      .then(({ json }) => {
        dispatch(fetchChartDataSuccuss(json));
        dispatch(addSuccessToast(t('Chart data was fetched successfully')));
      })
      .catch(() => {
        dispatch(fetchChartDataFailed());
        dispatch(
          addDangerToast(t('Sorry, there was an error fetching the data')),
        );
      });
  };
}
