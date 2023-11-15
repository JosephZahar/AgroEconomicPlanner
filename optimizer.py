from pulp import *
import warnings
warnings.filterwarnings("ignore")

# Decisions Variables

# Continuous Variables
rice_types = {
    'super': {'buy': ['dec', 'jan', 'feb', 'mar'],
              'pay': ['mar', 'apr', 'may', 'june', 'jul', 'aug'],
              'sell': ['feb', 'mar', 'apr', 'may', 'june', 'jul', 'aug', 'sept', 'oct', 'nov', 'dec_2', 'jan_2', 'feb_2', 'mar_2', 'apr_2']},
    'kanait': {'buy': ['dec', 'jan', 'feb', 'mar', 'april', 'may'],
               'pay': ['mar', 'apr', 'may', 'june', 'jul', 'aug', 'sept', 'oct'],
               'sell': ['mar', 'apr', 'may', 'june', 'jul', 'aug', 'sept', 'oct', 'nov', 'dec_2', 'jan_2', 'feb_2', 'mar_2', 'apr_2']},
    'cheap': {'buy': ['sept', 'oct', 'nov'],
            'pay': ['dec_2', 'jan_2', 'feb_2', 'mar_2', 'apr_2'],
            'sell': ['dec_2', 'jan_2', 'feb_2', 'mar_2', 'apr_2']}
}

deposit_perc = 0.15
init_investment = 300000
sale_profit = [1.13]*len(rice_types['super']['buy']) + \
              [1.18]*len(rice_types['kanait']['buy']) + \
              [1.12]*len(rice_types['cheap']['buy'])

rice_vars_dict = {}
for rices, operations in rice_types.items():
    for i in range(1, len(operations['buy'])+1):
        rice_vars_dict[f"{rices}_{i}"] = {}
        rice_vars_dict[f"price_{rices}_{i}"] = LpVariable(f"price_{rices}_{i}", lowBound=0, cat='Integer')
        for operation, months in operations.items():
            if operation == 'buy':
                rice_vars_dict[f"{rices}_{i}"][operation] = {months[i-1]: LpVariable(f"{rices}_{i}_{operation}_{months[i-1]}", upBound=0, cat='Integer')}
            elif operation == 'pay':
                rice_vars_dict[f"{rices}_{i}"][operation] = LpVariable.dicts(f"{rices}_{i}_{operation}", months[i-1:], upBound=0, cat='Integer')
            else:
                rice_vars_dict[f"{rices}_{i}"][operation] = LpVariable.dicts(f"{rices}_{i}_{operation}", months[i-1:], lowBound=0, cat='Integer')

months = ['dec', 'jan', 'feb', 'mar', 'apr', 'may', 'june', 'jul', 'aug', 'sept', 'oct', 'nov', 'dec_2', 'jan_2', 'feb_2', 'mar_2', 'apr_2']
bank_vars = {month: LpVariable(f"bank_{month}", lowBound=0, cat='Integer') for month in months}

# # Objective Function (maximize total cashflow)
maxProfit = LpProblem("Rice_Trade_Scheduler", LpMaximize)
# maxProfit += sum(bank_vars[month] for month in months)
maxProfit += bank_vars[months[-1]]



rices = ['super_1', 'super_2', 'super_3', 'super_4',
        'kanait_1', 'kanait_2', 'kanait_3', 'kanait_4', 'kanait_5', 'kanait_6',
        'cheap_1', 'cheap_2', 'cheap_3']
ops = ['buy', 'pay', 'sell']

# # Constraints
for i in range(len(months)):
    if i == 0:
        prev = init_investment
    else:
        prev = bank_vars[months[i-1]]

    maxProfit += bank_vars[months[i]] == prev + lpSum(
        [rice_vars_dict[r][op][months[i]] for r in rices for op in ops if
         months[i] in rice_vars_dict[r][op]])

    maxProfit += prev >= -lpSum(
        [rice_vars_dict[r][op][months[i]] for r in rices for op in ops[:2] if
         months[i] in rice_vars_dict[r][op]])

for r,profit in zip(rices, sale_profit):
    maxProfit += rice_vars_dict[f"price_{r}"] == lpSum(
            [rice_vars_dict[r][op][month] for op in ops[:2] for month in months if
             month in rice_vars_dict[r][op]])


    maxProfit += lpSum([rice_vars_dict[r]['buy'][month] for month in months if
                     month in rice_vars_dict[r]['buy']]) == rice_vars_dict[f"price_{r}"]*deposit_perc

    maxProfit += lpSum([rice_vars_dict[r]['sell'][month] for month in months if
                        month in rice_vars_dict[r]['sell']]) == rice_vars_dict[f"price_{r}"] * profit



solver = CPLEX_CMD(path='/Applications/CPLEX_Studio221/cplex/bin/x86-64_osx/cplex')
maxProfit.solve(solver)

print("Status:", LpStatus[maxProfit.status])
for v in maxProfit.variables():
    if v.varValue > 0:
        print(v.name, "=", v.varValue)