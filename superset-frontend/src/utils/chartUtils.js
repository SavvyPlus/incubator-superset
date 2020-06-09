/* eslint-disable camelcase */
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

// Round integers to nearest multiple of 10
function RoundUp(toRound) {
  if (toRound % 10 === 0) return toRound;
  return 10 - (toRound % 10) + toRound;
}

function maxBoxData(data) {
  // Map all boxData to a 2D array
  const boxData2DArr = [].concat(...data.map(d => d.boxData));
  // Get an array with each row's maximum value
  const maxRow = boxData2DArr.map(function (row) {
    return Math.max(...row);
  });
  // Get the maximum box data
  const max = Math.max(...maxRow);
  return max;
}

function getBoxPlotYMax(allBoxData) {
  return RoundUp(maxBoxData(allBoxData));
}

export function boxplotFormatter(param) {
  return [
    'Whiker Type: <strong>Min/Max</strong>',
    'Region: <strong>' + param.seriesName + '</strong>',
    'Period: <strong>' + param.name + '</strong>',
    'Minimum: <strong>' + param.data[1].toFixed(2) + '</strong>',
    'Q1: <strong>' + param.data[2].toFixed(2) + '</strong>',
    'Median: <strong>' + param.data[3].toFixed(2) + '</strong>',
    'Q3: <strong>' + param.data[4].toFixed(2) + '</strong>',
    'Maximum: <strong>' + param.data[5].toFixed(2) + '</strong>',
  ].join('<br/>');
}

function barPropFormatter(param) {
  return [
    'Period: <strong>' + param.name + '</strong>',
    'Price Bucket: <strong>' + param.seriesName + '</strong>',
    'Percentage: <strong>' +
      param.value.toFixed(2) +
      ' (' +
      (param.value * 100).toFixed(2) +
      '%)</strong>',
  ].join('<br/>');
}

function barValueFormatter(param) {
  return [
    'Period: <strong>' + param.name + '</strong>',
    'Price Bucket: <strong>' + param.seriesName + '</strong>',
    'BucketSum: <strong>$' + Math.round(param.value) + '</strong>',
  ].join('<br/>');
}

export function getOption(queryResponse) {
  const { viz_type } = queryResponse.form_data;
  if (viz_type === 'multi_boxplot') {
    const queryData = queryResponse.data;
    const regions = Object.keys(queryData);
    const data = Object.values(queryData);
    const yMax = getBoxPlotYMax(data);

    return {
      title: {
        text: queryResponse.query.includes('SpotPrice')
          ? 'Spot Price Forecast'
          : '$300/MWh Cap Payout',
        left: 'center',
      },
      legend: {
        top: '10%',
        data: regions,
        selected: {
          TAS: false,
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
          formatter: '{value}',
        },
        splitLine: {
          show: false,
        },
      },
      yAxis: {
        type: 'value',
        name: 'Nominal $/MWh',
        nameLocation: 'middle',
        nameGap: 25,
        min: 0,
        max: yMax,
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
      series: data.map((d, i) => ({
        name: regions[i],
        type: 'boxplot',
        data: d.boxData,
        tooltip: { formatter: boxplotFormatter },
      })),
    };
  } else if (viz_type === 'spot_price_histogram') {
    const { chart_type, state, data } = queryResponse.data;
    const legendData = data.map(d => d.priceBin);
    const xAxisData = data[0].labels;
    return {
      tooltip: {
        formatter:
          chart_type === 'value' ? barValueFormatter : barPropFormatter,
      },
      legend: {
        data: legendData,
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
        name: chart_type === 'value' ? 'BucketSum' : 'Percentage',
        nameLocation: 'middle',
        nameGap: 45,
        axisLabel: {
          formatter:
            chart_type === 'value'
              ? value => '$' + value / Math.pow(10, 6) + 'M'
              : value => value * 100 + '%',
        },
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
      },
      series: data.map(d => ({
        name: d.priceBin,
        type: 'bar',
        stack: 'SpotPrice',
        label: {
          show: false,
          // position: 'inside',
          // formatter: '${c}',
        },
        data: d.values,
      })),
    };
  }
  return {};
}
