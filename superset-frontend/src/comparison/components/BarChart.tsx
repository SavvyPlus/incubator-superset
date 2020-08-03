import React, { useEffect } from 'react';
import ReactEcharts from 'echarts-for-react';

interface ChartData {
  name: string;
  values: number[];
}

interface BarChartProps {
  years: number[];
  data: ChartData[];
  region: string;
  fuel: string;
  version: number;
  fetchChartData: (region: string, fuel: string, version: number) => any;
}

function BarChart({
  years,
  data,
  region,
  fuel,
  version,
  fetchChartData,
}: BarChartProps) {
  useEffect(() => {
    fetchChartData('SA1', '23', 2);
  }, []);

  console.log(region, fuel, version);

  return (
    <div>
      {data.length > 0 && (
        <ReactEcharts
          // key={`${chartId}${webpackHash}`}
          // id={`chart-id-${chartId}`}
          option={{
            // color: ['#003366', '#006699', '#4cabce', '#e5323e'],
            tooltip: {
              trigger: 'axis',
              axisPointer: {
                type: 'shadow',
              },
            },
            legend: {
              data: [data[0].name, data[1].name],
            },
            // toolbox: {
            //   show: true,
            //   orient: 'vertical',
            //   left: 'right',
            //   top: 'center',
            //   feature: {
            //     mark: { show: true },
            //     dataView: { show: true, readOnly: false },
            //     magicType: {
            //       show: true,
            //       type: ['line', 'bar', 'stack', 'tiled'],
            //     },
            //     restore: { show: true },
            //     saveAsImage: { show: true },
            //   },
            // },
            xAxis: [
              {
                type: 'category',
                axisTick: { show: false },
                data: years,
              },
            ],
            yAxis: [
              {
                type: 'value',
              },
            ],
            series: [
              {
                name: data[0].name,
                type: 'bar',
                barGap: 0,
                // label: labelOption,
                data: data[0].values,
              },
              {
                name: data[1].name,
                type: 'bar',
                // label: labelOption,
                data: data[1].values,
              },
            ],
          }}
          // style={{ height: `${height}px`, width: `${width}px` }}
          style={{ height: '550px' }}
          theme="light"
        />
      )}
    </div>
  );
}

export default BarChart;
