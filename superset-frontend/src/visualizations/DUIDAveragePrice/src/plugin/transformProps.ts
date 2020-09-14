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
import { ChartProps, DataRecord } from '@superset-ui/core';
import {
  transformData,
  getPeriods,
  boxplotFormatter,
  yAxisLabelFormatter,
} from '../utils';

export type DuidAveragePriceDatum = DataRecord;

export default function transformProps(chartProps: ChartProps) {
  /**
   * This function is called after a successful response has been
   * received from the chart data endpoint, and is used to transform
   * the incoming data prior to being sent to the Visualization.
   *
   * The transformProps function is also quite useful to return
   * additional/modified props to your data viz component. The formData
   * can also be accessed from your DuidAveragePrice.tsx file, but
   * doing supplying custom props here is often handy for integrating third
   * party libraries that rely on specific props.
   *
   * A description of properties in `chartProps`:
   * - `height`, `width`: the height/width of the DOM element in which
   *   the chart is located
   * - `formData`: the chart data request payload that was sent to the
   *   backend.
   * - `queryData`: the chart data response payload that was received
   *   from the backend. Some notable properties of `queryData`:
   *   - `data`: an array with data, each row with an object mapping
   *     the column/alias to its value. Example:
   *     `[{ col1: 'abc', metric1: 10 }, { col1: 'xyz', metric1: 20 }]`
   *   - `rowcount`: the number of rows in `data`
   *   - `query`: the query that was issued.
   *
   * Please note: the transformProps function gets cached when the
   * application loads. When making changes to the `transformProps`
   * function during development with hot reloading, changes won't
   * be seen until restarting the development server.
   */
  const { width, height, queryData } = chartProps;
  const data = queryData.data as DuidAveragePriceDatum[];

  // console.log('formData via TransformProps.ts', formData);
  // console.log(queryData);
  const transformedData = transformData(data);
  const periods = getPeriods(data);
  const keys = transformedData.map(entry => entry.duid);

  const echartOptions = {
    // title: {
    //   text: 'Spot Price Forecast',
    //   left: 'center',
    //   textStyle: {
    //     fontSize: 30,
    //   },
    // },
    legend: {
      top: '2%',
      data: keys,
      textStyle: {
        fontSize: 16,
      },
    },
    // toolbox: {
    //   feature: {
    //     saveAsImage: {
    //       title: 'Save as image',
    //     },
    //   },
    // },
    tooltip: {
      trigger: 'item',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '10%',
      top: '10%',
      right: '10%',
      bottom: '10%',
    },
    xAxis: {
      type: 'category',
      data: periods,
      boundaryGap: true,
      nameGap: 30,
      splitArea: {
        show: true,
      },
      axisLabel: {
        formatter: '{value}',
        fontSize: 16,
      },
      splitLine: {
        show: false,
      },
    },
    yAxis: {
      type: 'value',
      name: '$/MWh',
      nameLocation: 'middle',
      nameTextStyle: {
        fontSize: 16,
        fontWeight: 'bold',
      },
      nameGap: 60,
      boundaryGap: [0, '5%'],
      splitArea: {
        show: false,
      },
      axisLabel: {
        fontSize: 16,
        formatter: yAxisLabelFormatter,
      },
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        show: true,
        height: 20,
        type: 'slider',
        top: '95%',
        xAxisIndex: [0],
        start: 0,
        end: 20,
      },
    ],
    series: transformedData.map(d => ({
      name: d.duid,
      type: 'boxplot',
      data: d.values,
      tooltip: { formatter: boxplotFormatter },
      // itemStyle: {
      //   borderColor: REGION_BORDER_COLOR[regions[i]],
      // },
    })),
  };

  // console.log(echartOptions);

  return {
    width,
    height,
    data,
    echartOptions,
  };
}
