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

export interface TransformedDataProps {
  [key: string]: string;
}

export type GenerationTechWaterfallProps = {
  height: number;
  width: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<any, any>; // please add additional typing for your data here
  // add typing here for the props you pass in from transformProps.ts!
  transformedData: TransformedDataProps;
};

export default function GenerationTechWaterfall(
  props: GenerationTechWaterfallProps,
) {
  const { data, height, width, transformedData } = props;

  const chart = useRef(null);

  // Create series
  const createSeries = (
    open: string,
    close: string,
    name: string,
    chart: any,
    showSum: boolean,
  ) => {
    const series = chart.series.push(new am4charts.ColumnSeries());
    series.dataFields.valueY = close;
    series.dataFields.openValueY = open;
    series.name = name;
    series.dataFields.categoryX = 'category';
    series.clustered = false;
    series.strokeWidth = 0;
    series.columns.template.width = am4core.percent(90);

    const labelBullet = series.bullets.push(new am4charts.LabelBullet());
    labelBullet.label.hideOversized = true;
    labelBullet.label.fill = am4core.color('#fff');
    labelBullet.label.text = '{valueY}';
    labelBullet.label.adapter.add('text', (_: any, target: any) => {
      const val = Math.abs(target.dataItem.valueY - target.dataItem.openValueY);
      return val;
    });
    labelBullet.locationY = 0.5;

    if (showSum) {
      const sumBullet = series.bullets.push(new am4charts.LabelBullet());
      sumBullet.label.text = '{valueY.close}';
      sumBullet.verticalCenter = 'bottom';
      sumBullet.dy = -5;
      sumBullet.label.adapter.add('text', (_: any, target: any) => {
        const val = Math.abs(
          target.dataItem.dataContext.close2 -
            target.dataItem.dataContext.open1,
        );
        return val;
      });
    }
  };

  useLayoutEffect(() => {
    const x = am4core.create('chartdiv', am4charts.XYChart);

    x.data = [
      {
        category: 'Stage #1',
        open1: 0,
        close1: 83,
        open2: 83,
        close2: 128,
      },
      {
        category: 'Stage #2',
        open1: 121,
        close1: 128,
        open2: 128,
        close2: 128,
      },
      {
        category: 'Stage #3',
        open1: 111,
        close1: 114,
        open2: 114,
        close2: 121,
      },
      {
        category: 'Stage #4',
        open1: 98,
        close1: 108,
        open2: 108,
        close2: 111,
      },
      {
        category: 'Stage #5',
        open1: 85,
        close1: 96,
        open2: 96,
        close2: 98,
      },
      {
        category: 'Stage #6',
        open1: 55,
        close1: 70,
        open2: 70,
        close2: 85,
      },
      {
        category: 'Stage #7',
        open1: 3,
        close1: 36,
        open2: 36,
        close2: 55,
      },
      {
        category: 'Stage #8',
        open1: 0,
        close1: 2,
        open2: 2,
        close2: 3,
      },
    ];

    // Create axes
    const categoryAxis = x.xAxes.push(new am4charts.CategoryAxis());
    categoryAxis.dataFields.category = 'category';
    categoryAxis.renderer.grid.template.location = 0;
    categoryAxis.renderer.minGridDistance = 30;
    categoryAxis.renderer.ticks.template.disabled = false;
    categoryAxis.renderer.ticks.template.strokeOpacity = 0.5;

    const valueAxis = x.yAxes.push(new am4charts.ValueAxis());
    valueAxis.calculateTotals = true;
    // valueAxis.max = 160;

    createSeries('open1', 'close1', 'High', x, false);
    createSeries('open2', 'close2', 'Medium', x, true);

    chart.current = x as any;
    return () => {
      x.dispose();
    };
  }, [data, transformedData]);

  return (
    <div id="chartdiv" style={{ width: `${width}px`, height: `${height}px` }} />
  );
}
