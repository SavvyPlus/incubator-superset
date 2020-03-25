

def generate_fin_metric(metric, unit):
    d_metric = {
        'expressionType': 'SQL',
        # 'sqlExpression': 'SpotPrice',
        'column': None,
        'aggregate': None,
        'hasCustomLabel': False,
        'fromFormData': True,
        # 'label': "".join(metric.split()),
    }
    if metric == 'PPACFD':
        if unit == '0':
            d_metric['sqlExpression'] = 'PPACFD'
        else:
            d_metric['sqlExpression'] = '(PPACFD / PPAEnergy)'
        d_metric['label'] = metric

    if metric == 'MWSoldCFD':
        if unit == '0':
            d_metric['sqlExpression'] = 'MWSoldCFD'
        else:
            d_metric['sqlExpression'] = '(MWSoldCFD / (MWSoldQuantity * CumulativeHours))'
        d_metric['label'] = metric

    if metric == 'NonFirmingContributionMargin':
        if unit == '0':
            d_metric['sqlExpression'] = 'NonFirmingContributionMargin'
        else:
            d_metric['sqlExpression'] = '(NonFirmingContributionMargin / (CapacityMW * CumulativeHours))'
        d_metric['label'] = metric

    if metric == 'ContributionMargin':
        if unit == '0':
            d_metric['sqlExpression'] = '(PPACFD + MWSoldCFD + NonFirmingContributionMargin)'
        else:
            d_metric['sqlExpression'] = '((PPACFD + MWSoldCFD + NonFirmingContributionMargin) / (CapacityMW * CumulativeHours))'
        d_metric['label'] = metric

    if metric == 'FixedOM':
        if unit == '0':
            d_metric['sqlExpression'] = 'FixedOM'
        else:
            d_metric['sqlExpression'] = 'FixedOM / (CapacityMW * CumulativeHours)'
        d_metric['label'] = metric

    if metric == 'EBIT':
        if unit == '0':
            # static
            d_metric['sqlExpression'] = '(PPACFD + MWSoldCFD + NonFirmingContributionMargin) - FixedOM'
        else:
            d_metric['sqlExpression'] = '((PPACFD + MWSoldCFD + NonFirmingContributionMargin) - FixedOM) / (CapacityMW * CumulativeHours)'
        d_metric['label'] = metric

    if metric == 'EBITDiscounted':
        if unit == '0':
            # static
            d_metric['sqlExpression'] = 'EBITDiscounted'
        else:
            d_metric['sqlExpression'] = 'EBITDiscounted / (CapacityMW * CumulativeHours)'
        d_metric['label'] = metric

    if metric == 'CapitalExpenditure':
        if unit == '0':
            d_metric['sqlExpression'] = 'CapitalExpenditure'
        else:
            d_metric['sqlExpression'] = 'CapitalExpenditure / (CapacityMW * CumulativeHours)'
        d_metric['label'] = metric

    if metric == 'TerminalValue':
        if unit == '0':
            d_metric['sqlExpression'] = 'TerminalValue'
        else:
            d_metric['sqlExpression'] = 'TerminalValue / (CapacityMW * CumulativeHours)'
        d_metric['label'] = metric

    if metric == 'NetPresentValue':
        if unit == '0':
            d_metric['sqlExpression'] = 'EBITDiscounted - CapitalExpenditure + TerminalValue'
        else:
            d_metric['sqlExpression'] = '(EBITDiscounted - CapitalExpenditure + TerminalValue) / (CapacityMW * CumulativeHours)'
        d_metric['label'] = metric

    if metric == 'PPACFDAnnually':
        if unit == '0':
            d_metric['sqlExpression'] = 'PPACFDAnnual'
        else:
            d_metric['sqlExpression'] = '(PPACFDAnnual / PPAEnergy)'
        d_metric['label'] = metric

    if metric == 'MWSoldCFDAnnually':
        if unit == '0':
            d_metric['sqlExpression'] = 'MWSoldCFDAnnual'
        else:
            d_metric['sqlExpression'] = '(MWSoldCFDAnnual / (MWSoldQuantity * CumulativeHours))'
        d_metric['label'] = metric

    return d_metric
