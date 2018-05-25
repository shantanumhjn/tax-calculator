import datetime
import json


# transactions = {
#     "BUY": [
#
#     ],
#     "SELL": [
#
#     ]
# }
#
# total = {
#     "BUY": 0,
#     "SELL": 0
# }

def read_fund_names(fname):
    fund_names = {}
    with open(fname) as f:
        line_num = 1
        for line in f:
            if line_num == 1:
                line_num = 2
                continue
            row = line.strip().split(",")
            # fund_names[(row[1], row[2])] = fund_names.get((row[1], row[2]), 0) + 1
            if not fund_names.has_key(row[1]):
                fund_names[row[1]] = {"name": row[2], "count": 0}
            fund_names[row[1]]["count"] += 1

    for k, v in fund_names.items():
        print k, v

    return fund_names

def populate_fund_info(file_name):
    fund_names = read_fund_names(file_name)

    f_content = None
    with open("fund_info.json") as f:
        f_content = f.read()

    if f_content == None or len(f_content) == 0:
        f_content = "[]"

    existing_funds = json.loads(f_content)
    for fund in existing_funds:
        fund_names.pop(fund["isin"], None)

    for k, v in fund_names.items():
        existing_funds.append(
            {
                "isin": k,
                "name": v["name"],
                "type": "EQUITY"
            }
        )

    with open("fund_info.json", 'w') as f:
        f.write(json.dumps(existing_funds, indent = 2))

def read_transactions(file_name, fund):
    all_trans = []
    with open(file_name) as f:
        line_num = 1
        for line in f:
            if line_num == 1:
                line_num = 2
                continue
            row = line.strip().split(",")
            if row[1] != fund: continue
            print row[1], row[5], row[8], row[9], row[10]
            # trans = {
            #     "date": row[5],
            #     "amount": float(row[8]),
            #     "units": float(row[9]),
            #     "nav": float(row[10])
            # }
            # all_trans.append(trans)

    for trans in all_trans:
        print trans

    return all_trans

if __name__ == "__main__":
    # read_fund_names("coin_order_history.csv")
    # read_transactions("coin_order_history.csv", "INF194K01Y29")
    populate_fund_info("coin_order_history.csv")

# with open("coin_order_history.csv") as f:
#     line_num = 1
#     for line in f:
#         if line_num = 1: continue
#         row = line.strip().split(",")
#         if row[1] == isin:
#             trans = {
#                 "date": row[5],
#                 "amount": float(row[8]),
#                 "units": float(row[9]),
#                 "nav": float(row[10])
#             }
#             transactions[row[4]].append(trans)
#             total[row[4]] += float(row[9])
#         line_num += 1
#
# # print json.dumps(transactions, indent = 2)
#
# for k, v in transactions.items():
#     transactions[k] = sorted(v, key = lambda trans: trans["date"])
#
#
# print json.dumps(transactions, indent = 2)
#
# for k, v in total.items():
#     total[k] = round(v, 3)
#
# print json.dumps(total, indent = 2)
