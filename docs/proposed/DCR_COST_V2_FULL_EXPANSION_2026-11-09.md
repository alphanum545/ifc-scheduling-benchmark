# DCR-Cost v2 on the full expansion set (CI run, 9 November 2026)

Source: benchmark workflow run 42611201761 on `main` at d031e86 (results commit 69431cc), `set = expansion`
(1,890 instances), one process per machine (`workers = 1`), one repetition. All 26,460 runs
(14 algorithms × 1,890 instances) returned `status = ok` and `valid = True`.

**Reproducibility check.** On the 594 instances of the development sample (`DCR_COST_V2_2026-11-09.md`), the
CI cost and makespan equal the local runs exactly, for DCR-Cost v1 and v2, IC-PCP, CMaS and ProLiS seed 0
(0 differences of 594 each). This includes the numpy change (local 2.5.3, CI 2.2.6).

**Reading the table.**
- The paper 1 rows (HEFT … DCR-v4R) are budget-aware schedulers, run against each instance's budget, not
  cost minimizers. They are reference points, not paper 2 rivals.
- The paper 2 rivals are ProLiS, IC-PCP and CMaS (audits in `docs/paper_audits/`).
- Cost ratio = DCR-Cost v2 ÷ competitor, on instances where both meet D. Sign test: exact two-sided, on wins
  against losses.

Full expansion set: 1890 of 1890 instances with a valid DCR-Cost v2 run; v2 meets D on 1890.

### All
| vs | competitor meets D | both meet D | DCR-Cost v2 ÷ competitor, median (IQR) | mean ratio | v2 wins / ties / losses | sign p |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| ProLiS (seed 0) | 1809/1890 | 1809 | 0.984 (0.878–0.999) | 0.870 | 1714 / 65 / 30 | 0.0e+00 |
| ProLiS (mean of 10 seeds) | 1825/1890 | 1825 | 0.984 (0.877–0.998) | 0.870 | 1751 / 56 / 18 | 0.0e+00 |
| ProLiS (best of 10 seeds) | 1825/1890 | 1825 | 0.986 (0.886–0.999) | 0.872 | 1682 / 77 / 66 | 0.0e+00 |
| IC-PCP | 1717/1890 | 1717 | 0.467 (0.146–0.897) | 0.499 | 1693 / 0 / 24 | 0.0e+00 |
| CMaS | 278/1890 | 278 | 0.361 (0.294–0.636) | 0.552 | 253 / 1 / 24 | 2.2e-49 |
| DCR-Cost v1 | 1890/1890 | 1890 | 0.994 (0.908–1.000) | 0.900 | 1267 / 623 / 0 | 0.0e+00 |
| HEFT (budget-aware, paper 1) | 1890/1890 | 1890 | 0.146 (0.048–0.866) | 0.368 | 1890 / 0 / 0 | 0.0e+00 |
| PEFT (budget-aware, paper 1) | 1826/1890 | 1826 | 0.143 (0.047–0.829) | 0.344 | 1825 / 0 / 1 | 0.0e+00 |
| BDHEFT (budget-aware, paper 1) | 934/1890 | 934 | 0.055 (0.049–0.587) | 0.287 | 929 / 0 / 5 | 8.1e-269 |
| DBCS (budget-aware, paper 1) | 904/1890 | 904 | 0.052 (0.045–0.872) | 0.308 | 903 / 0 / 1 | 1.3e-269 |
| BDSD (budget-aware, paper 1) | 1109/1890 | 1109 | 0.208 (0.068–0.297) | 0.232 | 1106 / 0 / 3 | 0.0e+00 |
| BDDC (budget-aware, paper 1) | 1609/1890 | 1609 | 0.152 (0.057–0.287) | 0.287 | 1609 / 0 / 0 | 0.0e+00 |
| BDC (budget-aware, paper 1) | 1435/1890 | 1435 | 0.207 (0.061–0.281) | 0.287 | 1410 / 0 / 25 | 0.0e+00 |
| BDCWS (budget-aware, paper 1) | 1346/1890 | 1346 | 0.261 (0.107–0.413) | 0.332 | 1291 / 0 / 55 | 4.4e-307 |
| DCR-v4R (paper 1) (budget-aware, paper 1) | 1857/1890 | 1857 | 0.247 (0.070–0.910) | 0.422 | 1755 / 1 / 101 | 0.0e+00 |
| C_ref (dataset reference) | 1890/1890 | 1890 | 0.865 (0.705–0.945) | 0.839 | 1720 / 10 / 160 | 0.0e+00 |

