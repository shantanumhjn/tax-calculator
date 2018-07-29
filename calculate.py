import datetime
import json
from optparse import OptionParser
import os

SHOW_LEVEL_DEBUG = 1
SHOW_LEVEL_INFO = 2
SHOW_LEVEL_CURRENT = SHOW_LEVEL_INFO

SAVE_TO_FILE = False

def show(msg, level = SHOW_LEVEL_DEBUG):
    if level >= SHOW_LEVEL_CURRENT:
        print msg

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

    ret_funds = []
    for fund in existing_funds:
        if fund_names.pop(fund["isin"], None):
            ret_funds.append(fund)

    for k, v in fund_names.items():
        ft = str(raw_input(v["name"] + "(DEBT/EQUITY): "))
        info = {
            "isin": k,
            "name": v["name"],
            "type": ft
        }
        existing_funds.append(info)
        ret_funds.append(info)


    existing_funds = sorted(existing_funds, key = lambda fund: fund["isin"])
    with open("fund_info.json", 'w') as f:
        f.write(json.dumps(existing_funds, indent = 2))

    return ret_funds

def read_transactions(file_name, fund):
    all_trans = {"BUY": [], "SELL": [], "isin": fund}
    with open(file_name) as f:
        line_num = 1
        for line in f:
            if line_num == 1:
                line_num = 2
                continue
            row = line.strip().split(",")
            if row[1] != fund or row[11] not in ["Allotted", "Redeemed"]: continue
            trans = {
                "date": str_to_date(row[5]),
                "date_str": row[5],
                "amount": float(row[8]),
                "units": float(row[9]),
                "nav": float(row[10])
            }
            all_trans[row[4]].append(trans)
            if not all_trans.has_key("name"):
                all_trans["name"] = row[2]

    for k, v in all_trans.items():
        if k in ('BUY', 'SELL'):
            all_trans[k] = sorted(v, key = lambda trans: trans["date"])

    return all_trans

def calculate_tax_int(sale, buys, fund_name, fund_type, tax, print_header):
    period = 365
    if fund_type == "DEBT": period *= 3

    units = sale["units"]
    amount = sale["amount"]
    nav = sale["nav"]
    date = sale["date"]
    date_str = sale["date_str"]
    # show(50*"-")
    # show("Sale on {}, units: {}, nav: {}".format(sale["date_str"], units, nav))
    # show(50*"-")
    total_buy_units = 0
    ltcg = 0
    stcg = 0
    print_format = "{:<10}{:<40}{:<15}{:<10}{:<15}{:<10}{:<10}{:<10}{}"
    header = ["FundType", "FundName", "BuyDate", "BuyCost", "SellDate", "SellCost", "Units", "Profit", "Duration"]
    if print_header:
        show("\n")
        show(print_format.format(*header), SHOW_LEVEL_DEBUG)
        show(print_format.format(*["-"*len(h) for h in header]))
    loop = True
    while loop:
        buy_units = buys[0]["units"]
        buy_date = buys[0]["date"]
        buy_date_str = buys[0]["date_str"]
        buy_amount = buys[0]["amount"]
        buy_nav = buys[0]["nav"]
        if round(buy_units + total_buy_units, 3) > units:
            loop = False
            buy_units = units - total_buy_units
            buys[0]["units"] -= buy_units
        elif round(buy_units + total_buy_units, 3) == units:
            loop = False
            buys = buys[1:]
        else:
            buys = buys[1:]

        total_buy_units += buy_units

        buy_cost = buy_units * buy_nav
        sell_cost = buy_units * nav
        profit = (buy_units * nav) - (buy_units * buy_nav)

        # within a single sell, we need to look
        # at only the time period
        time_diff = (date - buy_date).days
        if time_diff > period:
            ltcg += profit
        else:
            stcg += profit

        # figuring out the FY
        fy = date.year
        if date.month < 4: fy -= 1

        output = [fund_type, fund_name, buy_date.strftime("%d/%m/%Y"), round(buy_cost, 2), date.strftime("%d/%m/%Y"), round(sell_cost, 2), buy_units, round(profit, 2), time_diff]
        show(print_format.format(*output))
        if SAVE_TO_FILE:
            output = output[1:]
            output = output[:5]
            with open("output.csv", "a") as f:
                f.write(",".join([str(o) for o in output]) + "\n")


    # show("ltcg: {}, stcg: {}".format(ltcg, stcg), SHOW_LEVEL_DEBUG)

    # populate the tax object
    if not tax.has_key(fy):
        tax[fy] = {
            "DEBT": {
                "gain": {
                    "ltcg": 0,
                    "stcg": 0
                }, "loss": {
                    "ltcg": 0,
                    "stcg": 0
                }
            }, "EQUITY": {
                "gain": {
                    "ltcg": 0,
                    "stcg": 0
                }, "loss": {
                    "ltcg": 0,
                    "stcg": 0
                }
            }
        }

    if ltcg > 0: tax[fy][fund_type]["gain"]["ltcg"] += ltcg
    if ltcg < 0: tax[fy][fund_type]["loss"]["ltcg"] += ltcg
    if stcg > 0: tax[fy][fund_type]["gain"]["stcg"] += stcg
    if stcg < 0: tax[fy][fund_type]["loss"]["stcg"] += stcg

