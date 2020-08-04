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
  isp: string;
  scenario: string;
  fetching: boolean;
  error: boolean;
  errorMsg: string;
  fetchChartData: (
    region: string,
    fuel: string,
    version: number,
    ispCase: string,
    ispScen: string,
  ) => any;
}

function BarChart({
  years,
  data,
  region,
  fuel,
  version,
  isp,
  scenario,
  fetching,
  error,
  errorMsg,
  fetchChartData,
}: BarChartProps) {
  useEffect(() => {
    fetchChartData(`${region}1`, fuel, version, isp, scenario);
  }, [region, fuel, version, isp, scenario]);

  const renderDiv = () => {
    if (error) {
      return <h3>{errorMsg}</h3>;
    }
    if (fetching || data.length === 0) {
      return (
        <div style={{ marginTop: '20rem' }}>
          <PreLoader position="floating" />
        </div>
      );
    }
    return (
      <ReactEcharts
        option={{
          color:
            fuel === 'Wind' ? ['#398880', '#b3b3b3'] : ['#efcb48', '#b3b3b3'],
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
    );
  };

  return (
    <div style={{ marginTop: 20, marginBottom: 50, textAlign: 'center' }}>
      {renderDiv()}
    </div>
  );
}

export default BarChart;
