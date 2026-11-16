# 01 — Riset (Shorts): "Your boss is hiding FREE money from you"

**Ringkasan untuk pemilik:** Semua angka di bawah dicek langsung dari sumber primer (Vanguard, Fidelity, IRS), diakses 2026-11-17. Bentuk match yang paling umum adalah 50% sampai 6% gaji. Sekitar **1 dari 5** peserta 401(k) tidak menyetor cukup untuk mendapat match penuh (Fidelity, Q2 2026). Kalau karyawan yang belum ikut plan juga dihitung, angkanya **sekitar 42%** (Vanguard, data 2023). Angka dolar terbaru per orang **tidak ada** dari sumber kuat. Angka "$1,336/tahun, $24 miliar" berasal dari studi Financial Engines **tahun 2015**, jadi sudah tua. Saran: di video pakai hitungan contoh kita sendiri ($1,200/tahun), jangan angka 2015. Catatan: "hiding" di hook itu hiperbola. Isi video sebaiknya bilang uangnya *tidak diambil*, bukan benar-benar disembunyikan bos.

---

## 1. What an employer match is + most common formulas
- A match = employer adds money to your 401(k) **only when you contribute**, up to a cap (e.g. "$0.50 per $1 on the first 6% of pay").
- **Most common formula (Vanguard 2025 data): 50% on the first 6% of pay**, used by 12% of plans with a match. Next: 100% on first 3% + 50% on next 2% (9%); 100% on first 6% (9%); 100% on first 5% (7%); **100% on first 4% (7%)**. Vanguard administers 100+ distinct formulas.
- Promised match value: **average 4.7% of pay, median 4.0%**. Employee deferral needed to get the full match: **average 6.4%, median 6.0%** of pay.
- 96% of Vanguard plans provide some employer contribution.
- Source: Vanguard, *How America Saves 2026* (released June 2026; 2025 data), Figures 4–10, pp. 21–24: https://workplace.vanguard.com/content/dam/inst/iig-transformation/insights/pdf/has/how-america-saves-2026.pdf
- Fidelity: most popular match on its platform = 100% on first 3% + 50% on next 2% (needs 5% from the employee). https://newsroom.fidelity.com/pressreleases/fidelity--q2-2026-retirement-analysis--record-savings-rates-help-drive-401-k---403-b--and-ira-balanc/s/bca5d71f-ebda-4289-bdd5-a90abde7feba

## 2. How many people miss the full match
| Figure | Publisher | Data period | Population |
|---|---|---|---|
| **81%** of 401(k) participants save enough for the full match, so **~19% (about 1 in 5) don't** | Fidelity Q2 2026 Retirement Analysis (released Sept 3, 2026) | June 30, 2026; 27,300 corporate plans, 25.8M participants | Participants only |
| "1 in 5 people contributing to a 401(k) aren't saving enough to get their full company match" | Fidelity infographic, citing *Building Financial Futures* Q1 2025 | Q1 2025 | Participants |
| **16% not contributing + 26% contributing below the match cap = ~42% of workers not getting the full match**; even at $150K+ income, ~20% don't max the match; only 22% of workers under $30K do | Vanguard Research, *Better match formulas for 401(k) plans* (July 2026) | Vanguard administrative data, 2023 | All eligible workers incl. non-participants |
| 25% miss the full match; typical shortfall **$1,336/yr**; **$24B/yr** total | Financial Engines, "Missing Out" (via SHRM, May 22, 2015) | ~2014–15; 4.4M participants, 553 companies | **OLD, avoid as headline** |

