# CryptoFusion: A Temporal Graph-AwareTransformer Framework for Robust Cryptocurrency Forecasting and Adaptive Portfolio Optimization

The cryptocurrency market is highly volatile, and
correlations between assets change rapidly based on sentiment
and event-driven news. In response, we propose a multimodal
framework, CryptoFusion based on transformers, for the fusion
and unification of structured and unstructured signals in a
coherent predictive execution pipeline. The framework comprises
(1) a dynamic graph neural network that models inter-asset
dependencies, (2) a credibility-aware LLM-driven news summa-
rization module focused on events that we benchmark against
aggressive but lighter sentiment heuristics, and (3) a cost-aware
adaptive reinforcement learning module that integrates realistic
market frictions in risk-sensitive portfolio optimization.
We test CryptoFusion on top-200 coins dataset from Jan
2017 - Jan 2025, encompassing the most important cryptocur-
rency market regimes. CryptoFusion achieves an 8.3% RMSE
reduction, 8.7 pp Directional Accuracy gain & 0.29 Sharpe
ratio improvement at 10 bps transaction costs against state-
of-the-art baselines models [1] [2] [3].Robust results in bullish,
bearish, and sideways markets; sensitivity analyses show robust-
ness to different risk-penalty parameters (λ) and transaction
cost tiers. Further ablative experiments show that removing the
graph module, LLM summarization, or RL allocator leads to
a significant decrease in predictive performance and portfolio
returns. For interpretability, CryptoFusion integrates SHAP
feature attributions with human iteratively evaluated short LLM-
generated rationales, with 25 raters achieving κ = 0.78 inter-
rater agreement. In summary, CryptoFusion advances the state-
of-the-art in multimodal financial AI by merging dynamic graphs,
credibility-filtered news, and risk-aware execution into an inte-
grated deployable system for crypto-portfolio management.
Index Terms—Cryptocurrency forecasting, multimodal trans-
formers, temporal graph networks, explainable AI, portfolio
optimization
