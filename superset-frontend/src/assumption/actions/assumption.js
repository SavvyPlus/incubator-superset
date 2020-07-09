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
import {
  addSuccessToast,
  addWarningToast,
  addDangerToast,
} from '../../messageToasts/actions';

export const SET_UPSERT = 'SET_UPSERT';
export function setUpsert(upsert) {
  return { type: SET_UPSERT, upsert };
}

export const SET_TABLE = 'SET_TABLE';
export function setTable(table) {
  return { type: SET_TABLE, table };
}

export const SET_VERSION = 'SET_VERSION';
export function setVersion(version) {
  return { type: SET_VERSION, version };
}

export const UPLOAD_FILE_SUCCESS = 'UPLOAD_FILE_SUCCESS';
export function uploadFileSuccess(data) {
  return { type: UPLOAD_FILE_SUCCESS, data };
}

export const UPLOAD_FILE_FAILED = 'UPLOAD_FILE_FAILED';
export function uploadFileFailed(error) {
  return { type: UPLOAD_FILE_FAILED, error };
}

export function uploadFile(table, note, files) {
  return dispatch => {
    return SupersetClient.post({
      endpoint: '/edit-assumption/upload-csv/',
      postPayload: {
        table,
        note,
        file: files[0],
      },
      stringify: false,
    })
      .then(({ json }) => {
        dispatch(uploadFileSuccess(json));
        dispatch(addSuccessToast(t('File was uploaded successfully.')));
      })
      .catch(() => {
        dispatch(uploadFileFailed());
        dispatch(
          addDangerToast(t('Sorry, there was an error uploading this file')),
        );
      });
  };
}

export const FETCH_TABLE_VERSIONS_STARTED = 'FETCH_TABLE_VERSIONS_STARTED';
export function fetchTableVersionsStarted() {
  return { type: FETCH_TABLE_VERSIONS_STARTED };
}

export const FETCH_TABLE_VERSIONS_SUCCESS = 'FETCH_TABLE_VERSIONS_SUCCESS';
export function fetchTableVersionsSuccess(versions) {
  return { type: FETCH_TABLE_VERSIONS_SUCCESS, versions };
}

export const FETCH_TABLE_VERSIONS_FAILED = 'FETCH_TABLE_VERSIONS_FAILED';
export function fetchTableVersionsFailed() {
  return { type: FETCH_TABLE_VERSIONS_FAILED };
}

export function fetchTableVersions(table) {
  return dispatch => {
    dispatch(fetchTableVersionsStarted());
    return SupersetClient.get({
      endpoint: `/edit-assumption/get-data/${table}/version/na`,
    })
      .then(({ json }) => {
        dispatch(fetchTableVersionsSuccess(json.versions));
      })
      .catch(() => {
        dispatch(fetchTableVersionsFailed());
        dispatch(
          addDangerToast(
            t('Sorry, there was an error updating table versions'),
          ),
        );
      });
  };
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
        console.log(json);
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

export const SAVE_TABLE_DATA_SUCESS = 'SAVE_TABLE_DATA_SUCESS';
export function saveTableDataSuccess(data) {
  return { type: SAVE_TABLE_DATA_SUCESS, data };
}

export const SAVE_TABLE_DATA_FAILED = 'SAVE_TABLE_DATA_FAILED';
export function saveTableDataFailed() {
  return { type: SAVE_TABLE_DATA_FAILED };
}

export function saveTableData(table, note, files) {
  return dispatch => {
    return SupersetClient.post({
      endpoint: '/edit-assumption/upload-csv/',
      postPayload: {
        table,
        note,
        file: files[0],
      },
      stringify: false,
    })
      .then(({ json }) => {
        dispatch(saveTableDataSuccess(json));
        dispatch(addSuccessToast(t('File was uploaded successfully.')));
      })
      .catch(() => {
        dispatch(saveTableDataFailed());
        dispatch(
          addDangerToast(t('Sorry, there was an error uploading this file')),
        );
      });
  };
}
