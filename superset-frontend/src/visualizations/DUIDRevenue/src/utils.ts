/* eslint-disable dot-notation */
import { DuidRevenueDatum } from './plugin/transformProps';

interface TransformedDataProps {
  duid: string;
  values: number[][];
}

export function formatSelectOptions(options: string[]): string[][] {
  const choices = options.map(opt => [opt, opt.toString()]);
  choices.unshift(['All', 'All']);
  return choices;
}

export function transformData(data: DuidRevenueDatum[]) {
  const transformedData: TransformedDataProps[] = [];
  const orderedData = data.sort((a, b) =>
    (a['`Year`'] as string) > (b['`Year`'] as string) ? 1 : -1,
  );
  // console.log(orderedData);
  orderedData.forEach(item => {
    const duid = item['`Duid`'] as string;
    const per0 = item['`0`'] as number;
    const per25 = item['`0.25`'] as number;
    const per50 = item['`0.5`'] as number;
    const per75 = item['`0.75`'] as number;
    const per100 = item['`1`'] as number;
    const idx = transformedData.findIndex(d => d.duid === duid);
    if (idx === -1) {
      transformedData.push({
        duid,
        values: [[per0, per25, per50, per75, per100]],
      });
    } else {
      transformedData[idx].values.push([per0, per25, per50, per75, per100]);
    }
  });
  // console.log(transformedData);
  return transformedData;
}

export function getPeriods(data: DuidRevenueDatum[]) {
  const orderedData = data.sort((a, b) =>
    (a['`Year`'] as string) > (b['`Year`'] as string) ? 1 : -1,
  );
  return Array.from(new Set(orderedData.map(entry => entry['`Year`'])));
}

export function boxplotFormatter(param: any) {
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

export function yAxisLabelFormatter(value: number) {
  // Formatted to be month/day; display year only in the first label
  return `${value / 1000000}M`;
}
