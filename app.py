from flask import Flask, send_file
import tushare as ts
import pandas as pd
import datetime as dt
from pathlib import Path

app = Flask(__name__)

TOKEN = "在Render里设置，不写这里"
ts.set_token(TOKEN)
pro = ts.pro_api()

WATCHLIST = ["600000.SH", "000001.SZ", "300750.SZ"]

OUT = Path("result.xlsx")

def calc(df):
    df = df.sort_values("trade_date")
    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["vol"]

    return {
        "price": close.iloc[-1],
        "ma20": close.rolling(20).mean().iloc[-1],
        "ma60": close.rolling(60).mean().iloc[-1],
        "h20": high.rolling(20).max().iloc[-1],
        "l20": low.rolling(20).min().iloc[-1],
        "vol": vol.iloc[-1],
        "vol20": vol.rolling(20).mean().iloc[-1],
    }

@app.route("/")
def run():
    rows = []

    end = dt.datetime.now().strftime("%Y%m%d")
    start = (dt.datetime.now() - dt.timedelta(days=200)).strftime("%Y%m%d")

    for code in WATCHLIST:
        df = pro.daily(ts_code=code, start_date=start, end_date=end)
        if df.empty:
            continue

        f = calc(df)

        signal = "🟢" if f["price"] > f["ma20"] > f["ma60"] else "🔴"

        rows.append({
            "code": code,
            "price": f["price"],
            "ma20": f["ma20"],
            "ma60": f["ma60"],
            "h20": f["h20"],
            "l20": f["l20"],
            "vol": f["vol"],
            "vol20": f["vol20"],
            "signal": signal,
        })

    out = pd.DataFrame(rows)
    out.to_excel(OUT, index=False)

    return send_file(OUT, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
