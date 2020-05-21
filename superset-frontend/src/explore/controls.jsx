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
/**
 * This file exports all controls available for use in the different visualization types
 *
 * While the React components located in `controls/components` represent different
 * types of controls (CheckboxControl, SelectControl, TextControl, ...), the controls here
 * represent instances of control types, that can be reused across visualization types.
 *
 * When controls are reused across viz types, their values are carried over as a user
 * changes the chart types.
 *
 * While the keys defined in the control itself get passed to the controlType as props,
 * here's a list of the keys that are common to all controls, and as a result define the
 * control interface:
 *
 * - type: the control type, referencing a React component of the same name
 * - label: the label as shown in the control's header
 * - description: shown in the info tooltip of the control's header
 * - default: the default value when opening a new chart, or changing visualization type
 * - renderTrigger: a bool that defines whether the visualization should be re-rendered
     when changed. This should `true` for controls that only affect the rendering (client side)
     and don't affect the query or backend data processing as those require to re run a query
     and fetch the data
 * - validators: an array of functions that will receive the value of the component and
     should return error messages when the value is not valid. The error message gets
     bubbled up to the control header, section header and query panel header.
 * - warning: text shown as a tooltip on a warning icon in the control's header
 * - error: text shown as a tooltip on a error icon in the control's header
 * - mapStateToProps: a function that receives the App's state and return an object of k/v
     to overwrite configuration at runtime. This is useful to alter a component based on
     anything external to it, like another control's value. For instance it's possible to
     show a warning based on the value of another component. It's also possible to bind
     arbitrary data from the redux store to the component this way.
 * - tabOverride: set to 'data' if you want to force a renderTrigger to show up on the `Data`
     tab, otherwise `renderTrigger: true` components will show up on the `Style` tab.
 *
 * Note that the keys defined in controls in this file that are not listed above represent
 * props specific for the React component defined as `type`. Also note that this module work
 * in tandem with `controlPanels/index.js` that defines how controls are composed into sections for
 * each and every visualization type.
 */
import React from 'react';
import { t } from '@superset-ui/translation';
import {
  getCategoricalSchemeRegistry,
  getSequentialSchemeRegistry,
} from '@superset-ui/color';
import {
  legacyValidateInteger,
  validateNonEmpty,
} from '@superset-ui/validator';

import * as v from './validators';

import {
  formatSelectOptionsForRange,
  formatSelectOptions,
  mainMetric,
} from '../modules/utils';
import ColumnOption from '../components/ColumnOption';
import { TIME_FILTER_LABELS } from './constants';

const categoricalSchemeRegistry = getCategoricalSchemeRegistry();
const sequentialSchemeRegistry = getSequentialSchemeRegistry();

export const PRIMARY_COLOR = { r: 0, g: 122, b: 135, a: 1 };

// input choices & options
export const D3_FORMAT_OPTIONS = [
  ['SMART_NUMBER', 'Adaptative formating'],
  ['~g', 'Original value'],
  [',d', ',d (12345.432 => 12,345)'],
  ['.1s', '.1s (12345.432 => 10k)'],
  ['.3s', '.3s (12345.432 => 12.3k)'],
  [',.1%', ',.1% (12345.432 => 1,234,543.2%)'],
  ['.3%', '.3% (12345.432 => 1234543.200%)'],
  ['.4r', '.4r (12345.432 => 12350)'],
  [',.3f', ',.3f (12345.432 => 12,345.432)'],
  ['+,', '+, (12345.432 => +12,345.432)'],
  ['$,.2f', '$,.2f (12345.432 => $12,345.43)'],
  ['DURATION', 'Duration in ms (66000 => 1m 6s)'],
  ['DURATION_SUB', 'Duration in ms (100.40008 => 100ms 400µs 80ns)'],
];

const ROW_LIMIT_OPTIONS = [10, 50, 100, 250, 500, 1000, 5000, 10000, 50000];

const SERIES_LIMITS = [0, 5, 10, 25, 50, 100, 500];

export const D3_FORMAT_DOCS =
  'D3 format syntax: https://github.com/d3/d3-format';

export const D3_TIME_FORMAT_OPTIONS = [
  ['smart_date', 'Adaptative formating'],
  ['%d/%m/%Y', '%d/%m/%Y | 14/01/2019'],
  ['%m/%d/%Y', '%m/%d/%Y | 01/14/2019'],
  ['%Y-%m-%d', '%Y-%m-%d | 2019-01-14'],
  ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S | 2019-01-14 01:32:10'],
  ['%d-%m-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S | 14-01-2019 01:32:10'],
  ['%H:%M:%S', '%H:%M:%S | 01:32:10'],
];

