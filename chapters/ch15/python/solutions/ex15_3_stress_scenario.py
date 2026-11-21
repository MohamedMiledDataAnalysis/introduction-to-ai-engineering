# Exercise 15.3 - The stress scenario and an order check
# Run from the root of the repository:  python chapters/ch15/python/solutions/ex15_3_stress_scenario.py

def order_problems(obj):
    problems = []
    order = ["stress_scenario_rhp_eur", "unfavourable_scenario_rhp_eur",
             "moderate_scenario_rhp_eur", "favourable_scenario_rhp_eur"]
    values = [obj.get(f) for f in order if obj.get(f) is not None]
    if values != sorted(values):
        problems.append("scenario values are not in increasing order")
    return problems


hbma = {"stress_scenario_rhp_eur": 5030, "unfavourable_scenario_rhp_eur": 9520,
        "moderate_scenario_rhp_eur": 11840, "favourable_scenario_rhp_eur": 14210}
swapped = dict(hbma, stress_scenario_rhp_eur=14210, favourable_scenario_rhp_eur=5030)
print(order_problems(hbma) or "in order")
print(order_problems(swapped))
