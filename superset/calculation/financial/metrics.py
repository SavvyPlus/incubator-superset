

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


def contribution_margin(df, strategy):
        if strategy == 'MO':
            df['ContributionMargin'] = list(df['NonFirmingContributionMargin'])
            df['EBIT'] = df['ContributionMargin'] - df['FixedOM']
        elif strategy == 'WOO':
            df['ContributionMargin'] = list(df['PPACFD'])
            df['EBIT'] = list(df['ContributionMargin'])
        elif strategy == 'MWO':
            df['ContributionMargin'] = df['NonFirmingContributionMargin'] + df['PPACFD']
            df['EBIT'] = df['ContributionMargin'] - df['FixedOM']
        else:
            df['EBIT'] = df['ContributionMargin'] - df['FixedOM']
        return df

def contribution_margin_dis(df, metric, base_metric):
        for scenario in df['Scenario'].unique():
            for firm_tect in df['FirmingTechnology'].unique():
                for tech in df['Technology'].unique():
                    df_year_list = []
                    for period in df['Period'].unique():
                        df_year_list.append(df[(df['Scenario'] == scenario) &
                                              (df['FirmingTechnology'] == firm_tect) &
                                              (df['Technology'] == tech) &
                                              (df['Period'] == period)])

                    for last_yr_df, cur_yr_df in zip(df_year_list[:-1], df_year_list[1:]):
                        for (index_1, row_1), (index_2, row_2) in zip(last_yr_df.iterrows(), cur_yr_df.iterrows()):
                            df.loc[index_2, metric] = cur_yr_df.loc[index_2, metric] = (
                                  row_2[base_metric] - row_1[base_metric]) / (1 +row_2['DiscountRate']) + row_1[metric]

        return df

def capital_adjustment_dis(df, strategy):
        if strategy == 'WOO':
            df['CapitalAdjustmentDiscounted'] = 0
        else:
            df['CapitalAdjustmentDiscounted'] = (df['CapitalExpenditure'] - df['TerminalValue']) / (
                        1 + df['DiscountRate'])
        return df

def net_present_value(df, strategy):
        df['NetPresentValue'] = df['EBITDiscounted'] - df['CapitalAdjustmentDiscounted']
        return df

def adjusted_EBIT(df):
    for scenario in df['Scenario'].unique():
        for firm_tect in df['FirmingTechnology'].unique():
            for tech in df['Technology'].unique():
                df_year_list = []
                for period in df['Period'].unique():
                    df_year_list.append(df[(df['Scenario'] == scenario) &
                                          (df['FirmingTechnology'] == firm_tect) &
                                          (df['Technology'] == tech) &
                                          (df['Period'] == period)])

                for df_year in df_year_list:
                    df_year = df_year[df_year['Percentile'] != 'avg']
                    for (head_index, head_row), (tail_index, tail_row) in zip(df_year.iterrows(), df_year.iloc[::-1].iterrows()):
                        df.loc[head_index, 'AdjustedEBIT'] = head_row['EBIT'] + head_row['PPACFD'] + tail_row['MWSoldCFD']


    return df