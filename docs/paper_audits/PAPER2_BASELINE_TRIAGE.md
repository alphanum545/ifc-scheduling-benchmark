# Paper 2 baseline triage (deadline-constrained cost minimization)

Papers received on 9 November 2026. Each was read in full before classification.

| Paper | Problem | Resource model | Verdict |
| --- | --- | --- | --- |
| ProLiS / L-ACO, Wu et al., IEEE TPDS 28(12), 2017 | Min cost s.t. deadline | Elastic IaaS, interval billing | **Implement ProLiS** (MAJOR adaptation, see `PROLIS_2017.md`); L-ACO optional |
| CMaS, Pham et al., IJDSN 13(11), 2017 | Cost–makespan trade-off + deadline reassignment | Fixed fog + cloud nodes | **Implement** (MINOR adaptation, see `CMAS_2017.md`) |
| IC-PCP, Abrishami et al., FGCS 29(1), 2013 | Min cost s.t. deadline via partial critical paths | Elastic IaaS: any number of instances, interval billing; tasks first use the remaining time of existing instances | **Implement as MAJOR adaptation** only after ProLiS/CMaS; the path-to-one-resource rule survives on a fixed pool, launching instances does not. Full audit pending |
| ET2FA, Sun et al., IEEE TSC 16(3), 2023 | Min cost + idle rate s.t. deadline | Unlimited elastic instances, per-second billing, instance hibernation | **Exclude**: hibernation and instance creation are defining and not representable (same reasoning as the companion DB-ACO audit) |
| Li Chunlin et al., J. Grid Computing 2019, "Hybrid Cloud Adaptive Scheduling Strategy for Heterogeneous Workloads" | Job scheduling of heterogeneous big-data workloads; BP-neural-network task placement for deadlines and public-cloud cost | Private cluster + public cloud bursting | **Exclude**: not DAG workflow scheduling; a learned model with no reproducible training setup |
| DB-ACO, Tao et al., IEEE TASE 2024 | Min cost s.t. deadline and budget | Elastic IaaS | **Excluded** by the companion audit (`DB_ACO_2024.md`); same standard applied here |
| PSO-SA, Khaledian et al., Computing 2024 | Energy + deadline | Fog/cloud | **Exclude**: no cost objective (`PSO_SA_2024.md`) |

Still wanted: the full papers of DCWS (Hussain et al., SIMPAT 2023, hybrid cloud with free private resources)
and the edge–cloud cost-minimization GA (Abdi et al., J. Supercomputing 2024).
