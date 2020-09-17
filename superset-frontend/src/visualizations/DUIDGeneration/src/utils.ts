/* eslint-disable dot-notation */
import { DuidGenerationDatum } from './plugin/transformProps';

interface DuidValuesProps {
  duid: string;
  values: number[][];
}

interface TransformedDataProps {
  axisData: string[];
  boxData: number[][];
  outliers: (string | number)[][];
}

// export function formatSelectOptions(options: string[]): string[][] {
//   const choices = options.map(opt => [opt, opt.toString()]);
//   choices.unshift(['All', 'All']);
//   return choices;
// }

// export function transformData(data: DuidGenerationDatum[]) {
//   const transformedData: TransformedDataProps[] = [];
//   const orderedData = data.sort((a, b) =>
//     (a['`Year`'] as string) > (b['`Year`'] as string) ? 1 : -1,
//   );
//   // console.log(orderedData);
//   orderedData.forEach(item => {
//     const duid = item['`Duid`'] as string;
//     const per0 = item['`0`'] as number;
//     const per25 = item['`0.25`'] as number;
//     const per50 = item['`0.5`'] as number;
//     const per75 = item['`0.75`'] as number;
//     const per100 = item['`1`'] as number;
//     const idx = transformedData.findIndex(d => d.duid === duid);
//     if (idx === -1) {
//       transformedData.push({
//         duid,
//         values: [[per0, per25, per50, per75, per100]],
//       });
//     } else {
//       transformedData[idx].values.push([per0, per25, per50, per75, per100]);
//     }
//   });
//   // console.log(transformedData);
//   return transformedData;
// }

export function asc(arr: any[]): any[] {
  arr.sort(function (a, b) {
    return a - b;
  });
  return arr;
}

export function quantile(ascArr: any[], p: number): number {
  const H = (ascArr.length - 1) * p + 1;
  const h = Math.floor(H);
  const v = +ascArr[h - 1];
  const e = H - h;
  return e ? v + e * (ascArr[h] - v) : v;
}

export function getPercentileData(
  rawData: number[][],
  boundIQR: number,
  periods: string[],
): TransformedDataProps {
  const boxData: number[][] = [];
  const outliers: (string | number)[][] = [];
  const axisData: string[] = [];
  const useExtreme = boundIQR === 0;

  for (let i = 0; i < rawData.length; i++) {
    axisData.push(`${periods[i]}`);
    let ascList: number[] = [];
    if (rawData[i].length === 0) {
      ascList = [0, 0, 0, 0, 0, 0, 0, 0];
    } else {
      ascList = asc(rawData[i].slice());
    }
    // const ascList = asc(rawData[i].slice());
    const Q1 = quantile(ascList, 0.25);
    const Q2 = quantile(ascList, 0.5);
    const Q3 = quantile(ascList, 0.75);
    const min = ascList[0];
    const max = ascList[ascList.length - 1];
    const bound = (boundIQR == null ? 1.5 : boundIQR) * (Q3 - Q1);
    const low = useExtreme ? min : Math.max(min, Q1 - bound);
    const high = useExtreme ? max : Math.min(max, Q3 + bound);
    boxData.push([low, Q1, Q2, Q3, high]);

    for (let j = 0; j < ascList.length; j++) {
      const dataItem = ascList[j];

      if (dataItem < low || dataItem > high) {
        const outlier = [`${periods[i]}`, dataItem];
        outliers.push(outlier);
      }
    }
  }

  return {
    boxData,
    outliers,
    axisData,
  };
}

export function getPeriods(data: DuidGenerationDatum[]): any[] {
  return asc(Array.from(new Set(data.map(entry => entry['`Year`']))));
}

export function getDuids(data: DuidGenerationDatum[]): any[] {
  return asc(Array.from(new Set(data.map(entry => entry['`Duid`']))));
}

export function formatSelectOptions(options: string[]): string[][] {
  const choices = options.map(opt => [opt, opt.toString()]);
  choices.unshift(['All', 'All']);
  return choices;
}

export function transformData(
  data: DuidGenerationDatum[],
  whiskerType: string,
): TransformedDataProps[] {
  const allDuidValues: DuidValuesProps[] = [];
  const duids = getDuids(data);
  const periods = getPeriods(data);
  duids.forEach(duid => {
    const duidValues: DuidValuesProps = { duid, values: [] };
    periods.forEach(period => {
      const values: number[] = [];
      data.forEach(entry => {
        if (entry['`Year`'] === period && entry['`Duid`'] === duid) {
          values.push(entry['`Generation`'] as number);
        }
      });
      duidValues.values.push(values);
    });
    allDuidValues.push(duidValues);
  });
  // console.log(transformedData);
  const transformedData: TransformedDataProps[] = [];
  allDuidValues.forEach(item => {
    if (whiskerType === 'min/max') {
      transformedData.push(getPercentileData(item.values, 0, periods));
    } else {
      transformedData.push(getPercentileData(item.values, 1.5, periods));
    }
  });
  // console.log(transformedData);
  // const orderedData = data.sort((a, b) =>
  //   (a['`Year`'] as string) > (b['`Year`'] as string) ? 1 : -1,
  // );
  // // console.log(orderedData);
  // orderedData.forEach(item => {
  //   const duid = item['`Duid`'] as string;
  //   const per0 = item['`0`'] as number;
  //   const per25 = item['`0.25`'] as number;
  //   const per50 = item['`0.5`'] as number;
  //   const per75 = item['`0.75`'] as number;
  //   const per100 = item['`1`'] as number;
  //   const idx = transformedData.findIndex(d => d.duid === duid);
  //   if (idx === -1) {
  //     transformedData.push({
  //       duid,
  //       values: [[per0, per25, per50, per75, per100]],
  //     });
  //   } else {
  //     transformedData[idx].values.push([per0, per25, per50, per75, per100]);
  //   }
  // });
  // console.log(transformedData);
  return transformedData;
}

export function boxplotFormatter(param: any): string {
  // console.log(param);
  return [
    'Whiker Type: <strong>Min/Max</strong>',
    `DUID: <strong>${param.seriesName}</strong>`,
    `Period: <strong>${param.name}</strong>`,
    `Minimum: <strong>${param.data[1].toFixed(2)}</strong>`,
    `Q1: <strong>${param.data[2].toFixed(2)}</strong>`,
    `Median: <strong>${param.data[3].toFixed(2)}</strong>`,
    `Q3: <strong>${param.data[4].toFixed(2)}</strong>`,
    `Maximum: <strong>${param.data[5].toFixed(2)}</strong>`,
  ].join('<br/>');
}

export function yAxisLabelFormatter(value: number): string {
  // Formatted to be month/day; display year only in the first label
  return `${(value / 1000000).toFixed(2)}M`;
}
