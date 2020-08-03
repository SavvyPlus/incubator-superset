import React, { useEffect } from 'react';
import ReactEcharts from 'echarts-for-react';

function BarChart({ fetchChartData }) {
  useEffect(() => {
    fetchChartData('SA1', '23', 2);
  }, []);

  return (
    <div>
      <ReactEcharts
        // key={`${chartId}${webpackHash}`}
        // id={`chart-id-${chartId}`}
        option={{
          // legend: {},
          tooltip: {},
          dataset: {
            dimensions: ['product', '2015', '2016', '2017'],
            source: [
              {
                product: 'Matcha Latte',
                '2015': 43.3,
                '2016': 85.8,
                '2017': 93.7,
              },
              { product: 'Milk Tea', '2015': 83.1, '2016': 73.4, '2017': 55.1 },
              {
                product: 'Cheese Cocoa',
                '2015': 86.4,
                '2016': 65.2,
                '2017': 82.5,
              },
              {
                product: 'Walnut Brownie',
                '2015': 72.4,
                '2016': 53.9,
                '2017': 39.1,
              },
            ],
          },
          xAxis: { type: 'category' },
          yAxis: {},
          // Declare several bar series, each will be mapped
          // to a column of dataset.source by default.
          series: [{ type: 'bar' }, { type: 'bar' }, { type: 'bar' }],
        }}
        // style={{ height: `${height}px`, width: `${width}px` }}
        theme="light"
      />
    </div>
  );
}

export default BarChart;
