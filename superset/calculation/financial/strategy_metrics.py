import copy

dict = copy.deepcopy(dict)


def generate_default_metrics():
    d_metric = {
        'expressionType': 'SQL',
        # 'sqlExpression': 'SpotPrice',
        'column': None,
        'aggregate': None,
        'hasCustomLabel': False,
        'fromFormData': True,
        # 'label': "".join(metric.split()),
    }
    metrics = []

    metrics.append({'sqlExpression': 'NonFirmingContributionMargin',
                    'label': "NonFirmingContributionMargin"})

    metrics.append({'sqlExpression': 'PPACFD',
                    'label': "PPACFD"})

    metrics.append({'sqlExpression': 'DiscountRate',
                    'label': "DiscountRate"})

    metrics.append({'sqlExpression': 'FixedOM',
                    'label': "FixedOM"})

    metrics.append({'sqlExpression': 'CapitalExpenditure',
                    'label': "CapitalExpenditure"})

    metrics.append({'sqlExpression': 'TerminalValue',
                    'label': "TerminalValue"})

    metrics.append({'sqlExpression': '(PPACFD + MWSoldCFD + NonFirmingContributionMargin)',
                    'label': "ContributionMargin"})

    for metric in metrics:
        metric.update({
            'expressionType': 'SQL',
            'column': None,
            'aggregate': None,
            'hasCustomLabel': False,
            'fromFormData': True,
        })
    return metrics


def generate_fin_str_metrics(metric):
    d_metric = {
        'expressionType': 'SQL',
        # 'sqlExpression': 'SpotPrice',
        'column': None,
        'aggregate': None,
        'hasCustomLabel': False,
        'fromFormData': True,
        # 'label': "".join(metric.split()),
    }
    metrics = []
    merchant = None
    wind_offtake = None
    merchant_wind_offtake = None
    merchant_wind_selling = None

    if metric == 'Contribution Margin':
        merchant = 'NonFirmingContributionMargin'
        wind_offtake = 'PPACFD'
        merchant_wind_offtake = '(NonFirmingContributionMargin + PPACFD)'
        merchant_wind_selling = '(PPACFD + MWSoldCFD + NonFirmingContributionMargin)'

    if metric == 'EBIT':
        merchant = '(NonFirmingContributionMargin - FixedOM)'
        wind_offtake = 'PPACFD'
        merchant_wind_offtake = '((NonFirmingContributionMargin + PPACFD) - FixedOM)'
        merchant_wind_selling = '((PPACFD + MWSoldCFD + NonFirmingContributionMargin) - FixedOM)'

    if metric == 'Capital Adjustment Discounted':
        # = (Capital Expenditure - Terminal Value) / (1 + Discount Rate*)
        merchant = '((CapitalExpenditure - TerminalValue) / (1 + DiscountRate))'
        wind_offtake = '0'
        # = (Capital Expenditure - Terminal Value) / (1 + Discount Rate*)
        merchant_wind_offtake = merchant
        # = (Capital Expenditure - Terminal Value) / (1 + Discount Rate*)
        merchant_wind_selling = merchant

    d_metric.update({'sqlExpression': merchant, 'label': "'Merchant Only'"})
    metrics.append(d_metric)

    d_metric.update({'sqlExpression': wind_offtake, 'label': "'Wind Offtake Only'"})
    metrics.append(d_metric)

    d_metric.update({'sqlExpression': merchant_wind_offtake, 'label': "'Merchant + Wind Offtake'"})
    metrics.append(d_metric)

    d_metric.update({'sqlExpression': merchant_wind_selling, 'label': "'Merchant + Wind Offtake + Selling Firm'"})
    metrics.append(d_metric)

    return metrics
