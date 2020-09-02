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
  console.log(data);
  const cals = Object.keys(data[0]).filter(k => k.includes('Cal'));
  // console.log(cals);

  const chart = useRef(null);
  const controls = useRef(null);

  useLayoutEffect(() => {
    // Create chart instance
    // Create chart instance
    const x = am4core.create('chartdiv', am4charts.XYChart);

    // Add data
    x.data = data;

    // Create axes
    const categoryAxis = x.xAxes.push(new am4charts.CategoryAxis());
    categoryAxis.dataFields.category = 'hhs';

    // const dateAxis = x.xAxes.push(new am4charts.DateAxis());
    categoryAxis.renderer.minGridDistance = 50;

    const valueAxis = x.yAxes.push(new am4charts.ValueAxis());

    cals.forEach(cal => {
      // Create series
      console.log(cal);
      const series = x.series.push(new am4charts.LineSeries());
      series.dataFields.valueY = cal;
      series.dataFields.categoryX = 'hhs';
      series.strokeWidth = 2;
      series.minBulletDistance = 10;
      series.tooltipText = '{valueY}';
      series.tooltip.pointerOrientation = 'vertical';
      series.tooltip.background.cornerRadius = 20;
      series.tooltip.background.fillOpacity = 0.5;
      series.tooltip.label.padding(12, 12, 12, 12);
    });

    // Add scrollbar
    x.scrollbarX = new am4charts.XYChartScrollbar();
    // x.scrollbarX.series.push(series);

    // Add cursor
    x.cursor = new am4charts.XYCursor();
    x.cursor.xAxis = categoryAxis;

    chart.current = x as any;
    return () => {
      x.dispose();
    };
  }, [data]);

  function generateChartData() {
    const chartData = [];
    const firstDate = new Date();
    firstDate.setDate(firstDate.getDate() - 1000);
    let visits = 1200;
    for (let i = 0; i < 500; i++) {
      // we create date objects here. In your data, you can have date strings
      // and then set format of your dates using chart.dataDateFormat property,
      // however when possible, use date objects, as this will speed up chart rendering.
      const newDate = new Date(firstDate);
      newDate.setDate(newDate.getDate() + i);

      visits += Math.round((Math.random() < 0.5 ? 1 : -1) * Math.random() * 10);

      chartData.push({
        date: newDate,
        visits,
      });
    }
    return chartData;
  }
  return (
    <div id="chartdiv" style={{ width: `${width}px`, height: `${height}px` }} />
  );
}
