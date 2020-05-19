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

export function prepareBoxplotData(data) {
  const boxData = [];
  const outliers = [];
  const axisData = [];
  for (let i = 0; i < data.length; i++) {
    const { values, label } = data[i];
    boxData.push([
      values.whisker_low,
      values.Q1,
      values.Q2,
      values.Q3,
      values.whisker_high,
    ]);
    axisData.push(label);
  }
  return {
    boxData,
    outliers,
    axisData,
  };
}

export function formatter(param) {
  return [
    'Experiment ' + param.name + ': ',
    'upper: ' + param.data[0],
    'Q1: ' + param.data[1],
    'median: ' + param.data[2],
    'Q3: ' + param.data[3],
    'lower: ' + param.data[4],
  ].join('<br/>');
}
