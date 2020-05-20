/* eslint-disable no-template-curly-in-string */
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
import { prepareBoxplotData } from 'echarts/extension/dataTool';

// export function prepareBoxplotData(data) {
//   const boxData = [];
//   const outliers = [];
//   const axisData = [];
//   for (let i = 0; i < data.length; i++) {
//     const { values, label } = data[i];
//     boxData.push([
//       values.whisker_low,
//       values.Q1,
//       values.Q2,
//       values.Q3,
//       values.whisker_high,
//     ]);
//     axisData.push(label);
//   }
//   return {
//     boxData,
//     outliers,
//     axisData,
//   };
// }

export function formatter(param) {
  return [
    'Whiker Type: Min/Max',
    'Region: ' + param.name,
    'Minimum: ' + param.data[1],
    'Q1: ' + param.data[2],
    'Median: ' + param.data[3],
    'Q3: ' + param.data[4],
    'Maximum: ' + param.data[5],
  ].join('<br/>');
}

export function getOption(queryResponse) {
  if (queryResponse.form_data.viz_type === 'box_plot_300_cap') {
    console.log(JSON. stringify(queryResponse.data))
    // const data = prepareBoxplotData(queryResponse.data);
    const data = [];
    for (let seriesIndex = 0; seriesIndex < 3; seriesIndex++) {
      const seriesData = [];
      for (let i = 0; i < 18; i++) {
        const cate = [];
        for (let j = 0; j < 100; j++) {
          cate.push(Math.random() * 200);
        }
        seriesData.push(cate);
      }
      data.push(prepareBoxplotData(seriesData));
    }
    return {
      title: {
        text: '$300/MWh Cap Payout',
        left: 'center',
      },
      legend: {
        top: '10%',
        data: ['NSW', 'VIC', 'QLD'],
        selected: {
          NSW: true,
          VIC: false,
          QLD: false,
        },
      },
      toolbox: {
        feature: {
          saveAsImage: {
            title: 'Save as image',
          },
        },
      },
      tooltip: {
        trigger: 'item',
        axisPointer: {
          type: 'shadow',
        },
      },
      grid: {
        left: '10%',
        top: '20%',
        right: '10%',
        bottom: '15%',
      },
      xAxis: {
        type: 'category',
        data: data[0].axisData,
        boundaryGap: true,
        nameGap: 30,
        splitArea: {
          show: true,
        },
        axisLabel: {
          formatter: 'Cal-{value}',
        },
        splitLine: {
          show: false,
        },
      },
      yAxis: {
        type: 'value',
        name: 'Value',
        min: -200,
        max: 400,
        splitArea: {
          show: false,
        },
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 20,
        },
        {
          show: true,
          height: 20,
          type: 'slider',
          top: '90%',
          xAxisIndex: [0],
          start: 0,
          end: 20,
        },
      ],
      series: [
        {
          name: 'NSW',
          type: 'boxplot',
          data: data[0].boxData,
          tooltip: { formatter },
        },
        {
          name: 'VIC',
          type: 'boxplot',
          data: data[1].boxData,
          tooltip: { formatter },
        },
        {
          name: 'QLD',
          type: 'boxplot',
          data: data[2].boxData,
          tooltip: { formatter },
        },
      ],
    };
  } else if (queryResponse.form_data.viz_type === 'spot_price_histogram') {
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: [
          '1.Below zero',
          '2.Zero to $25/MWh',
          '3.$25/MWh to $50/MWh',
          '4.$50/MWh to $100/MWh',
          '5.$100/MWh to $300/MWh',
        ],
      },
      toolbox: {
        feature: {
          saveAsImage: {
            title: 'Save as image',
          },
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      yAxis: {
        type: 'value',
      },
      xAxis: {
        type: 'category',
        data: [
          'Cal-20',
          'Cal-21',
          'Cal-22',
          'Cal-23',
          'Cal-24',
          'Cal-25',
          'Cal-26',
        ],
      },
      series: [
        {
          name: '1.Below zero',
          type: 'bar',
          stack: 'SpotPrice',
          label: {
            show: true,
            position: 'inside',
            formatter: '${c}',
          },
          data: [320, 302, 301, 334, 390, 330, 320],
        },
        {
          name: '2.Zero to $25/MWh',
          type: 'bar',
          stack: 'SpotPrice',
          label: {
            show: true,
            position: 'inside',
            formatter: '${c}',
          },
          data: [120, 132, 101, 134, 90, 230, 210],
        },
        {
          name: '3.$25/MWh to $50/MWh',
          type: 'bar',
          stack: 'SpotPrice',
          label: {
            show: true,
            position: 'inside',
            formatter: '${c}',
          },
          data: [220, 182, 191, 234, 290, 330, 310],
        },
        {
          name: '4.$50/MWh to $100/MWh',
          type: 'bar',
          stack: 'SpotPrice',
          label: {
            show: true,
            position: 'inside',
            formatter: '${c}',
          },
          data: [150, 212, 201, 154, 190, 330, 410],
        },
        {
          name: '5.$100/MWh to $300/MWh',
          type: 'bar',
          stack: 'SpotPrice',
          label: {
            show: true,
            position: 'inside',
            formatter: '${c}',
          },
          data: [820, 832, 901, 934, 1290, 1330, 1320],
        },
      ],
    };
  }
  return {};
}
