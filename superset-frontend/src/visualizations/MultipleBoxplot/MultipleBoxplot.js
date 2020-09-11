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
import { t, ChartMetadata } from '@superset-ui/core';
import { LegacyBoxPlotChartPlugin } from '@superset-ui/preset-chart-xy';
import thumbnail from './images/boxplot-multi.jpg';

const metadata = new ChartMetadata({
  name: t('Multiple Boxplot'),
  description: 'Multiple grouped boxplot for Empower',
  thumbnail,
  useLegacyApi: true,
});

export default class MultipleBoxplot extends LegacyBoxPlotChartPlugin {
  constructor() {
    super();
    this.metadata = metadata;
  }
}
