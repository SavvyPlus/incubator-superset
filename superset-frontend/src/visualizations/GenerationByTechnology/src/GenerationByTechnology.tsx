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

export interface TransformedDataProps {
  [key: string]: string;
}

export type GenerationByTechnologyProps = {
  height: number;
  width: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<any, any>; // please add additional typing for your data here
  // add typing here for the props you pass in from transformProps.ts!
  transformedData: TransformedDataProps;
};

export default function GenerationByTechnology(
  props: GenerationByTechnologyProps,
) {
  const { data, height, width, transformedData } = props;

  const chart = useRef(null);

  useLayoutEffect(() => {
    const x = am4core.create('chartdiv', am4charts.XYChart);

    // @ts-ignore
    x.data = transformedData;
    // console.log(transformedData);
    // Create axes
    const categoryAxis = x.xAxes.push(new am4charts.CategoryAxis());
    categoryAxis.dataFields.category = 'year';
    categoryAxis.renderer.grid.template.location = 0;

    const valueAxis = x.yAxes.push(new am4charts.ValueAxis());
    valueAxis.title.text = 'MWh';
    // valueAxis.renderer.inside = true;
    // valueAxis.renderer.labels.template.disabled = true;
    valueAxis.min = 0;
    x.numberFormatter.numberFormat = '#.a';

    [
      ['battery', 'Battery', '#9f5d8d'],
      ['biomass', 'Biomass', '#dd5025'],
      ['blackcoal', 'Black Coal', '#000000'],
      ['browncoal', 'Brown Coal', '#7f4d38'],
      ['demand', 'Demand', '#cccccc'],
      ['gas', 'Gas', '#e73727'],
      ['hydro', 'Hydro', '#98d2e8'],
      ['liquidfuel', 'Liquid Fuel', '#a75834'],
      ['solar', 'Solar', '#f1d563'],
      ['solarpv', 'Solar PV', '#f8e9a8'],
      ['wind', 'Wind', '#58b5aa'],
    ].forEach(region => {
      const series = x.series.push(new am4charts.ColumnSeries());
      const name = region[1];
      const field = region[0];
      const hex = region[2];
      series.name = name;
      series.dataFields.valueY = field;
      series.dataFields.categoryX = 'year';
      series.sequencedInterpolation = true;

      // Make it stacked
      series.stacked = true;

      // Configure columns
      series.columns.template.width = am4core.percent(60);
      series.columns.template.tooltipText =
        '[bold]{name}[/]\n[font-size:14px]{categoryX}: {valueY}';
      series.columns.template.stroke = am4core.color(hex);
      series.columns.template.fill = am4core.color(hex);

      // Add label
      const labelBullet = series.bullets.push(new am4charts.LabelBullet());
      // labelBullet.label.text = '{valueY}';
      labelBullet.locationY = 0.5;
      labelBullet.label.hideOversized = true;
    });

    x.legend = new am4charts.Legend();
    x.legend.position = 'top';

    x.scrollbarX = new am4core.Scrollbar();
    x.scrollbarX.parent = x.bottomAxesContainer;

    chart.current = x as any;
    return () => {
      x.dispose();
    };
  }, [data]);

  return (
    <div id="chartdiv" style={{ width: `${width}px`, height: `${height}px` }} />
  );
}
