/* eslint-disable @typescript-eslint/no-non-null-assertion */
/* eslint-disable @typescript-eslint/camelcase */
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
import React, { useRef, useLayoutEffect } from 'react';
import * as am4core from '@amcharts/amcharts4/core';
import * as am4charts from '@amcharts/amcharts4/charts';
// import * as am4plugins_rangeSelector from '@amcharts/amcharts4/plugins/rangeSelector';
import am4themes_animated from '@amcharts/amcharts4/themes/animated';

am4core.useTheme(am4themes_animated);

export type HalfHourSpotProps = {
  height: number;
  width: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<any, any>; // please add additional typing for your data here
  // add typing here for the props you pass in from transformProps.ts!
  boldText: boolean;
  headerFontSize: 'xxs' | 'xs' | 's' | 'm' | 'l' | 'xl' | 'xxl';
  headerText: string;
};

export default function HalfHourSpot(props: HalfHourSpotProps) {
  const { data, height, width } = props;
  // console.log(data);
  const cals = Object.keys(data[0])
    .filter(k => k.includes('Cal'))
    .sort();

  const chart = useRef(null);

  useLayoutEffect(() => {
    // Create chart instance
    // Create chart instance
    const x = am4core.create('chartdiv', am4charts.XYChart);

    // Add data
    x.data = data as any[];

    // Create axes
    const categoryAxis = x.xAxes.push(new am4charts.CategoryAxis());
    categoryAxis.dataFields.category = 'hhs';

    // const dateAxis = x.xAxes.push(new am4charts.DateAxis());
    categoryAxis.renderer.minGridDistance = 50;

    const valueAxis = x.yAxes.push(new am4charts.ValueAxis());
    valueAxis.title.text = 'Nominal Spot Price ($/MWh)';

    // Add scrollbar
    const scrollbarX = new am4charts.XYChartScrollbar();
    scrollbarX.minHeight = 30;

    let toolTxt = '';
    cals.forEach(cal => {
      toolTxt += `${cal.replace('_', '-')}: \${${cal}}\n`;
    });
    cals.forEach((cal, idx) => {
      // Create series
      const series = x.series.push(new am4charts.LineSeries());
      series.name = cal.replace('_', '-');
      series.dataFields.valueY = cal;
      series.dataFields.categoryX = 'hhs';
      series.strokeWidth = 2;
      series.minBulletDistance = 10;
      if (idx === 0) {
        series.tooltipText = `[bold]{categoryX}[/]\n\n${toolTxt}`;
      }
      series.tooltip!.pointerOrientation = 'vertical';
      series.tooltip!.background.cornerRadius = 20;
      series.tooltip!.background.fillOpacity = 0.5;
      series.tooltip!.label.padding(12, 12, 12, 12);
      scrollbarX.series.push(series);
    });

    x.scrollbarX = scrollbarX;
    x.scrollbarX.parent = x.bottomAxesContainer;
    // Add cursor
    x.cursor = new am4charts.XYCursor();
    x.cursor.xAxis = categoryAxis;

    x.legend = new am4charts.Legend();
    x.legend.position = 'top';
    x.legend.useDefaultMarker = true;
    x.legend.itemContainers.template.events.on('hit', function (ev) {
      const targetSeries = ev.target.dataItem!.dataContext as any;
      if (!(targetSeries.isHidden || targetSeries.isHiding)) {
        toolTxt = '';
        x.series.values.forEach(value => {
          const vy = value.dataFields.valueY!;
          if (vy !== targetSeries.dataFields.valueY) {
            if (!(value.isHidden || value.isHiding)) {
              toolTxt += `${vy.replace('_', '-')}: \${${vy}}\n`;
            }
          }
        });

        x.series.values[0].tooltipText = `[bold]{categoryX}[/]\n\n${toolTxt}`;
      } else {
        toolTxt = '';
        x.series.values.forEach(value => {
          const vy = value.dataFields.valueY!;
          if (!(value.isHidden || value.isHiding)) {
            // console.log(vy);
            toolTxt += `${vy.replace('_', '-')}: \${${vy}}\n`;
          }

          if (targetSeries.dataFields.valueY === vy) {
            toolTxt += `${vy.replace('_', '-')}: \${${vy}}\n`;
          }
          x.series.values[0].tooltipText = `[bold]{categoryX}[/]\n\n${toolTxt}`;
        });
      }
    });

    const marker: any = x.legend.markers.template.children.getIndex(0);
    marker!.cornerRadius(12, 12, 12, 12);
    marker!.strokeWidth = 1;
    marker!.strokeOpacity = 1;
    marker!.stroke = am4core.color('#ccc');

    chart.current = x as any;
    return () => {
      x.dispose();
    };
  }, [data]);

  return (
    <div id="chartdiv" style={{ width: `${width}px`, height: `${height}px` }} />
  );
}
