# Task09: separate lambda=0 control on PC2 H100

This is a new from-zero detector-only execution, t=0 to 3.6, using the unchanged detector kernels from the pi/800 package. It does not modify existing runs. Follow **RUNBOOK.md** for the exact Mac upload, PC2 install/submit, monitoring and download commands.

At zero environmental rate the bath is identity. The globally pure, subnormalized no-click state remains rank one. The spinor absorbing roof remains active; this is **not** detector-free or unitary propagation. Reduced spin states can become mixed through coherent spin-motion entanglement even though the global no-click state remains pure.

## Key settings

| Setting | Value |
|---|---|
| Physical rate | lambda_up=0; all ambient channels inactive |
| Detector | Same spinor ABC, positive +K_N/(2h_z) roof term |
| Geometry | omega=100, N=12, Nz=1500, Lz=20 |
| Time | dt=0.0005, 7200 steps, T=3.6 |
| Launch | mode00, z0=10, sigma_z(amplitude)=0.5, k0=kappa=pi, theta=pi/6, phi=0 |
| Arithmetic | complex128 |
| GMRES | rtol=1e-10, restart=30, maxiter=1000; inherited true-residual gate=1e-8 |
| Propagation | One state column in the exact copied Batch-64 detector wrapper; independent-column check each step |
| Bath/compression | Identity bath skipped; compression disabled; no post-launch normalization |
| Checkpoints | Every 100 steps and at start, resume seams, terminal endpoint or clean stop |
| Resource request | One H100, 3 CPU cores, 16 GiB host RAM, maximum 24 h |
| Finalization reserve | 30 min; manual resume only |
| Output namespace | `Task09_Lambda0_Fresh_PC2_H100_2026-09-06_v1[ARCHIVE_PATH]` |

The internal zero references already present in the positive-rate runs remain the primary paired controls. This separate execution cross-checks their reproducibility; it is not an independent integrator, a reason to discard those runs, a susceptibility calculation, or an automatic finite-rate scientific acceptance.

Read `VALIDATION/RELEASE_QA.md` for executed tests, unexecuted H100 checks, and scope limits. `SOURCE_IDENTITY.json` pins unchanged source bytes. `CONFIG.json` pins the scientific and operational settings.
