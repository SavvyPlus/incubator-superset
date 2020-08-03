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
  SET_REGION,
  SET_FUEL,
  SET_VERSION,
  SET_ISP,
  SET_SCENARIO,
  FETCH_CHART_DATA_SUCCESS,
  FETCH_CHART_DATA_FAILED,
} from '../actions/comparison';

export default function comparisonReducer(state = {}, action) {
  const actionHandlers = {
    [SET_REGION]() {
      return { ...state, region: action.region };
    },
    [SET_FUEL]() {
      return { ...state, fuel: action.fuel };
    },
    [SET_VERSION]() {
      return { ...state, version: action.version };
    },
    [SET_ISP]() {
      return { ...state, isp: action.isp };
    },
    [SET_SCENARIO]() {
      return { ...state, scenario: action.scenario };
    },
    [FETCH_CHART_DATA_SUCCESS]() {
      return {
        ...state,
        data: action.res.data,
        years: action.res.years,
      };
    },
    [FETCH_CHART_DATA_FAILED]() {
      return { ...state };
    },
  };

  if (action.type in actionHandlers) {
    return actionHandlers[action.type]();
  }
  return state;
}
