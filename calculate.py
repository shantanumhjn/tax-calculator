import datetime
import json
from argparse import ArgumentParser
import os

SHOW_LEVEL_DEBUG = 1
SHOW_LEVEL_INFO = 2
SHOW_LEVEL_CURRENT = SHOW_LEVEL_INFO

SAVE_TO_FILE = False

FILE_TYPE_ZERODHA = 'zerodha'
FILE_TYPE_KUVERA = 'kuvera'
FILE_TYPE = FILE_TYPE_ZERODHA

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

def populate_fund_types(trans):
    with open("fund_info.json") as f:
        f_content = f.read()
    if f_content is None or len(f_content) == 0:
        f_content = "[]"
    existing_funds = json.loads(f_content)

    fund_type_dict = {}
    for fund in existing_funds:
        fund_type_dict[fund['name']] = fund

    found_new_fund = False

    for k, v in trans.items():
        if not fund_type_dict.has_key(k):
            found_new_fund = True
            ft = str(raw_input(k + "(DEBT/EQUITY): "))
            if ft.lower().startswith('d'): ft = 'DEBT'
            if ft.lower().startswith('e'): ft = 'EQUITY'
            info = {
                "isin": v['isin'],
                "name": k,
                "type": ft
            }
            existing_funds.append(info)
            fund_type_dict[k] = info
        v['type'] = fund_type_dict[k]['type']

    if found_new_fund:
        existing_funds = sorted(existing_funds, key = lambda fund: fund["name"])
        with open("fund_info.json", 'w') as f:
            f.write(json.dumps(existing_funds, indent = 2))

FILE_READ_OBJECT = {
    FILE_TYPE_ZERODHA: {
        "name_index": 2,
        "isin_index": 1,
        "trans_type_index": 4,
        "other_attributes": [
            {"key": "date", "index": 5, "function": str_to_date,},
            {"key": "amount", "index": 8, "function": float,},
            {"key": "units", "index": 9, "function": float,},
            {"key": "nav", "index": 10, "function": float,},
        ],
    },
    FILE_TYPE_KUVERA: {
        "name_index": 2,
        "trans_type_index": 3,
        "other_attributes": [
            {"key": "date", "index": 0, "function": str_to_date,},
            {"key": "amount", "index": 7, "function": float,},
            {"key": "units", "index": 4, "function": float,},
            {"key": "nav", "index": 5, "function": float,},
        ],
    },
}

'''
    all_trans = {
        fund_name: {
            "buys": [],
            "sells": [],
            "fund_type": "type",
            "isin": "isin"
        }
    }
'''
def read_all_transactions(file_name):
    read_object = FILE_READ_OBJECT[FILE_TYPE]
    all_trans = {}
    with open(file_name) as f:
        file_content = f.read()
    first_line = True
    for line in file_content.split('\n'):
        if first_line:
            first_line = False
            continue
        line = line.strip()
        if not line: continue
        row = line.split(',')

        # special check for zerodha
        if FILE_TYPE == FILE_TYPE_ZERODHA:
            if row[11] not in ["Allotted", "Redeemed"]:
                continue
        fund_name = row[read_object["name_index"]]
        fund_isin = None
        if read_object.get("isin_index"):
            fund_isin = row[read_object.get("isin_index")]
        trans = {}
        for attrs in read_object["other_attributes"]:
            # trans[attrs["key"]] = attrs["function"](row[attrs["index"]])
            key = attrs["key"]
            index = attrs["index"]
            func = attrs["function"]
            trans[key] = func(row[index])

        if not all_trans.has_key(fund_name):
            all_trans[fund_name] = {
                "BUY": [],
                "SELL": [],
                "isin": fund_isin,
                "type": "DEBT",
                "name": fund_name,
            }
        trans_type = row[read_object["trans_type_index"]].upper()
        all_trans[fund_name][trans_type].append(trans)

    # populate fund type, DEBT or EQUITY
    populate_fund_types(all_trans)

    for k1, v1 in all_trans.items():
        for k2, v2 in v1.items():
            if k2 in ('BUY', 'SELL'):
                all_trans[k1][k2] = sorted(v2, key = lambda trans: trans["date"])

    return all_trans

def calculate_tax_int(sale, buys, fund_name, fund_type, tax, print_header):
    period = 365
    if fund_type == "DEBT": period *= 3

    units = sale["units"]
    amount = sale["amount"]
    nav = sale["nav"]
    date = sale["date"]
    # show(50*"-")
    # show("Sale on {}, units: {}, nav: {}".format(sale["date_str"], units, nav))
    # show(50*"-")
    total_buy_units = 0
    ltcg = 0
    stcg = 0
    print_format = "{:<10}{:<55}{:<15}{:<10}{:<15}{:<10}{:<10}{:<10}{}"
    header = ["FundType", "FundName", "BuyDate", "BuyCost", "SellDate", "SellCost", "Units", "Profit", "Duration"]
    if print_header:
        show("\n")
        show(print_format.format(*header), SHOW_LEVEL_DEBUG)
        show(print_format.format(*["-"*len(h) for h in header]))
    loop = True
    while loop:
        buy_units = buys[0]["units"]
        buy_date = buys[0]["date"]
        buy_amount = buys[0]["amount"]
        buy_nav = buys[0]["nav"]
        if round(buy_units + total_buy_units, 3) > units:
            loop = False
            buy_units = units - total_buy_units
            buys[0]["units"] -= buy_units
        elif round(buy_units + total_buy_units, 3) == units:
            loop = False
            buys.pop(0)
        else:
            buys.pop(0)

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

def calculate_tax(transactions, tax):
    print_header = True
    fund_name = transactions["name"]
    fund_type = transactions["type"]
    if len(transactions["SELL"]) > 0:
        buys = transactions["BUY"]
        for sale in transactions["SELL"]:
            calculate_tax_int(sale, buys, fund_name, fund_type, tax, print_header)
            print_header = False
    # else:
    #     show("No Sells yet.")

def check_all(file_name):
    tax = {}
    for trans in read_all_transactions(file_name).values():
        calculate_tax(trans, tax)

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
    parser = ArgumentParser(
        description=
            'Read mutual fund transaction files '
            'from Zerodha and calculate the tax.'
    )
    # action defaults to store
    parser.add_argument(
        "filename",
        action='store',
        help='file to read from'
    )
    parser.add_argument(
        "-t", "--filetype",
        default=FILE_TYPE_ZERODHA, choices=[FILE_TYPE_ZERODHA, FILE_TYPE_KUVERA],
        help='zerodha/kuvera format file'
    )
    parser.add_argument(
        "-d", "--debug",
        action = "store_true", default = False,
        help = "Print a lot more data"
    )
    parser.add_argument(
        "-s", "--save",
        action = "store_true", default = False,
        help = "saves transactions to a file (csv)"
    )

    args = parser.parse_args()

    if args.debug: SHOW_LEVEL_CURRENT = SHOW_LEVEL_DEBUG

    if args.save:
        SAVE_TO_FILE = True
        try:
            os.remove("output.csv")
        except OSError as e:
            print "unable to cleanup old output file: {}".format(e)

    FILE_TYPE = args.filetype

    check_all(args.filename)
