import json, re, os, pathlib, pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# ── helpers ──────────────────────────────────────────────────────────────
def clean_text(t: str) -> str:
    t = re.sub(r'http\S+', '', t or '')
    t = re.sub(r'[^a-zA-Z0-9\s]', '', t)
    return re.sub(r'\s+', ' ', t).strip()

def analyze_sentiment_finbert(text, nlp, tok, chunk_size=512, overlap=50):
    text = clean_text(text)
    token_ids = tok(text, return_tensors="pt", truncation=False,
                    add_special_tokens=False)["input_ids"][0]
    scores, confs = {"Positive":0,"Neutral":0,"Negative":0}, []
    for start in range(0, len(token_ids), chunk_size - overlap):
        chunk = tok.decode(token_ids[start:start+chunk_size], skip_special_tokens=True)
        out = nlp(chunk, truncation=True, max_length=chunk_size)[0]
        scores[out["label"]] += 1
        confs.append(out["score"])
    return max(scores, key=scores.get), scores["Positive"]-scores["Negative"], sum(confs)/len(confs) if confs else 0.0

# ── JSON parser ──────────────────────────────────────────────────────────
def process_data(records, source, nlp, tok):
    rows = []

    # helper must be defined *before* use
    def _add_row(txt, typ, date):
        if not txt: return
        s, sc, cf = analyze_sentiment_finbert(txt, nlp, tok)
        rows.append(dict(Source=source, Date=date, Text=txt,
                         Sentiment=s, Score=sc,
                         Confidence=cf, Type=typ))

    for day in records:
        date = day.get("Date") or day.get("date")
        for comment in day.get("comments", []):
            for c in comment.get("content", []):
                _add_row(c.get("text"), "Main", date)
            for rep in comment.get("replies", []):
                if isinstance(rep, dict) and "content" in rep:
                    for rc in rep["content"]:
                        _add_row(rc.get("text"), "Reply", date)
                elif isinstance(rep, dict):
                    _add_row(rep.get("text"), "Reply", date)
                elif isinstance(rep, str):
                    _add_row(rep, "Reply", date)
    return rows

# ── aggregate daily ──────────────────────────────────────────────────────
def calculate_daily_scores(df):
    df["Date"] = pd.to_datetime(df["Date"])
    daily = (df.groupby("Date")
               .agg(Sent_CumScore=('Score','sum'),
                    Sent_Confidence=('Confidence','mean'),
                    Sent_TextCount=('Text','count'))
               .reset_index())
    daily["Sent_NormScore"] = daily["Sent_CumScore"] / daily["Sent_TextCount"]
    return daily

# ── main ─────────────────────────────────────────────────────────────────
def main():
    tickers = ["WEMIX-USD","XAUT-USD"]
    base_dir = pathlib.Path("/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/Historic Data Cry")
    master_frames = []

    print("Loading FinBERT …")
    tok = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    mdl = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
    nlp = pipeline("sentiment-analysis", model=mdl, tokenizer=tok,
                   device=-1, batch_size=16)

    for tic in tickers:
        print(f"\n▶︎ {tic}")
        jpath = base_dir / tic / f"{tic}_merge_comments.json"
        if not jpath.exists():
            print("  ↪ missing JSON:", jpath); continue
        rows = process_data(json.load(open(jpath)), "Merged", nlp, tok)
        if not rows:
            print("  ↪ no sentiments"); continue
        df_daily = calculate_daily_scores(pd.DataFrame(rows))

        price_path = base_dir / tic / f"{tic}.csv"
        if not price_path.exists():
            print("  ↪ missing price CSV:", price_path); continue
        price_df = pd.read_csv(price_path, parse_dates=["Date"])
        price_df["Ticker"] = tic

        merged = price_df.merge(df_daily, on="Date", how="left")
        out_dir = base_dir / tic; out_dir.mkdir(parents=True, exist_ok=True)
        merged.to_csv(out_dir / f"{tic}_merged_master.csv", index=False)
        print("  ✓ merged CSV saved.")
        master_frames.append(merged)

    if master_frames:
        pd.concat(master_frames, ignore_index=True).to_csv(base_dir / "master_dataset.csv", index=False)
        print("\n🌟  All tickers combined → master_dataset.csv")

if __name__ == "__main__":
    main()
