import { HalfHourSpotDatum } from '../plugin/transformProps';

interface FinalDataProps {
  hhs: string;
  [key: string]: string | number;
}

export function convertDataFormat(
  rawData: HalfHourSpotDatum[],
): FinalDataProps[] {
  const finalData: FinalDataProps[] = [];
  const orderedData = rawData.sort((a, b) =>
    (a['`HHStarting`'] as string) > (b['`HHStarting`'] as string) ? 1 : -1,
  );
  const dataLen = Object.keys(orderedData).length;
  const calNum = dataLen / 48;
  let curHH: FinalDataProps = { hhs: '' };
  orderedData.forEach((od, idx) => {
    const hhs = od['`HHStarting`'] as string;
    const period = (od['`Period`'] as string).replace('-', '_');
    const sp =
      Math.round(((od['`SpotPrice`'] as number) + Number.EPSILON) * 100) / 100;

    if (idx % calNum === 0) {
      if (idx !== 0) finalData.push(curHH);
      curHH = { hhs: '' };
      curHH.hhs = hhs;
      curHH[period] = sp;
    } else if (idx === dataLen - 1) {
      curHH[period] = sp;
      finalData.push(curHH);
    } else {
      curHH[period] = sp;
    }
  });

  return finalData;
}
