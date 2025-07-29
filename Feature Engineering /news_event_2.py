"""
README · COLUMN REFERENCE
─────────────────────────
• **Date** – Calendar day attached to every market row (UTC).
• **Ticker** – Yahoo‑style symbol of the asset (e.g. *BTC‑USD*).
• **Open / High / Low / Close / Adj Close / Volume** – Daily OHLCV as
  downloaded from Yahoo Finance; *Adj Close* already accounts for splits
  or dividends (not relevant to crypto, but retained for stocks).

Sentiment block (prefixed **Sent_***, produced by an upstream social‑
media script and simply preserved here):
• **Sent_CumScore**  Total FinBERT polarity count ( +1 for *Positive*,
  –1 for *Negative*) aggregated over all social‑media snippets that day.
• **Sent_Confidence** Average model confidence across those snippets.
• **Sent_TextCount** Number of snippets processed.
• **Sent_NormScore** Sent_CumScore ÷ Sent_TextCount – gives the *mean*
  polarity per snippet.

News block (prefixed **News_***, built **in this file**):
• **News_Score** Same polarity count as above but over curated news
  articles (*Title + Summary + Body* per article).
• **News_Cnt**   Number of news articles on the date.
• **News_Conf**  Mean FinBERT confidence on those articles.
• **News_Norm**  News_Score ÷ News_Cnt.

Event detection:
• **Event_Flag** = 1 if *any* article that day contains at least one
  finance‑event keyword (lexnlp dynamic vocabulary + starter fallback),
  else 0.

All columns are overwritten—never duplicated—on successive runs, so the
CSV schema stays clean..
"""

from __future__ import annotations

import datetime as dtm
import json
import pathlib
import re
import time
import warnings
from typing import Any, Iterable

import numpy as np
import pandas as pd
from dateutil.parser import parse as dt
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

ROOT        = pathlib.Path("/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/Historic Data Cry")
TICKERS     = ["WEMIX-USD", "TUSD-USD", "BTC-USD"]
DEFAULT_KW  = {
    "merger", "acquisition", "upgrade", "downgrade", "fork", "hack",
    "regulation", "ban", "lawsuit", "approval", "launch", "token", "ipo",
}

print("[init] loading FinBERT …", flush=True)
_tok  = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
_mdl  = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
_finbert = pipeline("sentiment-analysis", model=_mdl, tokenizer=_tok, device=-1, batch_size=16)

# dynamic keyword list via lexnlp (falls back to DEFAULT_KW)

def _iter_lexnlp_keywords() -> Iterable[str]:
    try:
        import lexnlp.extract.en.events as lxev  # type: ignore
    except ModuleNotFoundError:
        return []
    kws: set[str] = set()
    for name in dir(lxev):
        if name.startswith("get_") and name.endswith(("_verbs", "_nouns")):
            fn = getattr(lxev, name, None)
            if callable(fn):
                try:
                    kws.update(fn())
                except Exception:
                    pass
    return {k.lower() for k in kws if k.isalpha() and len(k) > 2}

_EVENT_KW = _iter_lexnlp_keywords() or DEFAULT_KW
EV_PATTERNS = re.compile(r"\b(" + "|".join(map(re.escape, _EVENT_KW)) + r")\b", re.I)

_rx_url  = re.compile(r"http\S+")
_rx_punc = re.compile(r"[^\w\s]")

def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", _rx_punc.sub("", _rx_url.sub("", t))).strip()

def _flatten(obj: Any) -> str:
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, (list, tuple, set)):
        return " ".join(_flatten(x) for x in obj)
    if isinstance(obj, dict):
        return " ".join(_flatten(v) for v in obj.values())
    return str(obj)

def _sent_score(text: str, max_len: int = 512, overlap: int = 50):
    ids = _tok(_clean(text), return_tensors="pt", truncation=False, add_special_tokens=False)["input_ids"][0]
    pos = neg = conf = 0.0
    for i in range(0, len(ids), max_len - overlap):
        seg = _tok.decode(ids[i : i + max_len], skip_special_tokens=True)
        out = _finbert(seg, truncation=True, max_length=max_len)[0]
        if out["label"] == "Positive":
            pos += 1
        elif out["label"] == "Negative":
            neg += 1
        conf += out["score"]
    return pos - neg, conf / max(pos + neg, 1)

def merge_overwrite(df: pd.DataFrame, other: pd.DataFrame, on: str) -> pd.DataFrame:
    if other.empty:
        return df
    dup = [c for c in other.columns if c in df.columns and c != on]
    if dup:
        df = df.drop(columns=dup)
    return df.merge(other, on=on, how="left")

def build_daily_frames(news_json: Any):
    # Accept both dict and bare list without raising attribute errors
    if isinstance(news_json, dict):
        arts = news_json.get("articles", [])
    else:
        arts = news_json
    sent, evt = [], []
    for art in arts:
        date = pd.to_datetime(dt(art.get("Date") or art.get("date")).date())
        txt  = _flatten([art.get("Title"), art.get("Summary"), art.get("Body")])
        s, c = _sent_score(txt)
        sent.append({"Date": date, "News_Score": s, "News_Conf": c})
        evt.append({"Date": date, "Event_Flag": int(bool(EV_PATTERNS.search(txt)))})

    daily = (
        pd.DataFrame(sent)
        .groupby("Date")
        .agg(News_Score=("News_Score", "sum"),
             News_Cnt=("News_Score", "count"),
             News_Conf=("News_Conf", "mean"))
        .reset_index()
    )
    if not daily.empty:
        daily["News_Norm"] = daily["News_Score"] / daily["News_Cnt"]

    evt_df = pd.DataFrame(evt).groupby("Date").max().reset_index() if evt else pd.DataFrame()
    return daily, evt_df

def _process_ticker(ticker: str):
    td = ROOT / ticker
    master_csv = td / f"{ticker}_merged_master.csv"
    news_json  = td / f"{ticker}_news.json"
    if not (master_csv.exists() and news_json.exists()):
        print(f"[skip] {ticker}")
        return
    master = pd.read_csv(master_csv, parse_dates=["Date"])
    with open(news_json) as f:
        daily, evt = build_daily_frames(json.load(f))
    master = merge_overwrite(master, daily, "Date")
    master = merge_overwrite(master, evt, "Date")
    for col in ["News_Score", "News_Cnt", "News_Conf", "News_Norm", "Event_Flag"]:
        if col not in master.columns:
            master[col] = 0
    master[["News_Score", "News_Cnt", "News_Conf", "News_Norm", "Event_Flag"]] = (
        master[["News_Score", "News_Cnt", "News_Conf", "News_Norm", "Event_Flag"]].fillna(0)
    )
    if "FwdRet_7d" in master.columns:
        master = master.drop(columns=["FwdRet_7d"])
    master.to_csv(master_csv, index=False)
    print(f"[done] {ticker}")

def main():
    t0 = time.time()
    for tic in TICKERS:
        try:
            _process_ticker(tic)
        except Exception as e:
            print(f"[error] {tic}: {e}")
    print("Finished in", dtm.timedelta(seconds=time.time() - t0))

if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()
