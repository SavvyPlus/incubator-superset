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
import { formatSelectOptions } from '../../modules/utils';

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
        [
          {
            name: 'fin_scenario_picker',
            config: {
              type: 'SelectControl',
              multi: true,
              label: t('Scenario'),
              default: null,
              description: t('Select one scenario'),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.fin_scenarios),
              }),
            },
          },
        ],
        [
          {
            name: 'fin_firm_tech_picker',
            config: {
              type: 'SelectControl',
              multi: false,
              label: t('Firming Technology'),
              default: null,
              description: t('Select one firming technology'),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.fin_firm_techs),
              }),
            },
          },
        ],
        [
          {
            name: 'fin_strategy_picker',
            config: {
              type: 'SelectControl',
              multi: true,
              label: t('Strategy'),
              default: null,
              description: t('Select Strategy'),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.fin_strategy),
              }),
            },
          },
        ],
        [
          {
            name: 'fin_period_picker',
            config: {
              type: 'SelectControl',
              multi: true,
              label: t('Period'),
              default: null,
              description: t('Select one period'),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.fin_periods),
              }),
            },
          },
        ],
        [
          {
            name: 'fin_str_metric_picker',
            config: {
              type: 'SelectControl',
              multi: true,
              label: t('Metric'),
              default: null,
              validators: [validateNonEmpty, v.onlyContainsROI],
              description: t('Select metric'),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.fin_metric),
              }),
            },
          },
        ],
        [
          {
            name: 'fin_str_tech_picker',
            config: {
              type: 'SelectControl',
              multi: false,
              label: t('Technology'),
              default: null,
              validators: [validateNonEmpty],
              description: t('Select one technology'),
              mapStateToProps: state => ({
                choices: formatSelectOptions(state.fin_techs),
              }),
            },
          },
        ],
      ],
    },
  ],
};
