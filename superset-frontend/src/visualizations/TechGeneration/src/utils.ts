import { TechGenerationDatum } from './plugin/transformProps';
import { TransformedDataProps } from './TechGeneration';

export function allFuelTypes(datasource: any) {
  if (datasource && datasource.columns) {
    return datasource.columns
      .filter((col: any) => col.column_name !== 'Year')
      .filter((col: any) => col.column_name !== 'State')
      .filter((col: any) => col.column_name !== 'Percentile')
      .map((col: any) => col.column_name);
  }
  return [];
}

export function transformData(data: TechGenerationDatum[]) {
  const orderedData = data.sort((a, b) =>
    (a['`Year`'] as string) > (b['`Year`'] as string) ? 1 : -1,
  );
  const transformedData: TransformedDataProps[] = [];
  orderedData.forEach(d => {
    const keys = Object.keys(d)
      .filter(f => f !== '`State`')
      .filter(f => f !== '`Percentile`');

    const keysMap = keys.reduce((acc, cur) => {
      acc[cur.substring(1, cur.length - 1).toLowerCase()] = cur;
      return acc;
    }, {});
    transformedData.push(
      Object.keys(keysMap).reduce((acc, cur) => {
        acc[cur] = d[keysMap[cur]];
        return acc;
      }, {}),
    );
  });

  return transformedData;
}
