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
/* eslint camelcase: 0 */
import { SupersetClient } from '@superset-ui/connection';
import { t } from '@superset-ui/translation';
import URI from 'urijs';
import { logEvent } from '../../logger/actions';
import { Logger, LOG_ACTIONS_LOAD_CHART } from '../../logger/LogUtils';
import getClientErrorObject from '../../utils/getClientErrorObject';
// import { getExploreUrlAndPayload, getURIDirectory } from '../../explore/exploreUtils';
// import { saveSliceFailed, saveSliceSuccess } from '../../explore/actions/saveModalActions';
import {
  addSuccessToast as addSuccessToastAction,
  addDangerToast as addDangerToastAction,
  addInfoToast as addInfoToastAction,
} from '../../messageToasts/actions/index';

export const addInfoToast = addInfoToastAction;
export const addSuccessToast = addSuccessToastAction;
export const addDangerToast = addDangerToastAction;

export const SOLAR_UPDATE_STARTED = 'SOLAR_UPDATE_STARTED';
export function solarUpdateStarted(queryController, latestQueryFormData, key) {
  return {
    type: SOLAR_UPDATE_STARTED,
    queryController,
    latestQueryFormData,
    key,
  };
}

export const SOLAR_UPDATE_SUCCEEDED = 'SOLAR_UPDATE_SUCCEEDED';
export function solarUpdateSucceeded(queryResponse, key) {
  return { type: SOLAR_UPDATE_SUCCEEDED, queryResponse, key };
}

export const SOLAR_UPDATE_TIMEOUT = 'SOLAR_UPDATE_TIMEOUT';
export function solarUpdateTimeout(statusText, timeout, key) {
  return { type: SOLAR_UPDATE_TIMEOUT, statusText, timeout, key };
}

export const SOLAR_UPDATE_STOPPED = 'SOLAR_UPDATE_STOPPED';
export function solarUpdateStopped(key) {
  return { type: SOLAR_UPDATE_STOPPED, key };
}

export const SOLAR_UPDATE_FAILED = 'SOLAR_UPDATE_FAILED';
export function solarUpdateFailed(queryResponse, key) {
  return { type: SOLAR_UPDATE_FAILED, queryResponse, key };
}

export const FETCH_SOLAR_DATA = 'FETCH_SOLAR_DATA';
export function fetchSolarData(formData, force = false, timeout = 60, key) {
  return (dispatch) => {
    const url =
      '/superset/explore_json/' +
      formData.datasource_type +
      '/' +
      formData.datasource_id +
      '/';
    const logStart = Logger.getTimestamp();
    const controller = new AbortController();
    const { signal } = controller;
    dispatch(solarUpdateStarted(controller, formData, key));

    return SupersetClient.post({
      url,
      postPayload: { form_data: formData },
      signal,
      timeout: timeout * 1000,
    })
      .then(({ json }) => {
        dispatch(logEvent(LOG_ACTIONS_LOAD_CHART, {
          slice_id: key,
          is_cached: json.is_cached,
          force_refresh: force,
          row_count: json.rowcount,
          datasource: formData.datasource,
          start_offset: logStart,
          duration: Logger.getTimestamp() - logStart,
          has_extra_filters:
            formData.extra_filters && formData.extra_filters.length > 0,
          viz_type: formData.viz_type,
        }));
        dispatch(addSuccessToastAction(t('Successfully fetched solar data!')));
        return dispatch(solarUpdateSucceeded(json, key));
      })
      .catch((response) => {
        const appendErrorLog = (errorDetails) => {
          dispatch(logEvent(LOG_ACTIONS_LOAD_CHART, {
            slice_id: key,
            has_err: true,
            error_details: errorDetails,
            datasource: formData.datasource,
            start_offset: logStart,
            duration: Logger.getTimestamp() - logStart,
          }));
        };

        if (response.statusText === 'timeout') {
          appendErrorLog('timeout');
          dispatch(addDangerToast(t('Fetching timeout!')));
          return dispatch(
            solarUpdateTimeout(response.statusText, timeout, key),
          );
        } else if (response.name === 'AbortError') {
          appendErrorLog('abort');
          dispatch(addDangerToast(t('Fetching abort!')));
          return dispatch(solarUpdateStopped(key));
        }
        return getClientErrorObject(response).then((parsedResponse) => {
          appendErrorLog(parsedResponse.error);
          dispatch(addDangerToast(t('Fetching failed!')));
          return dispatch(solarUpdateFailed(parsedResponse, key));
        });
      });
  };
}

