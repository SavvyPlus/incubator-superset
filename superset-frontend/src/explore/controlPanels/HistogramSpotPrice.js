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
import { t, validateNonEmpty } from '@superset-ui/core';
import {
  periodTypeStaticPicker,
  periodFinyearPicker,
  periodCalyearPicker,
  periodQuarterlyPicker,
} from './Shared_Empower';

export default {
  controlPanelSections: [
    {
      label: t('Empower'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'spot_hist_chart_type_picker',
            config: {
              type: 'SelectControl',
              multi: false,
              label: t('Chart Type'),
              default: 'value',
              validators: [validateNonEmpty],
              choices: [
                ['value', 'Spot Price Value Annual'],
                ['percent', 'Spot Price Proportion Annual'],
              ],
            },
          },
        ],
        [
          {
            name: 'state_static_picker',
            config: {
              type: 'SelectControl',
              multi: false,
              label: t('Region'),
              default: ['VIC'],
              validators: [validateNonEmpty],
              choices: [
                ['NSW1', 'NSW'],
                ['VIC1', 'VIC'],
                ['QLD1', 'QLD'],
                ['TAS1', 'TAS'],
                ['SA1', 'SA'],
              ],
            },
          },
        ],
        [periodTypeStaticPicker],
        [periodFinyearPicker],
        [periodCalyearPicker],
        [periodQuarterlyPicker],
      ],
    },
  ],
};
