import { AmchartsStockDatum } from '../plugin/transformProps';

export function convertToDatetime(d: AmchartsStockDatum[]) {
  for (let i = 0; i < d.length; i += 1) {
    // eslint-disable-next-line no-param-reassign
    d[i]['`HalfHourStarting`'] = new Date(d[i]['`HalfHourStarting`'] as string);
  }

  d.sort((a, b) => {
    // Turn your strings into dates, and then subtract them
    // to get a value that is either negative, positive, or zero.
    return (
      new Date(a['`HalfHourStarting`'] as string).valueOf() -
      new Date(b['`HalfHourStarting`'] as string).valueOf()
    );
  });
  return d;
}
