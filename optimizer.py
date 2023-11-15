from pulp import *
import warnings
warnings.filterwarnings("ignore")

# Decisions Variables

# Continuous Variables
rice_types = {
    'super': {'buy': ['dec', 'jan', 'feb', 'mar'],
              'pay': ['mar', 'apr', 'may', 'june'],
              'sell': ['feb', 'mar', 'apr', 'may', 'june', 'jul', 'aug', 'sept', 'oct', 'nov', 'dec_2', 'jan_2', 'feb_2']},
    'kanait': {'buy': ['dec', 'jan', 'feb', 'mar', 'april', 'may'],
               'pay': ['mar', 'apr', 'may', 'june', 'jul', 'aug'],
               'sell': ['mar', 'apr', 'may', 'june', 'jul', 'aug', 'sept', 'oct', 'nov', 'dec_2', 'jan_2', 'feb_2']},
    '386': {'buy': ['sept', 'oct', 'nov'],
            'pay': ['dec_2', 'jan_2', 'feb_2'],
            'sell': ['dec_2', 'jan_2', 'feb_2']}
}

deposit_perc = 0.15
init_investment = 300000

rice_vars_dict = {}
for rice, operations in rice_types.items():
    for i in range(1, len(operations['buy'])+1):
        rice_vars_dict[f"{rice}_{i}"] = {}
        rice_vars_dict[f"price_{rice}_{i}"] = LpVariable(f"price_{rice}_{i}", lowBound=0, cat='Integer')
        for operation, months in operations.items():
            rice_vars_dict[f"{rice}_{i}"][operation] = LpVariable.dicts(f"{rice}_{i}_{operation}", months, lowBound=0, cat='Integer')
            if operation == 'buy':
                for month in months:
                    rice_vars_dict[f"is_buy_{month}_{rice}_{i}?"] = LpVariable(f"price_{rice}_{i}", lowBound=0, upBound=1, cat='Integer')

months = ['dec', 'jan', 'feb', 'mar', 'april', 'may', 'june', 'jul', 'aug', 'sept', 'oct', 'nov', 'dec_2', 'jan_2', 'feb_2']
bank_vars = {month: LpVariable(f"bank_{month}", lowBound=0, cat='Integer') for month in months}

# # Objective Function (maximize total cashflow)
maxProfit = LpProblem("Rice_Trade_Scheduler", LpMaximize)
maxProfit += sum(bank_vars[month] for month in months)

rice = ['super_1', 'super_2', 'super_3', 'super_4',
        'kanait_1', 'kanait_2', 'kanait_3', 'kanait_4', 'kanait_5', 'kanait_6',
        '386_1', '386_2', '386_3']
op = ['buy', 'sell', 'pay']
# # Constraints
for i in range(len(months)):
    if i == 0:
        prev = init_investment
    else:
        prev = bank_vars[months[i-1]]

    maxProfit += bank_vars[months[i]] == prev + lpSum(
        [rice_vars_dict[r][o][months[i]] for r in rice for o in op if
         months[i] in rice_vars_dict[r][o]])










# solver = CPLEX_CMD(path='/Applications/CPLEX_Studio221/cplex/bin/x86-64_osx/cplex')
# max_profit.solve(solver)
#
# # %%
#
# print("Status:", LpStatus[max_profit.status])
# for v in max_profit.variables():
#     if v.varValue > 0:
#         print(v.name, "=", v.varValue)