import datetime
import json

def str_to_date(date_str):
    date_parts = date_str.split("-")
    date_parts = [int(i) for i in date_parts]
    return datetime.date(date_parts[0], date_parts[1], date_parts[2])

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

    # for k, v in fund_names.items():
    #     print k, v

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
        ft = str(raw_input(v["name"] + "(DEBT/EQUITY): "))
        existing_funds.append(
            {
                "isin": k,
                "name": v["name"],
                "type": ft
            }
        )

    with open("fund_info.json", 'w') as f:
        f.write(json.dumps(existing_funds, indent = 2))

    return existing_funds

def read_transactions(file_name, fund):
    all_trans = {"BUY": [], "SELL": []}
    with open(file_name) as f:
        line_num = 1
        for line in f:
            if line_num == 1:
                line_num = 2
                continue
            row = line.strip().split(",")
            if row[1] != fund: continue
            # print row[1], row[5], row[8], row[9], row[10]
            trans = {
                "date": str_to_date(row[5]),
                "date_str": row[5],
                "amount": float(row[8]),
                "units": float(row[9]),
                "nav": float(row[10])
            }
            all_trans[row[4]].append(trans)

    for k, v in all_trans.items():
        all_trans[k] = sorted(v, key = lambda trans: trans["date"])

    # for trans in all_trans:
    #     print trans, all_trans[trans]

    return all_trans

def calculate_tax(transactions, fund_type):
    period = 365
    if fund_type == "DEBT": period *= 3
    if len(transactions["SELL"]) > 0:
        buys = transactions["BUY"]
        for sale in transactions["SELL"]:
            units = sale["units"]
            amount = sale["amount"]
            date = sale["date"]
            buy_units = 0
            buy_amount = 0
            loop = True
            while loop:
                # if buys[0]["units"] +
                None

    else:
        print "No gains yet"

def check_all(file_name):
    funds = populate_fund_info(file_name)
    for fund in funds:
        print fund["name"] + " (" + fund["isin"] + ")"
        calculate_tax(read_transactions(file_name, fund["isin"]), fund["type"])

if __name__ == "__main__":
    # read_fund_names("coin_order_history.csv")
    # read_transactions("coin_order_history.csv", "INF194K01Y29")
    check_all("coin_order_history.csv")
