

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

    return d_metric
