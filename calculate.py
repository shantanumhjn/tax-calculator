import datetime
import json
from optparse import OptionParser

SHOW_LEVEL_DEBUG = 1
SHOW_LEVEL_INFO = 2
SHOW_LEVEL_CURRENT = SHOW_LEVEL_INFO

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

    for k, v in all_trans.items():
        if k != 'isin':
            all_trans[k] = sorted(v, key = lambda trans: trans["date"])

    return all_trans

def calculate_tax_int(sale, buys, period, tax):
    units = sale["units"]
    amount = sale["amount"]
    nav = sale["nav"]
    date = sale["date"]
    show(50*"-")
    show("Sale on {}, units: {}, nav: {}".format(sale["date_str"], units, nav))
    show(50*"-")
    total_buy_units = 0
    ltcg = 0
    stcg = 0
    print_format = "{:<15}{:<10}{:<10}{:<10}{}"
    header = ["Date", "Units", "nav", "Profit", "Duration"]
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
        show(print_format.format(buy_date_str, buy_units, buy_nav, round(profit, 2), time_diff))

    show("ltcg: {}, stcg: {}".format(ltcg, stcg), SHOW_LEVEL_DEBUG)

    # populate the tax object
    if not tax.has_key(fy):
        tax[fy] = {
            "gain": {
                "ltcg": 0,
                "stcg": 0
            }, "loss": {
                "ltcg": 0,
                "stcg": 0
            }
        }
    if ltcg > 0: tax[fy]["gain"]["ltcg"] += ltcg
    if ltcg < 0: tax[fy]["loss"]["ltcg"] += ltcg
    if stcg > 0: tax[fy]["gain"]["stcg"] += stcg
    if stcg < 0: tax[fy]["loss"]["stcg"] += stcg

def calculate_tax(transactions, fund_type, tax):
    period = 365
    if fund_type == "DEBT": period *= 3

    if len(transactions["SELL"]) > 0:
        buys = transactions["BUY"]
        for sale in transactions["SELL"]:
            calculate_tax_int(sale, buys, period, tax)
    else:
        show("No Sells yet.")

def check_all(file_name):
    tax = {}
    funds = populate_fund_info(file_name)
    for fund in funds:
        show("\n" + fund["name"] + " (" + fund["type"] + ")")
        calculate_tax(read_transactions(file_name, fund["isin"]), fund["type"], tax)

    show("\n\nOverall summary:", SHOW_LEVEL_INFO)
    print_format = "{:<8}{:<10}{:<10}{:<10}{:<10}"
    headers = ["FY", "ST Gain", "ST Loss", "LT Gain", "LT Loss"]
    show(print_format.format(*headers), SHOW_LEVEL_INFO)
    show(print_format.format(*['-' * len(h) for h in headers]), SHOW_LEVEL_INFO)
    for fy in sorted(tax.keys()):
        st_gain = round(tax[fy]["gain"]["stcg"], 2)
        st_loss = round(tax[fy]["loss"]["stcg"], 2)
        lt_gain = round(tax[fy]["gain"]["ltcg"], 2)
        lt_loss = round(tax[fy]["loss"]["ltcg"], 2)
        show(print_format.format(fy, st_gain, st_loss, lt_gain, lt_loss), SHOW_LEVEL_INFO)

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
    (options, args) = parser.parse_args()
    if not options.filename:
        parser.error("filename is required!")

    if options.debug: SHOW_LEVEL_CURRENT = SHOW_LEVEL_DEBUG

    check_all(options.filename)
