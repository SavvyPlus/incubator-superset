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
    const formData = new FormData();
    formData.append(files[0].path, files[0]);

    return SupersetClient.post({
      endpoint: '/edit-assumption/upload-csv/',
      postPayload: {
        table,
        note,
        file: formData,
      },
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
