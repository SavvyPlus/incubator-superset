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
import React from 'react';
import PropTypes from 'prop-types';
import ReactEcharts from 'echarts-for-react';
import { withStyles } from '@material-ui/core/styles';

const styles = theme => ({
  typography: {
    margin: theme.spacing(2),
    fontSize: 15,
    width: 300,
  },
});

class HeatMap extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      exported: false,
    };

    this.getHeatmapOption = this.getHeatmapOption.bind(this);
    // this.onUnload = this.onUnload.bind(this);
  }

  // componentDidMount() {
  //   window.addEventListener('beforeunload', this.onUnload);
  // }

  // componentWillUnmount() {
  //   window.removeEventListener('beforeunload', this.onUnload);
  // }

  // onUnload(event) { // the method that will be used for both add and remove event
  //   // console.log("hellooww")
  //   // eslint-disable-next-line no-param-reassign
  //   event.returnValue = 'This will go back to search page, are you sure?';
  // }


  getHeatmapOption(data) {
    const months = [
      '7',
      '8',
      '9',
      '10',
      '11',
      '12',
      '1',
      '2',
      '3',
      '4',
      '5',
      '6',
    ];
    const years = ['2018/07\n~\n2019/06'];

    let solarData = [
      [0, 0, Math.round(data[1][0])],
      [0, 1, Math.round(data[1][1])],
      [0, 2, Math.round(data[1][2])],
      [0, 3, Math.round(data[1][3])],
      [0, 4, Math.round(data[1][4])],
      [0, 5, Math.round(data[1][5])],
      [0, 6, Math.round(data[1][6])],
      [0, 7, Math.round(data[1][7])],
      [0, 8, Math.round(data[1][8])],
      [0, 9, Math.round(data[1][9])],
      [0, 10, Math.round(data[1][10])],
      [0, 11, Math.round(data[1][11])],
    ];

    const solarValues = solarData.map(item => item[2]);
    const maxSolarValue = Math.max(...solarValues);

    solarData = solarData.map(function (item) {
      return [item[1], item[0], item[2] || '-'];
    });

    const option = {
      animation: false,
      grid: {
        height: '70%',
        y: '10%',
      },
      xAxis: {
        type: 'category',
        data: months,
        splitArea: {
          show: true,
        },
      },
      yAxis: {
        type: 'category',
        data: years,
        splitArea: {
          show: true,
        },
      },
      visualMap: {
        min: 0,
        max: maxSolarValue,
        calculable: true,
        orient: 'vertical',
        right: -20,
        top: '30%',
        inRange: {
          color: ['#aecee8', '#5fa2d9', '#0063B0'],
        },
      },
      series: [
        {
          name: '☀️ Irradiance ☀️ (W/m²)',
          type: 'heatmap',
          data: solarData,
          label: {
            normal: {
              show: true,
            },
          },
          itemStyle: {
            emphasis: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
            color: 'rgb(128, 128, 0)',
          },
          tooltip: {
            position: 'bottom',
          },
        },
      ],
    };
    return option;
  }

  render() {
    const { queryData } = this.props;
    const heatmapOptions = this.getHeatmapOption(queryData);

    const rootStyle = {
      width: '48%',
    };

    return (
      <div style={{ ...rootStyle }}>
        <ReactEcharts
          style={{ width: '100%', height: 400, marginTop: -40, marginLeft: 30 }}
          option={heatmapOptions}
        />
      </div>
    );
  }
}

HeatMap.propTypes = {
  classes: PropTypes.object.isRequired,
  queryData: PropTypes.array.isRequired,
};

export default withStyles(styles)(HeatMap);
