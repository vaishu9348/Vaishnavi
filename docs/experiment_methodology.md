# Experiment Methodology & Evaluation Protocol

This document outlines the scientific methodology, error quantification equations, and test protocol used to evaluate the privacy-preserving journey analytics system.

## 1. Research Question

> **"Which insurance claim workflow stage has the highest abandonment, and how accurately can this bottleneck be identified while operating under an $\epsilon \le 1.0$ differential privacy budget?"**

## 2. Experimental Hypotheses

1. **Bottleneck Identifiability Hypothesis**:
   Under Laplace differential privacy with $\epsilon = 1.0$, the platform correctly identifies `Document Upload` as the primary abandonment stage with $\ge 90\%$ statistical accuracy across randomized trials.

2. **Utility Error Hypothesis**:
   Mean Absolute Percentage Error (MAPE) between non-private ground truth abandonment rates and differentially private estimates will remain $\le 10\%$.

3. **Coexistence Resilience Hypothesis**:
   During active simulation of analytics service degradation, 100% of customer claims submitted through the legacy portal will succeed with zero exceptions.

---

## 3. Evaluation Metrics

### Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |\text{Actual}_i - \text{Predicted}_i|$$

### Mean Absolute Percentage Error (MAPE)
$$\text{MAPE} = \frac{1}{N} \sum_{i=1}^N \left|\frac{\text{Actual}_i - \text{Predicted}_i}{\max(\text{Actual}_i, 10^{-4})}\right| \times 100\%$$

### Top-Stage Identification Accuracy
$$\text{Acc}_{\text{top}} = \begin{cases} 1.0 & \text{if } \arg\max(\text{Rate}_{\text{actual}}) = \arg\max(\text{Rate}_{\text{private}}) \\ 0.0 & \text{otherwise} \end{cases}$$

### Ranking Agreement (Spearman Rank Correlation)
Spearman's $\rho$ measures the concordance of workflow stage abandonment rankings from least severe to most severe:
$$\rho = 1 - \frac{6 \sum d_i^2}{N(N^2 - 1)}$$

---

## 4. Benchmark Protocol

1. Generate 10,000 synthetic customer sessions (50,000+ events) with Document Upload modeled with 70% completion (30% drop-off).
2. Filter events with explicit `CONSENTED` status (~80%).
3. Calculate non-private ground truth rates per stage.
4. Execute 5 randomized trials across epsilon parameters $\epsilon \in \{0.1, 0.5, 1.0, 2.0\}$.
5. Measure MAE, MAPE, Top-Stage Accuracy, Ranking Agreement, Suppression Rate, and Runtime.
6. Export empirical benchmark matrix to `reports/experiment_results.csv`.
