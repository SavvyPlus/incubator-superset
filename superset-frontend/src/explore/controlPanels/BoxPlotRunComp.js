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
import * as v from '../validators';
import {
  formatSelectOptionsForRange,
  formatSelectOptions,
} from '../../modules/utils';

export default {
  controlPanelSections: [
    {
      label: t('Empower'),
      expanded: true,
      controlSetRows: [
        ['metrics'],
        ['adhoc_filters'],
        ['groupby'],
        [
          {
            name: 'data_type_picker',
            config: {
              type: 'SelectControl',
              multi: false,
              label: t('Data Type'),
              validator: [validateNonEmpty],
              default: 'SpotPrice',
              description: t('Select one data type'),
              choices: [
                ['SpotPrice', 'Spot Price'],
                ['LGCPrice', 'LGC Price'],
                ['ForwardPrice', 'Forward Price'],
                // ['Generation', 'Generation'],
                // ['Revenue', 'Revenue'],
              ],
            },
          },
        ],
        [
          {
            name: 'run_picker',
            config: {
              type: 'SelectControl',
              multi: true,
              label: t('Select Senarios'),
              validators: [validateNonEmpty, v.noLongerThan3],
              default: ['Base Case'],
              description: t('Select up to 3 run senarios'),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.scenarios),
              }),
            },
          },
        ],
        [
          {
            name: 'percentile_picker',
            config: {
              type: 'SelectControl',
              multi: false,
              label: t('Select Percentile'),
              default: '100',
              description: t('Select the percentile you want to drill down'),
              choices: [
                ['100', 'All'],
                ['75', '75-100'],
                ['50', '50-75'],
                ['25', '25-50'],
                ['0', '0-25'],
              ],
            },
          },
        ],
        [
          {
            name: 'state_picker',
            config: {
              type: 'SelectControl',
              multi: true,
              label: t('Select State'),
              default: ['VIC'],
              description: t('Select states'),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.states),
              }),
            },
          },
        ],
        [
          {
            name: 'period_type',
            config: {
              type: 'SelectControl',
              freeForm: false,
              label: t('Period type'),
              validators: [],
              default: 'CalYear',
              choices: formatSelectOptions(['CalYear', 'FinYear']),
              description: t('Select the period type'),
            },
          },
        ],
        [
          {
            name: 'cal_years',
            config: {
              type: 'SelectControl',
              validators: [validateNonEmpty, v.noLongerThan20],
              freeForm: true,
              multi: true,
              default: ['2020'],
              label: t('Calendar years'),
              // choices: formatSelectOptionsForRange(2019, 2023),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.cal_year),
              }),
              description: t('Select calendar years'),
            },
          },
        ],
        [
          {
            name: 'fin_years',
            config: {
              type: 'SelectControl',
              validators: [validateNonEmpty],
              freeForm: true,
              multi: true,
              default: ['2020'],
              label: t('Financial years'),
              choices: formatSelectOptionsForRange(2018, 2022),
              description: t('Select financial years'),
            },
          },
        ],
        [
          {
            name: 'whisker_options',
            config: {
              type: 'SelectControl',
              freeForm: true,
              label: t('Whisker/outlier options'),
              default: 'Min/max (no outliers)',
              description: t(
                'Determines how whiskers and outliers are calculated.',
              ),
              choices: formatSelectOptions([
                'Tukey',
                'Min/max (no outliers)',
                '2/98 percentiles',
                '9/91 percentiles',
              ]),
            },
          },
        ],
      ],
    },
  ],
};
