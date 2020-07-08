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
import {
  SET_UPSERT,
  SET_TABLE,
  SET_VERSION,
  UPLOAD_FILE_SUCCESS,
  UPLOAD_FILE_FAILED,
  FETCH_TABLE_VERSIONS_SUCCESS,
} from '../actions/assumption';

export default function assumptionReducer(state = {}, action) {
  const actionHandlers = {
    [SET_UPSERT]() {
      return { ...state, upsert: action.upsert };
    },
    [SET_TABLE]() {
      return { ...state, table: action.table };
    },
    [SET_VERSION]() {
      return { ...state, version: action.version };
    },
    [UPLOAD_FILE_SUCCESS]() {
      return {
        ...state,
        upsert: 'upload',
        table: 'RooftopSolarHistory',
      };
    },
    [UPLOAD_FILE_FAILED]() {
      return {
        ...state,
      };
    },
    [FETCH_TABLE_VERSIONS_SUCCESS]() {
      return {
        ...state,
        versions: action.versions,
      };
    },
  };

  if (action.type in actionHandlers) {
    return actionHandlers[action.type]();
  }
  return state;
}