- Fidelity release: https://newsroom.fidelity.com/pressreleases/fidelity--q2-2026-retirement-analysis--record-savings-rates-help-drive-401-k---403-b--and-ira-balanc/s/bca5d71f-ebda-4289-bdd5-a90abde7feba
- Fidelity infographic: https://sponsor.fidelity.com/bin-public/06_PSW_Website/documents/Corporate_Meet_Your_Match_Q2_2025_Infographic.pdf
- Vanguard match paper (Figure 1, p. 3): https://corporate.vanguard.com/content/dam/corp/research/pdf/better_match_formulas_401k_plans.pdf
- SHRM on the 2015 study: https://www.shrm.org/ResourcesAndTools/hr-topics/benefits/Pages/missing-out-on--match.aspx
- **Honest note:** I found no recent (2024–2026) primary source with a dollar amount missed per person. Use the worked example in section 4 for dollars.

## 3. Auto-enrollment
- **61%** of Vanguard plans had automatic enrollment at year-end 2025 (79% of plans with 1,000+ participants). 71% of those plans also auto-increase the rate each year.
- Default rate: **3% is the single most common default (32% of auto-enroll plans)**. 62% default at 4% or higher, and 31% at 6% or more.
- Participation is 94% with auto-enrollment vs 64% with voluntary enrollment (participant-weighted).
- Hook-relevant point: if the default is 3% but the match needs 6%, an auto-enrolled worker who never changes the rate can still miss part of the match. (This is inferred from the two figures above, not a statistic Vanguard reports.)
- Source: Vanguard *How America Saves 2026*, pp. 6, 10, 29 (Figures 15–19), same link as section 1.

## 4. Worked example (Python)
Formulas:
- full match = salary × cap × match rate = 60,000 × 4% × 100% = **$2,400/yr**
- received at 2% = 60,000 × min(2%, 4%) × 100% = $1,200, so **missed = $1,200/yr**
- one year's miss grown 30 yrs at 7% real: 1,200 × 1.07^30 = **$9,135**
- missing it every year for 30 yrs (end-of-year deposits): 1,200 × ((1.07^30 − 1) / 0.07) = **$113,353** in today's dollars (vs $36,000 of raw contributions)
- for comparison, the full $2,400 every year for 30 yrs = $226,706

```python
salary, rate, cap, contrib, r, n = 60_000, 1.00, 0.04, 0.02, 0.07, 30
missed = salary*cap*rate - salary*min(contrib, cap)*rate      # 1,200
one_year = missed*(1+r)**n                                     # 9,135
every_year = missed*((1+r)**n - 1)/r                           # 113,353
```
7% real return is an **assumption** for illustration, not a guarantee. Say "could grow to roughly $113,000" and include the "not financial advice" disclaimer.

## 5. Vesting (match can be forfeited)
- Your own salary deferrals are **always 100% vested**. Employer match may follow a vesting schedule, and "amounts that are not vested may be forfeited" when you leave. IRS: https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-vesting
- Slowest schedules allowed for matching contributions: **3-year cliff** (0% until 3 years of service, then 100%) or **6-year graded** (20% after 2 yrs, 40% after 3, 60% after 4, 80% after 5, 100% after 6). Plans may be faster, including immediate vesting. IRS Issue Snapshot: https://www.irs.gov/retirement-plans/issue-snapshot-vesting-schedules-for-matching-contributions
- In practice (Vanguard 2025): **~49% of plans vest the match immediately**. 22% of plans with a match use a 5- or 6-year graded schedule, covering about 1 in 6 participants who get a match. *How America Saves 2026*, p. 20.

## 6. 401(k) contribution limits
- **2026: $24,500** employee deferral (up from $23,500). Catch-up 50+: $8,000. Ages 60–63: $11,250. IRS IR-2025-111, Nov. 13, 2025: https://www.irs.gov/node/152316
- **Heads-up: 2027 = $25,500** (catch-up 50+ $8,500; ages 60–63 $11,750). IRS IR-2026-136, Nov. 12, 2026: https://www.irs.gov/newsroom/401k-limit-increases-to-25500-for-2027-ira-limit-remains-7500. If the Short goes up near or after Jan 2027, consider using the 2027 figure or leaving the limit out (it isn't essential to the match story).
