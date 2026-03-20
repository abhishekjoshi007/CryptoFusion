# CryptoFusion: A Temporal Graph-Aware Transformer Framework for Robust Cryptocurrency Forecasting and Adaptive Portfolio Optimization

> **Published at:** 2025 IEEE International Conference on Big Data (BigData)
> **DOI:** [10.1109/BIGDATA66926.2025.11402130](https://doi.org/10.1109/BIGDATA66926.2025.11402130)

**Authors:** Abhishek Joshi · Alihan Hadimlioglu · Nikhilesh Krishnakum Verma
*Texas A&M University–Corpus Christi*

---

## Overview

CryptoFusion is an end-to-end multimodal transformer framework that combines three tightly integrated components to forecast cryptocurrency returns and optimize portfolios:

1. **Temporal Graph Network (TGN) Sidecar** — dynamically models evolving inter-asset correlations via rolling Pearson windows, pruning weak edges (|ρ| < 0.2).
2. **Credibility-Aware LLM Event Summarizer** — filters low-credibility news (p_cred < 0.6 via FinBERT classifier) and generates 25-token summaries, benchmarked against VADER and TF-IDF.
3. **Risk-Aware RL Allocator (PPO / CVaR-PPO)** — translates predictions into portfolios with realistic maker/taker fees and liquidity-sensitive slippage.

Evaluated on the **top-200 coins from January 2017 – January 2025** across six market regimes, CryptoFusion achieves:

| Metric | Improvement vs. best baseline |
|--------|-------------------------------|
| RMSE | **−8.3%** |
| Directional Accuracy | **+8.7 pp** (65.5%) |
| Sharpe Ratio | **+0.29** (1.42 at 10 bps) |
| Sortino Ratio | 1.89 |
| Max Drawdown | −19.8% |

---

## Architecture

[CryptoFusion Architecture](assets/arch.png)


## Repository Structure

```
CryptoFusion/
├── CSV/
│   ├── Crypto.csv                     # Top-200 crypto ticker list
│   ├── Crypto_1.csv
│   └── macroeconomic_indicators.csv   # VIX, CPI, Fed Funds, BTC dominance
│
├── Data Extractions Scripts/
│   ├── historic_main.py               # OHLCV download via yfinance
│   ├── reddit_scrape.py               # Reddit sentiment scraper (PRAW)
│   ├── news.py                        # NY Times API news fetcher
│   ├── comments_main.py               # Comment aggregation
│   ├── holder.py                      # Holder utilities
│   └── News/
│       └── main.py                    # News pipeline entry point
│
├── Feature Engineering/
│   ├── finbert_1.py                   # FinBERT sentiment scoring (chunked)
│   └── news_event_2.py                # News FinBERT + NLP event detection
│
└── Helper/
    ├── catogeries.py                  # Asset category labeling
    ├── Combine categories.py          # Category merging
    ├── comments_merging.py            # Merge comment JSON files
    ├── file_mer.py                    # General file merging utilities
    └── microeconomic.py               # Microeconomic feature helpers
```

---

## Results

### Predictive Accuracy & Portfolio Performance (10 bps transaction costs)

[Results](assets/res_1png)
[Results](assets/res_2png)

### Sharpe Ratio by Market Regime

[Regime Analysis](assets/regime_sharpe.png)

CryptoFusion maintains Sharpe > 1.2 across all market regimes including the 2020 COVID-19 crash and the 2022 contagion.

### Ablation Study

[Ablation Results](assets/ablation.png) 

| Ablation | DA Drop | Sharpe Drop |
|----------|---------|-------------|
| Remove TGN | −18.3 pp | −0.21 |
| Replace LLM → TF-IDF | −6.8 pp | — |
| Replace LLM → VADER | −4.1 pp | — |
| Remove RL Allocator | — | below 1.0 |

### Sensitivity: Risk Penalty λ

[Lambda Sensitivity](assets/lambda_sensitivity.png) 

Sharpe remains > 1.2 across λ ∈ [0.1, 1.0], with peak performance at λ = 0.25 (PPO) and λ = 0.50 (CVaR-PPO).

### Event-Aligned Returns (Terra/Luna Collapse)

<[Event Aligned Returns](assets/event_aligned_returns.png) 

CryptoFusion underperforms on the shock day (+1 day), then recovers within 5–10 trading days as the credibility filter down-weights unreliable sources and the TGN rewires its graph.

---

## Data Pipeline

### 1. Historical Price Data

```bash
# Downloads OHLCV for all tickers in CSV/Crypto.csv via yfinance
python "Data Extractions Scripts/historic_main.py"
```

Output: `{TICKER}/{TICKER}.csv` with columns `Date, Ticker, Open, High, Low, Close, Adj Close, Volume`

### 2. Reddit Sentiment

```bash
# Requires PRAW credentials (see script header)
python "Data Extractions Scripts/reddit_scrape.py"
```

Scrapes r/stocks, r/investing, r/wallstreetbets, r/crypto, r/cryptocurrency. Output: `{TICKER}/{TICKER}_reddit_comments.json`

### 3. News Data

```bash
# Requires NY Times API key
python "Data Extractions Scripts/news.py"
```

Output: `{TICKER}/{TICKER}_news_url.csv`

### 4. Feature Engineering

```bash
# FinBERT sentiment scoring on Reddit comments
python "Feature Engineering/finbert_1.py"

# FinBERT on news + NLP event detection (lexnlp / keyword fallback)
python "Feature Engineering/news_event_2.py"
```

Produces per-ticker master CSVs with columns:

| Column | Description |
|--------|-------------|
| `Sent_CumScore` | Cumulative FinBERT polarity (+1/−1) from social media |
| `Sent_NormScore` | `Sent_CumScore / Sent_TextCount` |
| `Sent_Confidence` | Mean model confidence |
| `News_Score` | Cumulative FinBERT polarity from news articles |
| `News_Norm` | `News_Score / News_Cnt` |
| `News_Conf` | Mean news confidence |
| `Event_Flag` | 1 if any article contains a finance-event keyword |

---

## Model Components

### Multimodal Input Fusion

Each asset c_i at time t is represented as:

```
X_{i,t} = [x_hist | x_sent | x_news | x_macro | x_whitepaper]
```

All modalities projected to d_model = 256 and fed through a 6-layer, 8-head transformer encoder with sinusoidal positional encoding and modality dropout (p = 0.3).

### Temporal Graph Network (TGN) Sidecar

- Rolling 7-day Pearson correlation between all asset pairs
- Edges pruned where |ρ| < 0.2 (τ = 0.2 optimal from ablation)
- 2-layer message passing, 128-d embeddings concatenated to transformer output

### RL Portfolio Optimizer

Portfolio allocation modeled as an MDP:

- **State:** transformer embeddings + TGN graph embeddings + previous weights + cost params
- **Action:** target weights w_t ∈ [−0.3, 0.3]^N with Σw = 1
- **Reward:** R_portfolio − λ · Var[R_portfolio]
- **Optimizers:** PPO and CVaR-PPO (clip 0.2, entropy 0.01, lr 3×10⁻⁴)

Transaction cost model distinguishes maker fees (2–5 bps), taker fees (5–10 bps), and asset-specific slippage (5–10 bps for BTC/ETH, up to 50 bps for illiquid altcoins).

### Dual-Layer Explainability

- **SHAP** feature attributions via LightGBM surrogate
- **GPT-generated ~30-word rationales** per prediction
- Human evaluation: κ = 0.78 (Fleiss') across 25 raters

---

## Key Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Transformer layers | 6 | — |
| Attention heads | 8 | — |
| d_model | 256 | — |
| Modality dropout | 0.3 | Ablated over {0.1, 0.2, 0.3, 0.5} |
| TGN correlation threshold τ | 0.2 | Ablated over {0.0, 0.1, 0.2, 0.3, 0.5} |
| Credibility threshold p_cred | 0.6 | Ablated over {0.4…0.8} |
| Lookback window k | 30 days | — |
| Portfolio size K | 10 | Sensitivity over {5, 10, 20} |
| Risk aversion λ | 0.1–1.0 | Sensitivity analysis reported |
| Batch size | 64 | — |
| Weight decay | 10⁻² | AdamW |
| Training | 10 epochs pretrain + 5 PPO fine-tune | Early stopping on validation Sharpe |
| Training compute | ~70 GPU-hours / 3-fold run | NVIDIA A100 80GB, PyTorch 2.2 |

LoRA adapters reduce training cost by 40% with < 3% Sharpe degradation.

---

## Backtesting Protocol

Rolling-window expanding backtest:
- **Train:** last 18 months
- **Test:** next 3 months
- **Folds:** 3 expanding windows
- Delisted assets held until delisting; newly listed assets in cold-start evaluation

---

## Installation

```bash
git clone https://github.com/abhishekjoshi007/CryptoFusion
cd CryptoFusion

pip install torch==2.2 transformers pandas numpy yfinance praw requests lexnlp shap lightgbm stable-baselines3
```

**API keys required:**
- Reddit: `CLIENT_ID`, `CLIENT_SECRET` in `Data Extractions Scripts/reddit_scrape.py`
- NY Times: `API_KEY` in `Data Extractions Scripts/news.py`
- GPT-4 (for LLM summarizer): set `OPENAI_API_KEY` in environment

---

## Citation

```bibtex
@INPROCEEDINGS{11402130,
  author={Joshi, Abhishek and Hadimlioglu, Alihan and Verma, Nikhilesh Krishnakum},
  booktitle={2025 IEEE International Conference on Big Data (BigData)}, 
  title={CryptoFusion: A Temporal Graph-Aware Transformer Framework for Robust Cryptocurrency Forecasting and Adaptive Portfolio Optimization}, 
  year={2025},
  volume={},
  number={},
  pages={2349-2358},
  keywords={Costs;Sensitivity analysis;Pipelines;Reinforcement learning;Transformers;Robustness;Cryptocurrency;Forecasting;Portfolios;Optimization;Cryptocurrency forecasting;multimodal transformers;temporal graph networks;explainable AI;portfolio optimization},
  doi={10.1109/BigData66926.2025.11402130}}
```

---

## License

This project is for academic research purposes. See the paper for full details on data sources and third-party API usage.
