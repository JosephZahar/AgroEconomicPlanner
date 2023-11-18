import pandas as pd
from pulp import *
import warnings
import plotly.figure_factory as ff
import plotly.io as pio
pio.templates.default = "plotly_white"
warnings.filterwarnings("ignore")

def generate_trade_schedule():

    def get_valid_number(prompt):
        while True:
            try:
                user_input = int(input(prompt))
                return user_input
            except ValueError:
                print("That's not a valid number! Please try again. \n")

    init_investment = get_valid_number("Please enter your initial investment: ")
    rice_supply = get_valid_number("Please enter the maximum rice supply: ")

    # Decisions Variables
    # Continuous Variables
    rice_types = {
        'super': {'buy': ['dec', 'jan', 'feb', 'mar'],
                  'pay': ['jan', 'feb', 'mar', 'apr', 'may', 'june', 'jul'],
                  'sell': ['jan', 'feb', 'mar', 'apr', 'may', 'june', 'jul']},
        'kanait': {'buy': ['dec', 'jan', 'feb', 'mar', 'apr'],
                   'pay': ['jan', 'feb', 'mar', 'apr', 'may', 'june', 'jul'],
                   'sell': ['feb', 'mar', 'apr', 'may', 'june', 'jul']},
        'cheap': {'buy': ['sept', 'oct'],
                  'pay': ['oct', 'nov', 'dec', 'jan', 'feb', 'mar'],
                  'sell': ['oct', 'nov']}
    }

    deposit_perc = 0.2
    super_profit = 1.13
    kanait_profit = [1.11, 1.17, 1.225, 1.225]
    cheap_profit = 1.07
    interests = [1.05, 1.05, 1.075, 1.1, 1.125]

    rice_vars_dict = {}
    for rices, operations in rice_types.items():
        for i in range(1, len(operations['buy']) + 1):
            rice_vars_dict[f"{rices}_{i}"] = {}
            rice_vars_dict[f"price_{rices}_{i}"] = LpVariable(f"price_{rices}_{i}", lowBound=0, cat='Continuous')
            for operation, months in operations.items():
                if operation == 'buy':
                    rice_vars_dict[f"{rices}_{i}"][operation] = {
                        months[i - 1]: LpVariable(f"{rices}_{i}_{operation}_{months[i - 1]}", upBound=0,
                                                  cat='Continuous')}
                elif operation == 'pay':
                    rice_vars_dict[f"{rices}_{i}"][operation] = LpVariable.dicts(f"{rices}_{i}_{operation}",
                                                                                 months[i - 1:i - 1 + 5], upBound=0,
                                                                                 cat='Continuous')
                else:
                    end_sell = 4
                    if rices == 'cheap':
                        end_sell = 2
                    rice_vars_dict[f"{rices}_{i}"][operation] = LpVariable.dicts(f"{rices}_{i}_{operation}",
                                                                                 months[i - 1:i - 1 + end_sell],
                                                                                 lowBound=0, cat='Continuous')

    months = ['sept', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may', 'june', 'jul']
    bank_vars = {month: LpVariable(f"bank_{month}", lowBound=0, cat='Continuous') for month in months}

    # # Objective Function (maximize total cashflow)
    maxProfit = LpProblem("Rice_Trade_Scheduler", LpMaximize)
    # maxProfit += sum(bank_vars[month] for month in months)
    maxProfit += bank_vars[months[-1]]

    rices = ['super_1', 'super_2', 'super_3', 'super_4',
             'kanait_1', 'kanait_2', 'kanait_3', 'kanait_4', 'kanait_5',
             'cheap_1', 'cheap_2']
    ops = ['buy', 'pay', 'sell']

    # # Constraints
    for i in range(len(months)):
        if i == 0:
            prev = init_investment
        else:
            prev = bank_vars[months[i - 1]]

        maxProfit += bank_vars[months[i]] == prev + lpSum(
            [rice_vars_dict[r][op][months[i]] for r in rices for op in ops if
             months[i] in rice_vars_dict[r][op]])

        maxProfit += prev >= -lpSum(
            [rice_vars_dict[r][op][months[i]] for r in rices for op in ops[:2] if
             months[i] in rice_vars_dict[r][op]])

    for r in rices:
        maxProfit += -rice_vars_dict[f"price_{r}"] == lpSum([
            rice_vars_dict[r][op][month] * (1 / interests[i]) if op == 'pay' else rice_vars_dict[r][op][month]
            for op in ops[:2] for i, month in enumerate(rice_vars_dict[r][op])
        ])

        maxProfit += lpSum([rice_vars_dict[r]['buy'][month] for month in rice_vars_dict[r]['buy']]) == -rice_vars_dict[
            f"price_{r}"] * deposit_perc

        maxProfit += rice_vars_dict[f"price_{r}"] <= rice_supply

        if r.startswith("super"):
            maxProfit += lpSum([rice_vars_dict[r]['sell'][month] for month in rice_vars_dict[r]['sell']]) == \
                         rice_vars_dict[
                             f"price_{r}"] * super_profit
        elif r.startswith("cheap"):
            maxProfit += lpSum([rice_vars_dict[r]['sell'][month] for month in rice_vars_dict[r]['sell']]) == \
                         rice_vars_dict[
                             f"price_{r}"] * cheap_profit
        else:
            maxProfit += lpSum([rice_vars_dict[r]['sell'][month] * (1 / kanait_profit[i]) for
                                i, month in enumerate(rice_vars_dict[r]['sell'])]) == rice_vars_dict[f"price_{r}"]

    solver = CPLEX_CMD(path='/Applications/CPLEX_Studio221/cplex/bin/x86-64_osx/cplex', msg=False)
    maxProfit.solve(solver)
    month_to_num = {'jan': 1,
                    'feb': 2,
                    'mar': 3,
                    'apr': 4,
                    'may': 5,
                    'june': 6,
                    'jul': 7,
                    'aug': 8,
                    'sept': 9,
                    'oct': 10,
                    'nov': 11,
                    'dec': 12}

    print("Status:", LpStatus[maxProfit.status])
    print(f'\n', f'*********> Final Cashflow: {"{:,.0f}".format(pulp.value(maxProfit.objective))} $')

    blue = 'rgb(180, 198, 231)'
    orange = 'rgb(248, 202, 173)'
    green = 'rgb(198, 224, 180)'
    results_df = pd.DataFrame()
    annotations = []
    colors = {}
    y = 0
    prev = 'None'
    BAR_WIDTH = 0.3

    for v in maxProfit.variables():
        if v.varValue != 0 and v.name.startswith(("super", 'kanait', 'cheap')) and abs(v.varValue) > 1:
            split_var = v.name.split('_')
            rice = split_var[0].capitalize() + ' ' + split_var[1]
            action = split_var[2]
            month = month_to_num[split_var[-1]]
            end_month = month + 1 if month < 12 else 1
            end_year = '2023' if end_month > 8 else '2024'
            start_year = '2023' if month > 8 else '2024'
            start_date = start_year + '-' + str(month) + '-1'
            end_date = end_year + '-' + str(end_month) + '-1'
            text_date = start_year + '-' + str(month) + '-15'
            results_df = results_df.append({'Task': rice, 'Start': start_date, 'Finish': end_date,
                                            'Value': "{:,.0f}".format(v.varValue), 'x': text_date, 'y': y},
                                           ignore_index=True)
            y += 1

            if v.name.startswith("super"):
                colors[rice] = blue
            elif v.name.startswith("kanait"):
                colors[rice] = orange
            else:
                colors[rice] = green

    results_df = results_df.sort_values(by=['Task', 'Start'], ascending=False)
    shape_df = results_df.groupby('Task').agg({'Start': 'min', 'Finish': 'max', 'y': ['min', 'max']})
    shape_df.columns = ['x0', 'x1', 'y0', 'y1']

    y = 0
    for i, row in results_df.iterrows():
        annotations.append(dict(x=row.x, y=y, text=row.Value, showarrow=False, font=dict(color='black')))
        y += 1

    fig = ff.create_gantt(results_df, index_col='Task', colors=colors,
                          group_tasks=False,
                          bar_width=BAR_WIDTH)
    fig['layout']['annotations'] = annotations
    fig.update_layout(yaxis=dict(showticklabels=False), width=1800, height=1000,
                      title=f'Rice Trade Schedule --> {"{:,.0f}".format(pulp.value(maxProfit.objective))} $ in one year')

    for i, row in shape_df.iterrows():
        fig.add_shape(type='rect',
                      x0=row.x0, y0=abs(row.y0 - y + 1) + BAR_WIDTH,
                      x1=row.x1, y1=abs(row.y1 - y + 1) - BAR_WIDTH,
                      line=dict(color='black'),
                      layer='above')
    fig.update_layout(
        xaxis=dict(
            tickmode='linear',
            dtick='M1',
            showgrid=True,
            gridcolor='LightGrey'
        )
    )

    fig.write_image('riceScheduler.png')
    fig.show()

if __name__ == '__main__':
    generate_trade_schedule()