### Tight
| vs | competitor meets D | both meet D | DCR-Cost v2 ÷ competitor, median (IQR) | mean ratio | v2 wins / ties / losses | sign p |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| ProLiS (seed 0) | 555/630 | 555 | 0.992 (0.959–1.000) | 0.976 | 508 / 32 / 15 | 2.8e-129 |
| ProLiS (mean of 10 seeds) | 566/630 | 566 | 0.991 (0.958–0.999) | 0.975 | 526 / 29 / 11 | 1.1e-139 |
| ProLiS (best of 10 seeds) | 566/630 | 566 | 0.993 (0.959–1.000) | 0.976 | 503 / 35 / 28 | 9.6e-114 |
| IC-PCP | 459/630 | 459 | 0.930 (0.891–0.962) | 0.923 | 436 / 0 / 23 | 5.2e-100 |
| CMaS | 0/630 | 0 | nan (nan–nan) | nan | 0 / 0 / 0 | nan |
| DCR-Cost v1 | 630/630 | 630 | 1.000 (0.955–1.000) | 0.973 | 292 / 338 / 0 | 2.5e-88 |
| HEFT (budget-aware, paper 1) | 630/630 | 630 | 0.897 (0.866–0.942) | 0.895 | 630 / 0 / 0 | 4.5e-190 |
| PEFT (budget-aware, paper 1) | 566/630 | 566 | 0.886 (0.850–0.923) | 0.880 | 565 / 0 / 1 | 4.7e-168 |
| BDHEFT (budget-aware, paper 1) | 233/630 | 233 | 0.912 (0.884–0.961) | 0.916 | 228 / 0 / 5 | 8.1e-61 |
| DBCS (budget-aware, paper 1) | 267/630 | 267 | 0.908 (0.885–0.956) | 0.914 | 266 / 0 / 1 | 2.3e-78 |
| BDSD (budget-aware, paper 1) | 10/630 | 10 | 0.957 (0.945–0.998) | 0.997 | 7 / 0 / 3 | 3.4e-01 |
| BDDC (budget-aware, paper 1) | 349/630 | 349 | 0.877 (0.830–0.902) | 0.865 | 349 / 0 / 0 | 1.7e-105 |
| BDC (budget-aware, paper 1) | 248/630 | 248 | 0.920 (0.896–0.964) | 0.922 | 223 / 0 / 25 | 6.7e-41 |
| BDCWS (budget-aware, paper 1) | 115/630 | 115 | 0.999 (0.972–1.020) | 0.997 | 62 / 0 / 53 | 4.6e-01 |
| DCR-v4R (paper 1) (budget-aware, paper 1) | 597/630 | 597 | 0.949 (0.911–0.989) | 0.946 | 495 / 1 / 101 | 2.5e-63 |
| C_ref (dataset reference) | 630/630 | 630 | 0.937 (0.895–0.981) | 0.935 | 571 / 6 / 53 | 1.1e-110 |

### Moderate
| vs | competitor meets D | both meet D | DCR-Cost v2 ÷ competitor, median (IQR) | mean ratio | v2 wins / ties / losses | sign p |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| ProLiS (seed 0) | 624/630 | 624 | 0.988 (0.846–0.999) | 0.851 | 598 / 18 / 8 | 3.3e-165 |
| ProLiS (mean of 10 seeds) | 629/630 | 629 | 0.986 (0.843–0.998) | 0.850 | 608 / 15 / 6 | 2.2e-171 |
| ProLiS (best of 10 seeds) | 629/630 | 629 | 0.990 (0.855–0.999) | 0.855 | 579 / 26 / 24 | 3.4e-139 |
| IC-PCP | 628/630 | 628 | 0.288 (0.168–0.712) | 0.428 | 627 / 0 / 1 | 1.1e-186 |
| CMaS | 0/630 | 0 | nan (nan–nan) | nan | 0 / 0 / 0 | nan |
| DCR-Cost v1 | 630/630 | 630 | 0.987 (0.831–1.000) | 0.870 | 477 / 153 / 0 | 5.1e-144 |
| HEFT (budget-aware, paper 1) | 630/630 | 630 | 0.146 (0.130–0.168) | 0.162 | 630 / 0 / 0 | 4.5e-190 |
| PEFT (budget-aware, paper 1) | 630/630 | 630 | 0.145 (0.127–0.167) | 0.160 | 630 / 0 / 0 | 4.5e-190 |
| BDHEFT (budget-aware, paper 1) | 71/630 | 71 | 0.247 (0.220–0.278) | 0.282 | 71 / 0 / 0 | 8.5e-22 |
| DBCS (budget-aware, paper 1) | 7/630 | 7 | 0.212 (0.189–0.222) | 0.215 | 7 / 0 / 0 | 1.6e-02 |
| BDSD (budget-aware, paper 1) | 477/630 | 477 | 0.302 (0.260–0.488) | 0.373 | 477 / 0 / 0 | 5.1e-144 |
| BDDC (budget-aware, paper 1) | 630/630 | 630 | 0.166 (0.147–0.194) | 0.189 | 630 / 0 / 0 | 4.5e-190 |
| BDC (budget-aware, paper 1) | 557/630 | 557 | 0.243 (0.223–0.274) | 0.252 | 557 / 0 / 0 | 4.2e-168 |
| BDCWS (budget-aware, paper 1) | 601/630 | 601 | 0.323 (0.276–0.453) | 0.392 | 599 / 0 / 2 | 4.4e-176 |
| DCR-v4R (paper 1) (budget-aware, paper 1) | 630/630 | 630 | 0.250 (0.227–0.287) | 0.278 | 630 / 0 / 0 | 4.5e-190 |
| C_ref (dataset reference) | 630/630 | 630 | 0.719 (0.593–0.851) | 0.741 | 570 / 4 / 56 | 3.6e-108 |

