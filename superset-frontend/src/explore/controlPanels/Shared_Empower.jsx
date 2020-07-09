import { t } from '@superset-ui/translation';
import { validateNonEmpty } from '@superset-ui/validator';
import { columnChoices, controls } from '../controls';
import { formatSelectOptions } from '../../modules/utils';

export const periodTypeStaticPicker = {
  name: 'period_type_static_picker',
  config: {
    type: 'SelectControl',
    multi: false,
    label: t('Period Type'),
    default: ['CalYear'],
    validators: [validateNonEmpty],
    choices: formatSelectOptions(['CalYear', 'FinYear', 'Quarterly']),
  },
};

export const periodFinyearPicker = {
  name: 'period_finyear_picker',
  config: {
    type: 'SelectControl',
    multi: true,
    label: t('Period'),
    default: null,
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.period_finyear),
    }),
  },
};

export const periodCalyearPicker = {
  name: 'period_calyear_picker',
  config: {
    type: 'SelectControl',
    multi: true,
    label: t('Period'),
    default: null,
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.period_calyear),
    }),
  },
};

export const periodQuarterlyPicker = {
  name: 'period_quarterly_picker',
  config: {
    type: 'SelectControl',
    multi: true,
    label: t('Period'),
    default: null,
    mapStateToProps: state => ({
      choices: formatSelectOptions(state.period_quarterly),
    }),
  },
};