const timeColumnOption = {
  verbose_name: 'Time',
  column_name: '__timestamp',
  description: t(
    'A reference to the [Time] configuration, taking granularity into ' +
      'account',
  ),
};

const groupByControl = {
  type: 'SelectControl',
  controlGroup: 'groupby',
  multi: true,
  freeForm: true,
  label: t('Group by'),
  default: [],
  includeTime: false,
  description: t('One or many controls to group by'),
  optionRenderer: c => <ColumnOption column={c} showType />,
  valueRenderer: c => <ColumnOption column={c} />,
  valueKey: 'column_name',
  allowAll: true,
  filterOption: (opt, text) =>
    (opt.column_name &&
      opt.column_name.toLowerCase().indexOf(text.toLowerCase()) >= 0) ||
    (opt.verbose_name &&
      opt.verbose_name.toLowerCase().indexOf(text.toLowerCase()) >= 0),
  promptTextCreator: label => label,
  mapStateToProps: (state, control) => {
    const newState = {};
    if (state.datasource) {
      newState.options = state.datasource.columns.filter(c => c.groupby);
      if (control && control.includeTime) {
        newState.options.push(timeColumnOption);
      }
    }
    return newState;
  },
  commaChoosesOption: false,
};

const metrics = {
  type: 'MetricsControl',
  controlGroup: 'metrics',
  multi: true,
  label: t('Metrics'),
  validators: [validateNonEmpty],
  default: c => {
    const metric = mainMetric(c.savedMetrics);
    return metric ? [metric] : null;
  },
  mapStateToProps: state => {
    const datasource = state.datasource;
    return {
      columns: datasource ? datasource.columns : [],
      savedMetrics: datasource ? datasource.metrics : [],
      datasourceType: datasource && datasource.type,
    };
  },
  description: t('One or many metrics to display'),
};
const metric = {
  ...metrics,
  multi: false,
  label: t('Metric'),
  description: t('Metric'),
  default: props => mainMetric(props.savedMetrics),
};

export function columnChoices(datasource) {
  if (datasource && datasource.columns) {
    return datasource.columns
      .map(col => [col.column_name, col.verbose_name || col.column_name])
      .sort((opt1, opt2) =>
        opt1[1].toLowerCase() > opt2[1].toLowerCase() ? 1 : -1,
      );
  }
  return [];
}

