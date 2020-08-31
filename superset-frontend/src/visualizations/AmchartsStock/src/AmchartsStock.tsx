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
// import React, { useEffect, createRef } from 'react';
import React, { useRef, useLayoutEffect } from 'react';
import * as am4core from '@amcharts/amcharts4/core';
import * as am4charts from '@amcharts/amcharts4/charts';
import * as am4plugins_rangeSelector from '@amcharts/amcharts4/plugins/rangeSelector';
import am4themes_animated from '@amcharts/amcharts4/themes/animated';

am4core.useTheme(am4themes_animated);

export type AmchartsStockProps = {
  height: number;
  width: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<any, any>; // please add additional typing for your data here
  // add typing here for the props you pass in from transformProps.ts!
  boldText: boolean;
  headerFontSize: 'xxs' | 'xs' | 's' | 'm' | 'l' | 'xl' | 'xxl';
  headerText: string;
};

export default function AmchartsStock(props: AmchartsStockProps) {
  const { data, height, width } = props;

  const chart = useRef(null);
  const controls = useRef(null);

  useLayoutEffect(() => {
    // Create chart
    const x = am4core.create('chartdiv', am4charts.XYChart);
    x.padding(15, 15, 15, 15);

    x.data = data as any[];

    const dateAxis = x.xAxes.push(new am4charts.DateAxis());
    dateAxis.start = 0.5;
    dateAxis.keepSelection = true;
    dateAxis.groupData = true;

    const valueAxis = x.yAxes.push(new am4charts.ValueAxis());
    valueAxis.tooltip!.disabled = true;
    valueAxis.title.text = 'Spot Price';

    const keys = Object.keys(data[0]);
    let scrollAdded = false;
    keys.forEach(key => {
      if (key !== '`HalfHourStarting`') {
        const series = x.series.push(new am4charts.LineSeries());
        series.name = key.slice(1, -2);
        series.dataFields.dateX = '`HalfHourStarting`';
        series.dataFields.valueY = `${key}`;
        series.tooltip!.background.fill = am4core.color('#fff');
        series.tooltipText = '{name}: [bold]{valueY}[/]';
        series.groupFields.valueY = 'sum';
        // series.stroke = am4core.color('red');
        // series.fill = am4core.color('red');

        if (!scrollAdded) {
          const scrollbarX = new am4charts.XYChartScrollbar();
          scrollbarX.series.push(series);
          x.scrollbarX = scrollbarX;
          scrollAdded = true;
        }
      }
    });

    x.cursor = new am4charts.XYCursor();
    x.cursor.lineY.opacity = 0;

    // Add range selector
    const selector = new am4plugins_rangeSelector.DateAxisRangeSelector();
    selector.container = controls.current as any;
    selector.axis = dateAxis;

    chart.current = x as any;
    return () => {
      x.dispose();
    };
  }, []);

  return (
    <div>
      <div ref={controls} />
      <div
        id="chartdiv"
        style={{ width: `${width}px`, height: `${height}px` }}
      />
    </div>
  );
}