### Relaxed
| vs | competitor meets D | both meet D | DCR-Cost v2 ÷ competitor, median (IQR) | mean ratio | v2 wins / ties / losses | sign p |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| ProLiS (seed 0) | 630/630 | 630 | 0.970 (0.641–0.992) | 0.795 | 608 / 15 / 7 | 9.5e-170 |
| ProLiS (mean of 10 seeds) | 630/630 | 630 | 0.969 (0.641–0.992) | 0.794 | 617 / 12 / 1 | 1.1e-183 |
| ProLiS (best of 10 seeds) | 630/630 | 630 | 0.971 (0.641–0.992) | 0.796 | 600 / 16 / 14 | 3.2e-157 |
| IC-PCP | 630/630 | 630 | 0.094 (0.049–0.406) | 0.261 | 630 / 0 / 0 | 4.5e-190 |
| CMaS | 278/630 | 278 | 0.361 (0.294–0.636) | 0.552 | 253 / 1 / 24 | 2.2e-49 |
| DCR-Cost v1 | 630/630 | 630 | 0.978 (0.804–1.000) | 0.857 | 498 / 132 / 0 | 2.4e-150 |
| HEFT (budget-aware, paper 1) | 630/630 | 630 | 0.045 (0.038–0.048) | 0.047 | 630 / 0 / 0 | 4.5e-190 |
| PEFT (budget-aware, paper 1) | 630/630 | 630 | 0.044 (0.038–0.047) | 0.046 | 630 / 0 / 0 | 4.5e-190 |
| BDHEFT (budget-aware, paper 1) | 630/630 | 630 | 0.052 (0.045–0.055) | 0.054 | 630 / 0 / 0 | 4.5e-190 |
| DBCS (budget-aware, paper 1) | 630/630 | 630 | 0.050 (0.042–0.053) | 0.052 | 630 / 0 / 0 | 4.5e-190 |
| BDSD (budget-aware, paper 1) | 622/630 | 622 | 0.070 (0.058–0.148) | 0.112 | 622 / 0 / 0 | 1.1e-187 |
| BDDC (budget-aware, paper 1) | 630/630 | 630 | 0.052 (0.046–0.066) | 0.064 | 630 / 0 / 0 | 4.5e-190 |
| BDC (budget-aware, paper 1) | 630/630 | 630 | 0.059 (0.053–0.069) | 0.067 | 630 / 0 / 0 | 4.5e-190 |
| BDCWS (budget-aware, paper 1) | 630/630 | 630 | 0.101 (0.079–0.176) | 0.153 | 630 / 0 / 0 | 4.5e-190 |
| DCR-v4R (paper 1) (budget-aware, paper 1) | 630/630 | 630 | 0.058 (0.052–0.071) | 0.068 | 630 / 0 / 0 | 4.5e-190 |
| C_ref (dataset reference) | 630/630 | 630 | 0.819 (0.678–0.912) | 0.841 | 579 / 0 / 51 | 2.3e-114 |

### Against CP-SAT (60-task; best found in 5 min; proven-optimal subset)
| method | n | ÷ C* median | p90 | proven-optimal n | ÷ C* median there |
| --- | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v2 | 270 | 1.027 | 1.299 | 67 | 1.013 |
| DCR-Cost v1 | 270 | 1.079 | 1.744 | 67 | 1.013 |
| ProLiS (mean of 10 seeds) | 266 | 1.123 | 1.794 | 66 | 1.091 |
| ProLiS (best of 10 seeds) | 266 | 1.113 | 1.788 | 66 | 1.091 |
| IC-PCP | 242 | 1.693 | 6.932 | 56 | 1.165 |
| CMaS | 58 | 2.440 | 5.024 | 0 | nan |

