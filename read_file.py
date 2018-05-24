import datetime
import json


transactions = {
    "BUY": [

    ],
    "SELL": [

    ]
}

total = {
    "BUY": 0,
    "SELL": 0
}

with open("coin_order_history.csv") as f:
    isin = "INF109K01TX1"
    for line in f:
        row = line.strip().split(",")
        if row[1] == isin:
            trans = {
                "date": row[5],
                "amount": float(row[8]),
                "units": float(row[9]),
                "nav": float(row[10])
            }
            transactions[row[4]].append(trans)
            total[row[4]] += float(row[9])

# print json.dumps(transactions, indent = 2)

for k, v in transactions.items():
    transactions[k] = sorted(v, key = lambda trans: trans["date"])


print json.dumps(transactions, indent = 2)

for k, v in total.items():
    total[k] = round(v, 3)

print json.dumps(total, indent = 2)