def calculate_tax(transactions, fund_type, tax):
    print_header = True
    fund_name = transactions["name"]
    if len(transactions["SELL"]) > 0:
        buys = transactions["BUY"]
        for sale in transactions["SELL"]:
            calculate_tax_int(sale, buys, fund_name, fund_type, tax, print_header)
            print_header = False
    # else:
    #     show("No Sells yet.")

def check_all(file_name):
    tax = {}
    funds = populate_fund_info(file_name)
    for fund in funds:
        # show("\n" + fund["name"] + " (" + fund["type"] + ")")
        calculate_tax(read_transactions(file_name, fund["isin"]), fund["type"], tax)

    show("\n\nOverall summary:", SHOW_LEVEL_INFO)
    print_format = "{:<8}{:<15}{:<15}{:<15}{:<15}{:<15}{:<15}{:<15}{:<15}"
    headers = ["FY", "Debt ST Gain", "Debt ST Loss", "Debt LT Gain", "Debt LT Loss", "Equity ST Gain", "Equity ST Loss", "Equity LT Gain", "Equity LT Loss"]
    show(print_format.format(*headers), SHOW_LEVEL_INFO)
    show(print_format.format(*['-' * len(h) for h in headers]), SHOW_LEVEL_INFO)
    for fy in sorted(tax.keys()):
        d_st_gain = round(tax[fy]["DEBT"]["gain"]["stcg"], 2)
        d_st_loss = round(tax[fy]["DEBT"]["loss"]["stcg"], 2)
        d_lt_gain = round(tax[fy]["DEBT"]["gain"]["ltcg"], 2)
        d_lt_loss = round(tax[fy]["DEBT"]["loss"]["ltcg"], 2)
        e_st_gain = round(tax[fy]["EQUITY"]["gain"]["stcg"], 2)
        e_st_loss = round(tax[fy]["EQUITY"]["loss"]["stcg"], 2)
        e_lt_gain = round(tax[fy]["EQUITY"]["gain"]["ltcg"], 2)
        e_lt_loss = round(tax[fy]["EQUITY"]["loss"]["ltcg"], 2)
        show(print_format.format(fy, d_st_gain, d_st_loss, d_lt_gain, d_lt_loss, e_st_gain, e_st_loss, e_lt_gain, e_lt_loss), SHOW_LEVEL_INFO)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "-f", "--file",
        dest = "filename", metavar = "FILE",
        help = "File name to read data from (required)"
    )
    parser.add_option(
        "-d", "--debug",
        action = "store_true", default = False, dest = "debug",
        help = "Print a lot more data"
    )
    parser.add_option(
        "-s", "--save",
        action = "store_true", default = False, dest = "save",
        help = "saves transactions to a file (csv)"
    )

    (options, args) = parser.parse_args()
    if not options.filename:
        parser.error("filename is required!")

    if options.debug: SHOW_LEVEL_CURRENT = SHOW_LEVEL_DEBUG

    if options.save:
        SAVE_TO_FILE = True
        try:
            os.remove("output.csv")
        except OSError as e:
            print "unable to cleanup old output file"

    check_all(options.filename)
