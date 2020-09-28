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

export type GenerationTechPieProps = {
  height: number;
  width: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<any, any>; // please add additional typing for your data here
  // add typing here for the props you pass in from transformProps.ts!
  transformedData: TransformedDataProps;
};

export default function GenerationTechPie(props: GenerationTechPieProps) {
  const { data, height, width, transformedData } = props;

  const chart = useRef(null);

  useLayoutEffect(() => {
    const x = am4core.create('chartdiv', am4charts.PieChart3D);

    x.hiddenState.properties.opacity = 0; // this creates initial fade-in

    x.data = [
      {
        country: 'Brown Coal',
        litres: 501.9,
      },
      {
        country: 'Hydro',
        litres: 301.9,
      },
      {
        country: 'Solar',
        litres: 201.1,
      },
      {
        country: 'Biomass',
        litres: 165.8,
      },
      {
        country: 'Wind',
        litres: 139.9,
      },
      {
        country: 'Gas',
        litres: 128.3,
      },
    ];

    x.innerRadius = am4core.percent(40);
    x.depth = 120;

    x.legend = new am4charts.Legend();

    const series = x.series.push(new am4charts.PieSeries3D());
    series.dataFields.value = 'litres';
    series.dataFields.depthValue = 'litres';
    series.dataFields.category = 'country';
    series.slices.template.cornerRadius = 5;
    series.colors.step = 3;

    chart.current = x as any;
    return () => {
      x.dispose();
    };
  }, [data, transformedData]);

  return (
    <div id="chartdiv" style={{ width: `${width}px`, height: `${height}px` }} />
  );
}
