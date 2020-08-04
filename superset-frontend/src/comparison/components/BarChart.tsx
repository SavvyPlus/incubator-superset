import React, { useEffect } from 'react';
import ReactEcharts from 'echarts-for-react';
import PreLoader from '../../components/PreLoader';
import { barFormatter } from '../../utils/chartUtils';

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
  fetching: boolean;
  fetchChartData: (region: string, fuel: string, version: number, isp_case: string, isp_scen: string) => any;
}

function BarChart({
  years,
  data,
  region,
  fuel,
  version,
  fetching,
  fetchChartData,
}: BarChartProps) {
  useEffect(() => {
    fetchChartData('SA1', 'Solar', 1, 'Counterfactual', 'Central');
  }, [region, fuel]);

  console.log(region, fuel, version);

  return (
    <div style={{ marginTop: 20, marginBottom: 50 }}>
      {fetching || data.length === 0 ? (
        <div style={{ marginTop: '20rem' }}>
          <PreLoader position="floating" />
        </div>
      ) : (
        <ReactEcharts
          option={{
            color: ['#efcb48', '#b3b3b3'],
            title: {
              left: 'center',
              text: `${fuel} Generation`,
              textStyle: {
                fontSize: 26,
              },
            },
            tooltip: {
              trigger: 'axis',
              axisPointer: {
                type: 'shadow',
              },
            },
            legend: {
              top: '8%',
              icon: 'circle',
              textStyle: {
                fontSize: 16,
              },
              data: [data[0].name, data[1].name],
            },
            grid: {
              top: '20%',
            },
            toolbox: {
              show: true,
              right: '10%',
              top: 'top',
              feature: {
                dataView: {
                  show: true,
                  readOnly: true,
                  title: 'View data',
                  lang: ['Data', 'Close'],
                },
                saveAsImage: { show: true, title: 'Save as image' },
              },
            },
            xAxis: [
              {
                type: 'category',
                axisTick: { show: false },
                data: years,
                name: 'Year',
                nameLocation: 'center',
                nameGap: 30,
                nameTextStyle: {
                  fontSize: 16,
                },
              },
            ],
            yAxis: [
              {
                type: 'value',
                name: 'Generation (MW)',
                nameLocation: 'center',
                nameGap: 40,
                nameTextStyle: {
                  fontSize: 16,
                },
                axisLabel: {
                  formatter: barFormatter,
                },
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
        />
      )}
    </div>
  );
}

export default BarChart;
