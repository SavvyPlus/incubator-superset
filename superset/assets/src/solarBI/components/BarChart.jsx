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
import { CSVLink } from 'react-csv';

const styles = theme => ({
  typography: {
    margin: theme.spacing(2),
    fontSize: 15,
    width: 300,
  },
  csvLink: {
    position: 'absolute',
    right: 180,
    top: 9,
    zIndex: 200,
    color: '#424242',
    '& span': {
      display: 'none',
      fontSize: 12,
      transform: 'translateY(3px)',
    },
    '&:hover span': {
      top: 0,
      left: -70,
      width: 160,
      margin: 10,
      display: 'block',
      padding: '5px 20px 5px 5px',
      zIndex: 200,
      position: 'absolute',
      textDecoration: 'none',
      color: '#4297bd',
    },
  },
});

class BarChart extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      headers: [
        { label: 'Date', key: 'date' },
        { label: 'Solar Radiation', key: 'solar_data' },
      ],
    };

    this.getBarchartOption = this.getBarchartOption.bind(this);
  }

  getBarchartOption(data) {
    if (data) {
      const data1 = data[1];
      const xAxisData = data[0];

      const option = {
        // title: {
        //   text: 'Monthly Average',
        //   show: true,
        //   left: 'center',
        //   top: -5,
        // },
        toolbox: {
          feature: {
            saveAsImage: {
              icon: 'image://https://i.ibb.co/LvGQLgf/4444.png',
              pixelRatio: 2,
              title: 'Save As Image',
            },
          },
          right: 125,
          top: 5,
        },
        tooltip: {},
        xAxis: {
          data: xAxisData,
          silent: false,
          splitLine: {
            show: false,
          },
        },
        yAxis: {
          name: '(W/m²)',
        },
        itemStyle: {
          color: '#0063B0',
        },
        series: [
          {
            name: '☀️ Irradiance ☀️ (W/m²)',
            type: 'bar',
            data: data1,
            animationDelay(idx) {
              return idx * 10;
            },
          },
        ],
        animationEasing: 'elasticOut',
        animationDelayUpdate(idx) {
          return idx * 5;
        },
      };

      return option;
    }
    return {};
  }

  render() {
    // const { queryData, width } = this.props;
    const { queryData, classes } = this.props;
    const mergedData = [];
    for (let i = 18; i < 30; i++) {
      mergedData.push({ date: queryData[0][i], solar_data: queryData[1][i] });
    }

    const barchartOptions = this.getBarchartOption(queryData);

    // const isSmallScreen = /xs|sm|md/.test(width);
    const rootStyle = {
      // display: isSmallScreen ? 'initial' : 'flex',
      marginLeft: -60,
      marginTop: -40,
      position: 'relative',
    };

    return (
      <div style={{ ...rootStyle }}>
        <CSVLink filename={'solar-data.csv'} className={classes.csvLink} data={mergedData} headers={this.state.headers}>
          <i className="fas fa-download" /><span>Download As CSV</span>
        </CSVLink>
        <ReactEcharts
          style={{ width: '100%', height: 300 }}
          option={barchartOptions}
        />
      </div>
    );
  }
}

BarChart.propTypes = {
  classes: PropTypes.object.isRequired,
  queryData: PropTypes.array.isRequired,
};

export default withStyles(styles)(BarChart);