export const controls = {
  metrics,

  metric,

  datasource: {
    type: 'DatasourceControl',
    label: t('Datasource'),
    default: null,
    description: null,
    mapStateToProps: (state, control, actions) => ({
      datasource: state.datasource,
      onDatasourceSave: actions ? actions.setDatasource : () => {},
    }),
  },

  viz_type: {
    type: 'VizTypeControl',
    label: t('Visualization Type'),
    default: 'table',
    description: t('The type of visualization to display'),
  },

  y_axis_bounds: {
    type: 'BoundsControl',
    label: t('Y Axis Bounds'),
    renderTrigger: true,
    default: [null, null],
    description: t(
      'Bounds for the Y-axis. When left empty, the bounds are ' +
        'dynamically defined based on the min/max of the data. Note that ' +
        "this feature will only expand the axis range. It won't " +
        "narrow the data's extent.",
    ),
  },

  order_by_cols: {
    type: 'SelectControl',
    multi: true,
    label: t('Ordering'),
    default: [],
    description: t('One or many metrics to display'),
    mapStateToProps: state => ({
      choices: state.datasource ? state.datasource.order_by_choices : [],
    }),
  },

  data_type_picker: {
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

  run_picker: {
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

  percentile_picker: {
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

  state_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Select State'),
    default: ['VIC'],
    description: t('Select states'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.states),
    }),
  },

  state_static_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Region'),
    default: ['VIC'],
    choices: [
      ['NSW1', 'NSW'],
      ['VIC1', 'VIC'],
      ['QLD1', 'QLD'],
      ['TAS1', 'TAS'],
      ['SA1', 'SA'],
    ],
  },

  spot_hist_chart_type_picker: {
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

  price_bin_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Price Bin'),
    // default: null,
    validators: [validateNonEmpty],
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.price_bins),
    }),
  },

  period_type_static_picker: {
    type: 'SelectControl',
    multi: false,
    label: t('Period Type'),
    default: ['CalYear'],
    validators: [validateNonEmpty],
    choices: formatSelectOptions(['CalYear', 'FinYear', 'Quarterly']),
    // description: t('Select the period type'),
  },

  period_type: {
    type: 'SelectControl',
    freeForm: false,
    label: t('Period type'),
    validators: [],
    default: 'CalYear',
    choices: formatSelectOptions(['CalYear', 'FinYear']),
    description: t('Select the period type'),
  },

  period_calyear_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Period'),
    default: null,
    // description: t('Select states'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.period_calyear),
    }),
  },

  period_finyear_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Period'),
    default: null,
    // description: t('Select states'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.period_finyear),
    }),
  },

  period_quarterly_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Period'),
    default: null,
    // description: t('Select states'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.period_quarterly),
    }),
  },

  cal_years: {
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

  fin_years: {
    type: 'SelectControl',
    validators: [validateNonEmpty],
    freeForm: true,
    multi: true,
    default: ['2020'],
    label: t('Financial years'),
    choices: formatSelectOptionsForRange(2018, 2022),
    description: t('Select financial years'),
  },

  // control for financial charts
  fin_scenario_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Scenario'),
    default: null,
    description: t('Select one scenario'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.fin_scenarios),
    }),
  },

  fin_firm_tech_picker: {
    type: 'SelectControl',
    multi: false,
    label: t('Firming Technology'),
    default: null,
    description: t('Select one firming technology'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.fin_firm_techs),
    }),
  },

  fin_tech_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Technology'),
    default: null,
    description: t('Select multiple technologies'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.fin_techs),
    }),
  },

  fin_period_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Period'),
    default: null,
    description: t('Select one period'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.fin_periods),
    }),
  },

  fin_unit_picker: {
    type: 'SelectControl',
    multi: false,
    label: t('Unit'),
    default: '0',
    validators: [validateNonEmpty],
    description: t('Select unit'),
    choices: [
      ['0', '$'],
      ['1', '$/MWh'],
    ],
  },

  fin_strategy_picker: {
    type: 'SelectControl',
    multi: true,
    label: t('Strategy'),
    default: null,
    description: t('Select Strategy'),
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.fin_strategy),
    }),
  },

  fin_metric_picker: {
    type: 'SelectControl',
    multi: false,
    label: t('Metric'),
    default: 'PPA CFD',
    validators: [validateNonEmpty],
    description: t('Select metric'),
    choices: [
      ['PPA CFD', 'PPA CFD'],
      ['MW Sold CFD', 'MW Sold CFD'],
      ['Non-Firming Contribution Margin', 'Non-Firming Contribution Margin'],
      ['Contribution Margin', 'Contribution Margin'],
      ['Fixed O&M', 'Fixed O&M'],
      ['EBIT', 'EBIT'],
      ['EBIT (Discounted)', 'EBIT (Discounted)'],
      ['Capital Expenditure', 'Capital Expenditure'],
      ['Terminal Value (Discounted)', 'Terminal Value (Discounted)'],
      ['Net Present Value', 'Net Present Value'],
      ['PPA CFD (Annually)', 'PPA CFD (Annually)'],
      ['MW Sold CFD (Annually)', 'MW Sold CFD (Annually)'],
    ],
  },

  fin_str_metric_picker: {
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

  fin_str_tech_picker: {
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

  color_picker: {
    label: t('Fixed Color'),
    description: t('Use this to define a static color for all circles'),
    type: 'ColorPickerControl',
    default: PRIMARY_COLOR,
    renderTrigger: true,
  },

  metric_2: {
    ...metric,
    label: t('Right Axis Metric'),
    clearable: true,
    description: t('Choose a metric for right axis'),
  },

  linear_color_scheme: {
    type: 'ColorSchemeControl',
    label: t('Linear Color Scheme'),
    choices: () =>
      sequentialSchemeRegistry.values().map(value => [value.id, value.label]),
    default: sequentialSchemeRegistry.getDefaultKey(),
    clearable: false,
    description: '',
    renderTrigger: true,
    schemes: () => sequentialSchemeRegistry.getMap(),
    isLinear: true,
  },

  secondary_metric: {
    ...metric,
    label: t('Color Metric'),
    default: null,
    validators: [],
    description: t('A metric to use for color'),
  },

  groupby: groupByControl,

  columns: {
    ...groupByControl,
    label: t('Columns'),
    description: t('One or many controls to pivot as columns'),
  },

  druid_time_origin: {
    type: 'SelectControl',
    freeForm: true,
    label: TIME_FILTER_LABELS.druid_time_origin,
    choices: [
      ['', 'default'],
      ['now', 'now'],
    ],
    default: null,
    description: t(
      'Defines the origin where time buckets start, ' +
        'accepts natural dates as in `now`, `sunday` or `1970-01-01`',
    ),
  },

  granularity: {
    type: 'SelectControl',
    freeForm: true,
    label: TIME_FILTER_LABELS.granularity,
    default: 'one day',
    choices: [
      [null, 'all'],
      ['PT5S', '5 seconds'],
      ['PT30S', '30 seconds'],
      ['PT1M', '1 minute'],
      ['PT5M', '5 minutes'],
      ['PT30M', '30 minutes'],
      ['PT1H', '1 hour'],
      ['PT6H', '6 hour'],
      ['P1D', '1 day'],
      ['P7D', '7 days'],
      ['P1W', 'week'],
      ['week_starting_sunday', 'week starting Sunday'],
      ['week_ending_saturday', 'week ending Saturday'],
      ['P1M', 'month'],
      ['P3M', 'quarter'],
      ['P1Y', 'year'],
    ],
    description: t(
      'The time granularity for the visualization. Note that you ' +
        'can type and use simple natural language as in `10 seconds`, ' +
        '`1 day` or `56 weeks`',
    ),
  },

  granularity_sqla: {
    type: 'SelectControl',
    label: TIME_FILTER_LABELS.granularity_sqla,
    description: t(
      'The time column for the visualization. Note that you ' +
        'can define arbitrary expression that return a DATETIME ' +
        'column in the table. Also note that the ' +
        'filter below is applied against this column or ' +
        'expression',
    ),
    default: control => control.default,
    clearable: false,
    optionRenderer: c => <ColumnOption column={c} showType />,
    valueRenderer: c => <ColumnOption column={c} />,
    valueKey: 'column_name',
    mapStateToProps: state => {
      const props = {};
      if (state.datasource) {
        props.options = state.datasource.columns.filter(c => c.is_dttm);
        props.default = null;
        if (state.datasource.main_dttm_col) {
          props.default = state.datasource.main_dttm_col;
        } else if (props.options && props.options.length > 0) {
          props.default = props.options[0].column_name;
        }
      }
      return props;
    },
  },

  time_grain_sqla: {
    type: 'SelectControl',
    label: TIME_FILTER_LABELS.time_grain_sqla,
    default: 'P1D',
    description: t(
      'The time granularity for the visualization. This ' +
        'applies a date transformation to alter ' +
        'your time column and defines a new time granularity. ' +
        'The options here are defined on a per database ' +
        'engine basis in the Superset source code.',
    ),
    mapStateToProps: state => ({
      choices: state.datasource ? state.datasource.time_grain_sqla : null,
    }),
  },

  time_range: {
    type: 'DateFilterControl',
    freeForm: true,
    label: TIME_FILTER_LABELS.time_range,
    default: t('Last week'), // this value is translated, but the backend wouldn't understand a translated value?
    description: t(
      'The time range for the visualization. All relative times, e.g. "Last month", ' +
        '"Last 7 days", "now", etc. are evaluated on the server using the server\'s ' +
        'local time (sans timezone). All tooltips and placeholder times are expressed ' +
        'in UTC (sans timezone). The timestamps are then evaluated by the database ' +
        "using the engine's local timezone. Note one can explicitly set the timezone " +
        'per the ISO 8601 format if specifying either the start and/or end time.',
    ),
    mapStateToProps: state => ({
      endpoints: state.form_data ? state.form_data.time_range_endpoints : null,
    }),
  },

  time_range_fixed: {
    type: 'CheckboxControl',
    label: t('Fix to selected Time Range'),
    description: t(
      'Fix the trend line to the full time range specified in case filtered results do not include the start or end dates',
    ),
    renderTrigger: true,
    visibility(props) {
      const {
        time_range: timeRange,
        viz_type: vizType,
        show_trend_line: showTrendLine,
      } = props.form_data;
      // only display this option when a time range is selected
      return timeRange && timeRange !== 'No filter';
    },
  },

  max_bubble_size: {
    type: 'SelectControl',
    freeForm: true,
    label: t('Max Bubble Size'),
    default: '25',
    choices: formatSelectOptions(['5', '10', '15', '25', '50', '75', '100']),
  },

  whisker_options: {
    type: 'SelectControl',
    freeForm: true,
    label: t('Whisker/outlier options'),
    default: 'Min/max (no outliers)',
    description: t('Determines how whiskers and outliers are calculated.'),
    choices: formatSelectOptions([
      'Tukey',
      'Min/max (no outliers)',
      '2/98 percentiles',
      '9/91 percentiles',
    ]),
  },

  number_format: {
    type: 'SelectControl',
    freeForm: true,
    label: t('Number format'),
    renderTrigger: true,
    default: 'SMART_NUMBER',
    choices: D3_FORMAT_OPTIONS,
    description: D3_FORMAT_DOCS,
  },

  row_limit: {
    type: 'SelectControl',
    freeForm: true,
    label: t('Row limit'),
    validators: [legacyValidateInteger],
    default: 10000,
    choices: formatSelectOptions(ROW_LIMIT_OPTIONS),
  },

  limit: {
    type: 'SelectControl',
    freeForm: true,
    label: t('Series limit'),
    validators: [legacyValidateInteger],
    choices: formatSelectOptions(SERIES_LIMITS),
    description: t(
      'Limits the number of time series that get displayed. A sub query ' +
        '(or an extra phase where sub queries are not supported) is applied to limit ' +
        'the number of time series that get fetched and displayed. This feature is useful ' +
        'when grouping by high cardinality dimension(s).',
    ),
  },

  quarter: {
    type: 'SelectControl',
    freeForm: false,
    label: t('Quarter'),
    validators: [],
    choices: formatSelectOptions(['Q1', 'Q2', 'Q3', 'Q4', 'All Qtrs']),
    description: t('Select the quarter'),
  },

  timeseries_limit_metric: {
    type: 'MetricsControl',
    label: t('Sort By'),
    default: null,
    description: t('Metric used to define the top series'),
    mapStateToProps: state => ({
      columns: state.datasource ? state.datasource.columns : [],
      savedMetrics: state.datasource ? state.datasource.metrics : [],
      datasourceType: state.datasource && state.datasource.type,
    }),
  },

  series: {
    ...groupByControl,
    label: t('Series'),
    multi: false,
    default: null,
    description: t(
      'Defines the grouping of entities. ' +
        'Each series is shown as a specific color on the chart and ' +
        'has a legend toggle',
    ),
  },

  entity: {
    ...groupByControl,
    label: t('Entity'),
    default: null,
    multi: false,
    validators: [validateNonEmpty],
    description: t('This defines the element to be plotted on the chart'),
  },

  x: {
    ...metric,
    label: t('X Axis'),
    description: t('Metric assigned to the [X] axis'),
    default: null,
  },

  y: {
    ...metric,
    label: t('Y Axis'),
    default: null,
    description: t('Metric assigned to the [Y] axis'),
  },

  size: {
    ...metric,
    label: t('Bubble Size'),
    default: null,
  },

  y_axis_format: {
    type: 'SelectControl',
    freeForm: true,
    label: t('Y Axis Format'),
    renderTrigger: true,
    default: 'SMART_NUMBER',
    choices: D3_FORMAT_OPTIONS,
    description: D3_FORMAT_DOCS,
    mapStateToProps: state => {
      const showWarning =
        state.controls &&
        state.controls.comparison_type &&
        state.controls.comparison_type.value === 'percentage';
      return {
        warning: showWarning
          ? t(
              'When `Calculation type` is set to "Percentage change", the Y ' +
                'Axis Format is forced to `.1%`',
            )
          : null,
        disabled: showWarning,
      };
    },
  },

  adhoc_filters: {
    type: 'AdhocFilterControl',
    label: t('Filters'),
    default: null,
    description: '',
    mapStateToProps: state => ({
      columns: state.datasource
        ? state.datasource.columns.filter(c => c.filterable)
        : [],
      savedMetrics: state.datasource ? state.datasource.metrics : [],
      datasource: state.datasource,
    }),
    provideFormDataToProps: true,
  },

  color_scheme: {
    type: 'ColorSchemeControl',
    label: t('Color Scheme'),
    default: categoricalSchemeRegistry.getDefaultKey(),
    renderTrigger: true,
    choices: () => categoricalSchemeRegistry.keys().map(s => [s, s]),
    description: t('The color scheme for rendering chart'),
    schemes: () => categoricalSchemeRegistry.getMap(),
  },

  label_colors: {
    type: 'ColorMapControl',
    label: t('Color Map'),
    default: {},
    renderTrigger: true,
    mapStateToProps: state => ({
      colorNamespace: state.form_data.color_namespace,
      colorScheme: state.form_data.color_scheme,
    }),
  },
};
export default controls;