export const SAVE_SOLAR_DATA_SUCCESS = 'SAVE_SOLAR_DATA_SUCCESS';
export function saveSolarDataSuccess(data) {
  return { type: SAVE_SOLAR_DATA_SUCCESS, data };
}

export const SAVE_SOLAR_DATA_FAILED = 'SAVE_SOLAR_DATA_FAILED';
export function saveSolarDataFailed() {
  return { type: SAVE_SOLAR_DATA_FAILED };
}

export function saveSolarData(formData, requestParams) {
  return (dispatch) => {
    const directory = '/superset/solar/';
    const payload = {
      ...formData,
      endpointType: 'base',
      requestParams,
    };

    let uri = new URI([location.protocol, '//', location.host].join(''));
    const search = uri.search(true);
    const paramNames = Object.keys(requestParams);
    if (paramNames.length) {
      paramNames.forEach((name) => {
        if (requestParams.hasOwnProperty(name)) {
          search[name] = requestParams[name];
        }
      });
    }
    uri = uri.search(search).directory(directory);

    return SupersetClient.post({
      url: uri.toString(),
      postPayload: { form_data: payload },
    })
      .then(({ json }) => {
        dispatch(addSuccessToastAction(t('Successfully save data into My Data!')));
        dispatch(saveSolarDataSuccess(json));
      }).catch(() => dispatch(saveSolarDataFailed()));
  };
}

export const REQEUST_SOLAR_DATA_STARTED = 'REQEUST_SOLAR_DATA_STARTED';
export function requestSolarDataStarted() {
  return { type: REQEUST_SOLAR_DATA_STARTED };
}

export const REQEUST_SOLAR_DATA_SUCCEEDED = 'REQEUST_SOLAR_DATA_SUCCEEDED';
export function requestSolarDataSucceeded(data) {
  return { type: REQEUST_SOLAR_DATA_SUCCEEDED, data };
}

export const REQUEST_SOLAR_DATA_FAILED = 'REQUEST_SOLAR_DATA_FAILED';
export function requestSolarDataFailed() {
  return { type: REQUEST_SOLAR_DATA_FAILED };
}

export function requestSolarData(queryData, timeout = 60) {
  return (dispatch) => {
    const url =
      '/superset/request_data/' +
      queryData.lat + '/' + queryData.lng + '/' +
      queryData.startDate + '/' + queryData.endDate + '/' +
      queryData.resolution + '/' + queryData.address_name + '/' +
      queryData.generation + '/' + queryData.unit + '/' +
      queryData.cap1 + '/' + queryData.cap2 + '/';

    // const logStart = Logger.getTimestamp();
    const controller = new AbortController();
    const { signal } = controller;
    dispatch(requestSolarDataStarted());

    return SupersetClient.post({
      url,
      postPayload: { form_data: queryData },
      signal,
      timeout: timeout * 1000,
    })
      .then(({ json }) => dispatch(requestSolarDataSucceeded(json)))
      // dispatch(addSuccessToast(t('Request confirmed! An email has been sent to you.')));
      .catch(() => {
        dispatch(requestSolarDataFailed());
        dispatch(addDangerToast(t('Request failed.')));
      });
  };
}

export const START_TRIAL_START = 'START_TRIAL_START';
export function startTrialStart() {
  return { type: START_TRIAL_START };
}

export const START_TRIAL_SUCCESS = 'START_TRIAL_SUCCESS';
export function startTrialSuccess(res) {
  return { type: START_TRIAL_SUCCESS, res };
}

export const START_TRIAL_FAIL = 'START_TRIAL_FAIL';
export function startTrialFail() {
  return { type: START_TRIAL_FAIL };
}

export function startTrial(timeout = 60) {
  return (dispatch) => {
    const url = '/billing/start_trial/';
    const controller = new AbortController();
    const { signal } = controller;
    dispatch(startTrialStart());

    return SupersetClient.post({
      url,
      postPayload: {},
      signal,
      timeout: timeout * 1000,
    })
      .then(({ json }) => {
        dispatch(startTrialSuccess(json));
        dispatch(addSuccessToastAction(t(json.msg)));
      })
      .catch(response =>
        getClientErrorObject(response).then(({ error }) => {
          dispatch(startTrialFail());
          dispatch(addDangerToast(t(error)));
        }),
      );
  };
}
