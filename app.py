import os
import datetime as dt
from pathlib import Path

import pandas as pd
import tushare as ts
from flask import Flask, send_file, Response

app = Flask(__name__)

# 从 Render 环境变量读取（不要把 token 写进代码）
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "").strip()
if TUSHARE_TOKEN:
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
else:
    pro = None

WATCHLIST = ["600000.SH", "000001.SZ", "300750.SZ"]
OUT = Path("result.xlsx")


def calc(df: pd.DataFrame) -> dict:
    df = df.sort_values("trade_date")
    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["vol"]

    return {
        "price": float(close.iloc[-1]),
        "ma20": float(close.rolling(20).mean().iloc[-1]),
        "ma60": float(close.rolling(60).mean().iloc[-1]),
        "h20": float(high.rolling(20).max().iloc[-1]),
        "l20": float(low.rolling(20).min().iloc[-1]),
        "vol": float(vol.iloc[-1]),
        "vol20": float(vol.rolling(20).mean().iloc[-1]),
    }


@app.route("/")
def run():
    if pro is None:
        return Response(
            "TUSHARE_TOKEN 未设置：请到 Render -> Service -> Environment 添加变量 TUSHARE_TOKEN。",
            status=500,
            mimetype="text/plain",
        )

    rows = []
    end = dt.datetime.now().strftime("%Y%m%d")
    start = (dt.datetime.now() - dt.timedelta(days=220)).strftime("%Y%m%d")

    for code in WATCHLIST:
        df = pro.daily(ts_code=code, start_date=start, end_date=end)
        if df is None or df.empty:
            continue
        if len(df) < 60:
            continue

        f = calc(df)

        # 简单信号灯：价>MA20>MA60 = 🟢，否则 🔴（后面我们再升级成你“三国纪律版”）
        signal = "🟢" if (f["price"] > f["ma20"] > f["ma60"]) else "🔴"

        rows.append(
            {
                "code": code,
                "price": f["price"],
                "ma20": f["ma20"],
                "ma60": f["ma60"],
                "h20": f["h20"],
                "l20": f["l20"],
                "vol": f["vol"],
                "vol20": f["vol20"],
                "signal": signal,
            }
        )

    out = pd.DataFrame(rows)
    out.to_excel(OUT, index=False)

    return send_file(OUT, as_attachment=True)


if __name__ == "__main__":
    # Render 会给 PORT 环境变量；本地运行则默认 10000
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
