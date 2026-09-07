# Privacy Model & Mathematical Framework

This document outlines the privacy-preserving mechanisms implemented in the Insurance Privacy Journey Analytics Platform.

## 1. Principles of Data Minimisation

Under GDPR Article 5(1)(c) and modern privacy frameworks, personal data collection must be limited to what is strictly necessary in relation to the purposes for which they are processed.

* **No Direct Identifiers**: Name, email address, physical address, national ID, and phone number are stripped at ingestion.
* **No Pseudonymous Tracking**: Persistent advertising identifiers or cookies across websites are prohibited.
* **Non-Reversible Session Tokens**: Sessions are assigned cryptographic salted tokens (`ANON-XXXX-XXXX`). No rainbow table or mapping database is maintained.
* **Temporal Coarsening**: Timestamps are bucketized to hourly intervals ($\Delta t = 1\text{ hour}$).

---

## 2. Consent-Aware Processing

Consent states represent an explicit prerequisite for telemetry processing:
$$\text{Consent Status} \in \{\text{CONSENTED}, \text{NOT\_CONSENTED}, \text{UNKNOWN}\}$$

* If $\text{status} = \text{CONSENTED} \implies \text{Included in aggregation}$
* If $\text{status} \in \{\text{NOT\_CONSENTED}, \text{UNKNOWN}, \text{None}\} \implies \text{Dropped immediately}$

---

## 3. Minimum Group-Size Suppression ($k$-Anonymity)

To protect individuals in sparse workflow branches from being singled out:
$$\text{Display}(C) = \begin{cases} C & \text{if } C \ge k \\ \text{"[SUPPRESSED < 10]"} & \text{if } C < k \end{cases}$$
Where $k = 10$ by default.

---

## 4. Differential Privacy Formulation

Differential privacy provides a rigorous mathematical guarantee that the presence or absence of any single customer's journey does not significantly alter the probability distribution of query outputs.

### Definition ($\epsilon$-Differential Privacy)
A randomized mechanism $\mathcal{M}$ satisfies $\epsilon$-differential privacy if for any two neighboring datasets $D, D'$ differing by at most one individual journey, and for any set of query outcomes $S \subseteq \text{Range}(\mathcal{M})$:
$$P[\mathcal{M}(D) \in S] \le e^\epsilon \cdot P[\mathcal{M}(D') \in S]$$

### Sensitivity ($\Delta f$)
For count queries where each individual can contribute at most one journey session:
$$\Delta f = \max \|f(D) - f(D')\|_1 = 1$$

### Laplace Mechanism
For each stage count query $f(D)$, noise is sampled from the Laplace distribution $\text{Lap}(b)$:
$$\mathcal{M}(D) = f(D) + \text{Lap}\left(\frac{\Delta f}{\epsilon}\right) = f(D) + \text{Lap}\left(\frac{1}{\epsilon}\right)$$

Where probability density function is:
$$p(x) = \frac{1}{2b} \exp\left(-\frac{|x|}{b}\right), \quad b = \frac{1}{\epsilon}$$

### Privacy Budget Accounting
The platform enforces a strict cumulative privacy budget cap $\epsilon_{\text{total}} = 1.0$.
$$\sum_{i=1}^m \epsilon_i \le \epsilon_{\text{total}}$$
When $\epsilon_{\text{consumed}} \ge \epsilon_{\text{total}}$, subsequent queries are refused, maintaining privacy guarantees across the operational lifecycle.