### Policy runtime (s), one process per machine
| method | tasks | median | p90 | max |
| --- | ---: | ---: | ---: | ---: |
| dcr-cost-v2 | 60 | 0.67 | 2.04 | 2.73 |
| dcr-cost-v2 | 100 | 1.07 | 2.90 | 4.70 |
| dcr-cost-v2 | 200 | 2.41 | 6.20 | 10.52 |
| dcr-cost-v2 | 400 | 8.47 | 14.85 | 26.28 |
| dcr-cost-v2 | 600 | 17.05 | 31.53 | 50.12 |
| dcr-cost-v2 | 800 | 33.23 | 60.63 | 94.72 |
| dcr-cost-v2 | 1000 | 59.32 | 101.12 | 174.90 |
| dcr-cost-v1 | 60 | 0.28 | 0.61 | 0.70 |
| dcr-cost-v1 | 100 | 0.46 | 0.93 | 1.13 |
| dcr-cost-v1 | 200 | 1.05 | 2.04 | 2.58 |
| dcr-cost-v1 | 400 | 2.79 | 5.16 | 6.64 |
| dcr-cost-v1 | 600 | 5.30 | 9.73 | 12.57 |
| dcr-cost-v1 | 800 | 9.96 | 15.94 | 20.44 |
| dcr-cost-v1 | 1000 | 16.14 | 25.61 | 36.89 |
| prolis-s0 | 60 | 0.09 | 0.49 | 0.66 |
| prolis-s0 | 100 | 0.14 | 0.60 | 1.12 |
| prolis-s0 | 200 | 0.29 | 1.18 | 2.34 |
| prolis-s0 | 400 | 0.60 | 2.50 | 4.70 |
| prolis-s0 | 600 | 0.92 | 3.63 | 7.17 |
| prolis-s0 | 800 | 1.18 | 5.40 | 9.54 |
| prolis-s0 | 1000 | 1.62 | 6.75 | 11.99 |
| icpcp | 60 | 0.10 | 0.51 | 0.70 |
| icpcp | 100 | 0.18 | 0.64 | 1.21 |
| icpcp | 200 | 0.40 | 1.31 | 2.65 |
| icpcp | 400 | 1.11 | 2.99 | 5.70 |
| icpcp | 600 | 2.31 | 4.90 | 9.26 |
| icpcp | 800 | 3.30 | 7.43 | 13.10 |
| icpcp | 1000 | 5.39 | 9.95 | 17.23 |
| cmas | 60 | 0.20 | 0.58 | 0.99 |
| cmas | 100 | 0.42 | 1.00 | 1.60 |
| cmas | 200 | 1.19 | 2.39 | 4.60 |
| cmas | 400 | 3.35 | 6.18 | 11.62 |
| cmas | 600 | 6.56 | 12.06 | 21.79 |
| cmas | 800 | 9.59 | 17.96 | 25.13 |
| cmas | 1000 | 14.20 | 24.71 | 41.11 |

CPU models (DCR-Cost v2 rows): AMD EPYC 9V74 80-Core Processor: 439; Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz: 31; AMD EPYC 7763 64-Core Processor: 758; INTEL(R) XEON(R) PLATINUM 8573C: 220; AMD EPYC 9V45 96-Core Processor: 442

**Runtime caveat.** The runners had five different CPU models (counts above), so runtimes are indicative
only. DCR-Cost v2 is the slowest method: 59 s median at 1,000 tasks, against 16 s for v1 and 1.6 s per ProLiS
run (16 s for the 10-seed protocol). Every candidate gets the improvement pass, and that pass dominates the
cost.

## Summary

- DCR-Cost v2 meets D on 1,890/1,890. ProLiS: 1,809 (seed 0) and 1,825 (any of 10 seeds). IC-PCP: 1,717.
  CMaS: 278.
- Against ProLiS, v2 wins 1,751, ties 56 and loses 18 (mean of 10 seeds). Against the best of 10 seeds:
  1,682 / 77 / 66. Median saving 1.4–1.6%, mean saving about 13%. The gaps are largest on relaxed deadlines
  (mean ratio 0.79).
- Against IC-PCP: 0.467 median ratio, 1,693 wins and 24 losses. Against C_ref: 0.865 median, 1,720 / 10 / 160.
- Against CP-SAT (60-task, unchanged from the sample): 2.7% median above the best known cost; 1.3% where
  optimality is proven.
