#!/usr/bin/env python3
import json, re, pathlib, pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

def clean(t): return re.sub(r'\s+', ' ', re.sub(r'[^a-zA-Z0-9\s]', '', re.sub(r'http\S+', '', t or ''))).strip()

def finbert(text, nlp, tok, sz=512, ov=50):
    ids = tok(clean(text), return_tensors="pt", truncation=False, add_special_tokens=False)["input_ids"][0]
    pos = neg = conf = 0
    for i in range(0, len(ids), sz - ov):
        out = nlp(tok.decode(ids[i:i+sz], skip_special_tokens=True), truncation=True, max_length=sz)[0]
        if out["label"] == "Positive": pos += 1
        elif out["label"] == "Negative": neg += 1
        conf += out["score"]
    cnt = (pos + neg) or 1
    return ("Positive" if pos>neg else "Negative" if neg>pos else "Neutral", pos - neg, conf/cnt)

def news_frames(obj, nlp, tok):
    arts = obj.get("articles", []) if isinstance(obj, dict) else obj
    det = []
    for a in arts:
        txt = ". ".join([a.get("Title",""), a.get("Summary","")] + a.get("Body", []))
        lab, sc, cf = finbert(txt, nlp, tok)
        det.append({"Date": a["Date"], "Title": a.get("Title",""), "Sent_Label": lab,
                    "Sent_Score": sc, "Sent_Conf": cf})
    if not det:
        empty_cols = ["Date","News_CumScore","News_TextCount","News_Conf","News_NormScore"]
        return pd.DataFrame(det), pd.DataFrame(columns=empty_cols)
    det_df = pd.DataFrame(det)
    det_df["Date"] = pd.to_datetime(det_df["Date"])
    daily = (det_df.groupby("Date")
               .agg(News_CumScore=('Sent_Score','sum'),
                    News_TextCount=('Sent_Score','count'),
                    News_Conf=('Sent_Conf','mean'))
               .reset_index())
    daily["News_NormScore"] = daily["News_CumScore"] / daily["News_TextCount"]
    return det_df, daily

def main():
    tickers = ["WEMIX-USD","XAUT-USD"]
    root = pathlib.Path("/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/Historic Data Cry")
    tok = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    mdl = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
    nlp = pipeline("sentiment-analysis", model=mdl, tokenizer=tok, device=-1, batch_size=16)

    for t in tickers:
        mpath = root / t / f"{t}_merged_master.csv"
        npath = root / t / f"{t}_news.json"
        if not mpath.exists(): continue
        master = pd.read_csv(mpath, parse_dates=["Date"])
        if npath.exists():
            det, daily = news_frames(json.load(open(npath)), nlp, tok)
            det.to_csv(root / t / f"{t}_news_detailed_scores.csv", index=False)
            daily["Date"] = pd.to_datetime(daily["Date"])
            master = master.merge(daily, on="Date", how="left")
            fill = {"News_CumScore":0,"News_TextCount":0,"News_Conf":0,"News_NormScore":0}
            master.fillna(fill, inplace=True)
        master.to_csv(mpath, index=False)

if __name__ == "__main__":
    main()
