/* eslint-disable no-param-reassign */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { render } from 'react-dom';
import Highcharts from 'highcharts/highstock';
import HighchartsReact from 'highcharts-react-official';
import * as Actions from '../actions/generation';

(function (H) {
  H.Pointer.prototype.reset = function () {
    return undefined;
  };

  /**
   * Highlight a point by showing tooltip, setting hover state and draw crosshair
   */
  H.Point.prototype.highlight = function (event) {
    event = this.series.chart.pointer.normalize(event);
    this.onMouseOver(); // Show the hover marker
    // this.series.chart.tooltip.refresh(this); // Show the tooltip
    this.series.chart.xAxis[0].drawCrosshair(event, this); // Show the crosshair
  };

  H.syncExtremes = function (e) {
    const thisChart = this.chart;

    if (e.trigger !== 'syncExtremes') {
      // Prevent feedback loop
      Highcharts.each(Highcharts.charts, function (chart) {
        if (chart && chart !== thisChart) {
          if (chart.xAxis[0].setExtremes) {
            // It is null while updating
            chart.xAxis[0].setExtremes(e.min, e.max, undefined, false, {
              trigger: 'syncExtremes',
            });
          }
        }
      });
    }
  };
})(Highcharts);

class Charts extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      options1: {
        chart: {
          type: 'area',
        },
        title: {
          text: 'Generation',
        },
        xAxis: {
          tickmarkPlacement: 'on',
          title: {
            enabled: false,
          },
          // visible: true,
          crosshair: true,
          // tickWidth: 0,
          // tickLength: 0,
          // events: {
          //   setExtremes(e) {
          //     Highcharts.syncExtremes(e);
          //   },
          // },
        },
        yAxis: {
          title: {
            text: 'MW',
          },
        },
        plotOptions: {
          series: {
            point: {
              events: {
                mouseOver: this.setHoverData.bind(this),
              },
            },
          },
          area: {
            stacking: 'normal',
            lineColor: '#666666',
            lineWidth: 1,
            marker: {
              lineWidth: 1,
              lineColor: '#666666',
            },
          },
        },
        tooltip: {
          shared: true,
          valueSuffix: ' MW',
        },
        series: [
          {
            name: 'Asia',
            data: [
              5042,
              4635,
              3809,
              5947,
              4402,
              3634,
              5268,
              5042,
              4635,
              3809,
              5947,
              4402,
              3634,
              5268,
            ],
          },
          {
            name: 'Africa',
            data: [
              1106,
              1107,
              1111,
              1133,
              1221,
              1767,
              1766,
              1106,
              1107,
              1111,
              1133,
              1221,
              1767,
              1766,
            ],
          },
          {
            name: 'Europe',
            data: [
              563,
              603,
              676,
              608,
              547,
              729,
              628,
              563,
              603,
              676,
              608,
              547,
              729,
              628,
            ],
          },
          {
            name: 'America',
            data: [
              1118,
              1231,
              1154,
              1156,
              1339,
              1218,
              1201,
              1118,
              1231,
              1154,
              1156,
              1339,
              1218,
              1201,
            ],
          },
          {
            name: 'Oceania',
            data: [42, 42, 42, 36, 43, 50, 46, 42, 42, 42, 36, 43, 50, 46],
          },
        ],
      },
      options2: {
        xAxis: {
          visible: true,
          crosshair: true,
          tickWidth: 0,
          tickLength: 0,
          events: {
            setExtremes(e) {
              Highcharts.syncExtremes(e);
            },
          },
          labels: {
            format: '{value} km',
          },
        },
        yAxis: {
          gridLineWidth: 2,
          tickWidth: 2,
          tickLength: 78,
          tickmarkPlacement: 'on',
          tickPixelInterval: 40,
          title: { enabled: false },
          labels: {
            align: 'left',
            x: -60,
            y: -10,
          },
        },
        legend: { enabled: false },
        marker: { enabled: false },
        plotOptions: {
          line: { marker: { enabled: false } },
          column: { pointWidth: 6 },
        },
        tooltip: {
          enabled: true,
          useHTML: true,
          shared: true,
          borderRadius: 3,
          shape: 'rectangle',
          shadow: false,
          padding: 20,
        },
        series: [
          {
            type: 'line',
            name: 'Generation',
            data: [
              1118,
              1231,
              1154,
              1156,
              1339,
              1218,
              1201,
              1118,
              1231,
              1154,
              1156,
              1339,
              1218,
              1201,
            ],
          },
        ],
      },
      options3: {
        chart: {
          type: 'column',
        },
        title: {
          text: 'Stacked column chart',
        },
        xAxis: {
          crosshair: true,
        },
        yAxis: {
          min: 0,
          title: {
            text: 'Total fruit consumption',
          },
        },
        tooltip: {
          shared: true,
          headerFormat: '<b>{point.x}</b><br/>',
          pointFormat: '{series.name}: {point.y}<br/>Total: {point.stackTotal}',
        },
        plotOptions: {
          series: {
            pointPadding: 0,
            groupPadding: 0,
            borderWidth: 0,
            shadow: false,
          },
          column: {
            stacking: 'normal',
          },
        },
        series: [
          {
            name: 'Asia',
            data: [
              5042,
              4635,
              3809,
              5947,
              4402,
              3634,
              5268,
              5042,
              4635,
              3809,
              5947,
              4402,
              3634,
              5268,
            ],
          },
          {
            name: 'Africa',
            data: [
              1106,
              1107,
              1111,
              1133,
              1221,
              1767,
              1766,
              1106,
              1107,
              1111,
              1133,
              1221,
              1767,
              1766,
            ],
          },
          {
            name: 'Europe',
            data: [
              563,
              603,
              676,
              608,
              547,
              729,
              628,
              563,
              603,
              676,
              608,
              547,
              729,
              628,
            ],
          },
          {
            name: 'America',
            data: [
              1118,
              1231,
              1154,
              1156,
              1339,
              1218,
              1201,
              1118,
              1231,
              1154,
              1156,
              1339,
              1218,
              1201,
            ],
          },
          {
            name: 'Oceania',
            data: [42, 42, 42, 36, 43, 50, 46, 42, 42, 42, 36, 43, 50, 46],
          },
        ],
      },
    };
  }

  componentDidMount() {
    ['mousemove', 'touchmove', 'touchstart'].forEach(function (eventType) {
      document
        .getElementById('container')
        .addEventListener(eventType, function (e) {
          let chart;
          let point;
          let i;
          let event;

          for (i = 0; i < Highcharts.charts.length; i += 1) {
            chart = Highcharts.charts[i];
            if (chart) {
              // Find coordinates within the chart
              event = chart.pointer.normalize(e);
              // Get the hovered point
              point = chart.series[0].searchPoint(event, true);
              if (point) {
                point.highlight(e);
              }
            }
          }
        });
    });
  }

  setHoverData = e => {
    console.log(e.target.category);
  };

  render() {
    return (
      <div id="container">
        <HighchartsReact
          highcharts={Highcharts}
          options={this.state.options1}
        />
        <div style={{ height: 30 }} />
        <HighchartsReact
          highcharts={Highcharts}
          options={this.state.options2}
        />
        {/* <HighchartsReact
          highcharts={Highcharts}
          options={this.state.options3}
        /> */}
      </div>
    );
  }
}

function mapStateToProps(state) {
  const { generation } = state;
  return {
    generation,
  };
}

function mapDispatchToProps(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Charts);
