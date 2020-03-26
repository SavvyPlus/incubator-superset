

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
    if metric == 'PPA CFD':
        if unit == '0':
            d_metric['sqlExpression'] = 'PPACFD'
        else:
            d_metric['sqlExpression'] = '(PPACFD / PPAEnergy)'
        d_metric['label'] = 'PPACFD'

    if metric == 'MW Sold CFD':
        if unit == '0':
            d_metric['sqlExpression'] = 'MWSoldCFD'
        else:
            d_metric['sqlExpression'] = '(MWSoldCFD / (MWSoldQuantity * CumulativeHours))'
        d_metric['label'] = 'MWSoldCFD'

    if metric == 'Non-Firming Contribution Margin':
        if unit == '0':
            d_metric['sqlExpression'] = 'NonFirmingContributionMargin'
        else:
            d_metric['sqlExpression'] = '(NonFirmingContributionMargin / (CapacityMW * CumulativeHours))'
        d_metric['label'] = 'NonFirmingContributionMargin'

    if metric == 'Contribution Margin':
        if unit == '0':
            d_metric['sqlExpression'] = '(PPACFD + MWSoldCFD + NonFirmingContributionMargin)'
        else:
            d_metric['sqlExpression'] = '((PPACFD + MWSoldCFD + NonFirmingContributionMargin) / (CapacityMW * CumulativeHours))'
        d_metric['label'] = 'ContributionMargin'

    if metric == 'Fixed O&M':
        if unit == '0':
            d_metric['sqlExpression'] = 'FixedOM'
        else:
            d_metric['sqlExpression'] = 'FixedOM / (CapacityMW * CumulativeHours)'
        d_metric['label'] = 'FixedOM'

    if metric == 'EBIT':
        if unit == '0':
            # static
            d_metric['sqlExpression'] = '(PPACFD + MWSoldCFD + NonFirmingContributionMargin) - FixedOM'
        else:
            d_metric['sqlExpression'] = '((PPACFD + MWSoldCFD + NonFirmingContributionMargin) - FixedOM) / (CapacityMW * CumulativeHours)'
        d_metric['label'] = metric

    if metric == 'EBIT (Discounted)':
        if unit == '0':
            # static
            d_metric['sqlExpression'] = 'EBITDiscounted'
        else:
            d_metric['sqlExpression'] = 'EBITDiscounted / (CapacityMW * CumulativeHours)'
        d_metric['label'] = 'EBITDiscounted'

    if metric == 'Capital Expenditure':
        if unit == '0':
            d_metric['sqlExpression'] = 'CapitalExpenditure'
        else:
            d_metric['sqlExpression'] = 'CapitalExpenditure / (CapacityMW * CumulativeHours)'
        d_metric['label'] = 'CapitalExpenditure'

    if metric == 'Terminal Value (Discounted)':
        if unit == '0':
            d_metric['sqlExpression'] = 'TerminalValue'
        else:
            d_metric['sqlExpression'] = 'TerminalValue / (CapacityMW * CumulativeHours)'
        d_metric['label'] = 'TerminalValue'

    if metric == 'Net Present Value':
        if unit == '0':
            d_metric['sqlExpression'] = 'EBITDiscounted - CapitalExpenditure + TerminalValue'
        else:
            d_metric['sqlExpression'] = '(EBITDiscounted - CapitalExpenditure + TerminalValue) / (CapacityMW * CumulativeHours)'
        d_metric['label'] = 'NetPresentValue'

    if metric == 'PPA CFD (Annually)':
        if unit == '0':
            d_metric['sqlExpression'] = 'PPACFDAnnual'
        else:
            d_metric['sqlExpression'] = '(PPACFDAnnual / PPAEnergy)'
        d_metric['label'] = 'PPACFDAnnual'

    if metric == 'MW Sold CFD (Annually)':
        if unit == '0':
            d_metric['sqlExpression'] = 'MWSoldCFDAnnual'
        else:
            d_metric['sqlExpression'] = '(MWSoldCFDAnnual / (MWSoldQuantity * CumulativeHours))'
        d_metric['label'] = 'MWSoldCFDAnnual'

    return d_metric

