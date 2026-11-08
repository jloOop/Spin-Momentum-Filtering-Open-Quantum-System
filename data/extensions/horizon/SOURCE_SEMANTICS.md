# Executed writer and numerical conventions

Source: `work/responses/4775.Environmental_response_144_00_spinor_upward/spinor_upward_omega144_mode00_N12_dt2p5e-4_T20_ins5e-2_07_environmental_response_solver.py`
SHA256: `bfe35ce4b61b860c70dfb149248fc75be9e41238380d144ea59c4080f505df41`

```python
827: def norm2_cpu(vector: np.ndarray, h_z: float) -> float:
828:     return float(h_z * np.sum(np.abs(vector) ** 2, dtype=np.float64))
829: 
830: 
831: def inner_cpu(left: np.ndarray, right: np.ndarray, h_z: float) -> complex:
832:     return complex(h_z * np.vdot(left, right))
```

```python
1412: def complete_shell_labels_descending(n_shell: int) -> Tuple[Tuple[int, int], ...]:
1413:     labels: List[Tuple[int, int]] = []
1414:     for total in range(n_shell + 1):
1415:         for nx in range(total, -1, -1):
1416:             labels.append((nx, total - nx))
1417:     return tuple(labels)
1418: 
1419: def complete_shell_labels_audit02_native(n_shell: int) -> Tuple[Tuple[int, int], ...]:
1420:     """Literal ordering in the attached final Audit-02 source."""
1421:     labels: List[Tuple[int, int]] = []
1422:     for total in range(n_shell + 1):
1423:         for nx in range(total + 1):
1424:             labels.append((nx, total - nx))
1425:     return tuple(labels)
1426: 
1427: def build_projected_ladders(
1428:     labels: Tuple[Tuple[int, int], ...]
1429: ) -> Tuple[sp.csr_matrix, sp.csr_matrix, Dict[Tuple[int, int], int]]:
1430:     index = {label: position for position, label in enumerate(labels)}
1431:     rows_x: List[int] = []
1432:     cols_x: List[int] = []
1433:     data_x: List[complex] = []
1434:     rows_y: List[int] = []
1435:     cols_y: List[int] = []
1436:     data_y: List[complex] = []
1437: 
1438:     for column, (nx, ny) in enumerate(labels):
1439:         if nx > 0:
1440:             rows_x.append(index[(nx - 1, ny)])
1441:             cols_x.append(column)
1442:             data_x.append(math.sqrt(nx))
1443:         if ny > 0:
1444:             rows_y.append(index[(nx, ny - 1)])
1445:             cols_y.append(column)
1446:             data_y.append(math.sqrt(ny))
1447: 
1448:     dimension = len(labels)
1449:     a_x = sp.csr_matrix(
1450:         (np.asarray(data_x, dtype=np.complex128), (rows_x, cols_x)),
1451:         shape=(dimension, dimension),
1452:         dtype=np.complex128,
1453:     )
1454:     a_y = sp.csr_matrix(
1455:         (np.asarray(data_y, dtype=np.complex128), (rows_y, cols_y)),
1456:         shape=(dimension, dimension),
1457:         dtype=np.complex128,
1458:     )
1459:     return a_x, a_y, index
1460: 
1461: def basis_vector(dimension: int, index: int) -> np.ndarray:
1462:     vector = np.zeros(dimension, dtype=np.complex128)
1463:     vector[index] = 1.0
1464:     return vector
1465: 
1466: def orbital_permutation(
1467:     source_labels: Sequence[Tuple[int, int]],
1468:     target_labels: Sequence[Tuple[int, int]],
1469: ) -> sp.csr_matrix:
1470:     """Return P such that v_target = P v_source."""
1471:     source_index = {label: idx for idx, label in enumerate(source_labels)}
1472:     rows = np.arange(len(target_labels), dtype=np.int32)
1473:     cols = np.asarray([source_index[label] for label in target_labels], dtype=np.int32)
1474:     data = np.ones(len(target_labels), dtype=np.complex128)
1475:     return sp.csr_matrix((data, (rows, cols)), shape=(len(target_labels), len(source_labels)))
1476: 
1477: def audit02_to_task05_tensor_permutation(
1478:     native_labels: Sequence[Tuple[int, int]],
1479:     task05_labels: Sequence[Tuple[int, int]],
1480: ) -> sp.csr_matrix:
1481:     """Map Audit-02 (orbital, spin-fast) to Task-05 (spin, orbital)."""
1482:     native_index = {label: idx for idx, label in enumerate(native_labels)}
1483:     task_index = {label: idx for idx, label in enumerate(task05_labels)}
1484:     m_modes = len(task05_labels)
1485:     rows: List[int] = []
1486:     cols: List[int] = []
1487:     data: List[complex] = []
1488:     for label in task05_labels:
1489:         mu_task = task_index[label]
1490:         mu_native = native_index[label]
1491:         for spin in range(2):
1492:             rows.append(spin * m_modes + mu_task)
1493:             cols.append(mu_native * 2 + spin)
1494:             data.append(1.0)
1495:     return sp.csr_matrix(
1496:         (np.asarray(data, dtype=np.complex128), (rows, cols)),
1497:         shape=(2 * m_modes, 2 * m_modes),
1498:     )
```

```python
2446: def channel_environment_operators(
2447:     operators: OscillatorOperators,
2448:     direction: str,
2449: ) -> Tuple[Tuple[str, sp.csr_matrix, sp.csr_matrix], ...]:
2450:     identity_spin = sp.eye(2, dtype=np.complex128, format="csr")
2451:     if direction == "downward":
2452:         orbital = (("x", operators.a_x), ("y", operators.a_y))
2453:     elif direction == "upward":
2454:         orbital = (("x", operators.a_x_dagger), ("y", operators.a_y_dagger))
2455:     elif direction == "dephasing":
2456:         orbital = (("x", operators.n_x), ("y", operators.n_y))
2457:     else:
2458:         raise ValueError(f"Unsupported environmental direction {direction!r}")
2459:     result: List[Tuple[str, sp.csr_matrix, sp.csr_matrix]] = []
2460:     for label, operator in orbital:
2461:         channel = sp.kron(identity_spin, operator, format="csr")
2462:         anti = (channel.getH() @ channel).tocsr()
2463:         result.append((label, channel, anti))
2464:     return tuple(result)
2465: 
2466: 
2467: def apply_channel_operator(operator: sp.csr_matrix, state: np.ndarray, n_z: int) -> np.ndarray:
2468:     matrix = np.asarray(state, dtype=np.complex128).reshape(operator.shape[1], n_z)
2469:     return np.asarray(operator @ matrix, dtype=np.complex128).reshape(-1)
2470: 
2471: 
2472: def source_vectors_at_state(
2473:     state: np.ndarray,
2474:     *,
2475:     operators: OscillatorOperators,
2476:     direction: str,
2477:     h_z: float,
2478:     n_z: int,
2479: ) -> Dict[str, Any]:
2480:     state = np.asarray(state, dtype=np.complex128).reshape(-1)
2481:     branches: List[np.ndarray] = []
2482:     labels: List[str] = []
2483:     jump_norms: List[float] = []
2484:     anti_expectations: List[float] = []
2485:     trace_terms: List[float] = []
2486:     for axis, jump_operator, anti_operator in channel_environment_operators(operators, direction):
2487:         jump = apply_channel_operator(jump_operator, state, n_z)
2488:         anti = apply_channel_operator(anti_operator, state, n_z)
2489:         jump_norm = norm2_cpu(jump, h_z)
2490:         anti_expectation = float(inner_cpu(state, anti, h_z).real)
2491:         branches.extend((jump, anti))
2492:         labels.extend((f"jump_{axis}", f"anti_{axis}"))
2493:         jump_norms.append(jump_norm)
2494:         anti_expectations.append(anti_expectation)
2495:         trace_terms.append(jump_norm - anti_expectation)
2496:     return {
2497:         "branch_vectors": np.stack(branches, axis=1).astype(np.complex128, copy=False),
2498:         "branch_labels": np.asarray(labels, dtype="U16"),
2499:         "jump_norm2": np.asarray(jump_norms, dtype=np.float64),
2500:         "anti_expectation": np.asarray(anti_expectations, dtype=np.float64),
2501:         "trace_terms": np.asarray(trace_terms, dtype=np.float64),
2502:         "trace_total": float(np.sum(trace_terms, dtype=np.float64)),
2503:         "activity_total": float(np.sum(jump_norms, dtype=np.float64)),
2504:     }
2505: 
2506: 
2507: def projected_upward_identity_audit(operators: OscillatorOperators) -> Dict[str, Any]:
2508:     identity = sp.eye(operators.m_modes, dtype=np.complex128, format="csr")
2509:     top = sp.diags(
2510:         (operators.shell_of_mode == int(np.max(operators.shell_of_mode))).astype(np.float64),
2511:         0,
2512:         format="csr",
2513:         dtype=np.complex128,
2514:     )
2515:     expected = (
2516:         operators.n_perp
2517:         + 2.0 * identity
2518:         - (int(np.max(operators.shell_of_mode)) + 2.0) * top
2519:     ).tocsr()
2520:     actual = (
2521:         operators.a_x @ operators.a_x_dagger
2522:         + operators.a_y @ operators.a_y_dagger
2523:     ).tocsr()
2524:     residual = sparse_max_abs(actual - expected)
2525:     return {
2526:         "identity": "sum_j a_j a_j^dagger = N_perp + 2 I - (N_shell+2) Pi_top",
2527:         "maximum_abs_residual": residual,
2528:         "passed": residual <= OPERATOR_TOL,
```

```python
2551: def lightweight_source_diagnostics(
2552:     state: Any,
2553:     *,
2554:     backend: NumericalBackend,
2555:     operators: OscillatorOperators,
2556:     h_z: float,
2557:     n_z: int,
2558: ) -> Tuple[float, float, float, float]:
2559:     shaped = state.reshape(2, operators.m_modes, n_z)
2560:     density = shaped.real * shaped.real + shaped.imag * shaped.imag
2561:     mode_population = h_z * backend.xp.sum(density, axis=(0, 2), dtype=backend.float64)
2562:     mode_population_cpu = np.asarray(backend.to_cpu(mode_population), dtype=np.float64)
2563:     survival = float(np.sum(mode_population_cpu, dtype=np.float64))
2564:     nx = float(np.dot(mode_population_cpu, operators.nx_diag))
2565:     ny = float(np.dot(mode_population_cpu, operators.ny_diag))
2566:     nx2 = float(np.dot(mode_population_cpu, operators.nx_diag ** 2))
2567:     ny2 = float(np.dot(mode_population_cpu, operators.ny_diag ** 2))
2568:     top = float(np.sum(mode_population_cpu[operators.shell_of_mode == int(np.max(operators.shell_of_mode))]))
2569:     if survival <= 0.0:
2570:         raise FloatingPointError("Reference survival became nonpositive")
2571:     down = (nx + ny) / survival
2572:     up = (
2573:         float(np.dot(mode_population_cpu, operators.nx_diag + operators.ny_diag + 2.0))
2574:         - (int(np.max(operators.shell_of_mode)) + 2.0) * top
2575:     ) / survival
2576:     phi = (nx2 / survival - (nx / survival) ** 2) + (ny2 / survival - (ny / survival) ** 2)
2577:     return down, up, phi, top / survival
```

```python
3960: # =============================================================================
3961: def panel_index_for_step(insertion_steps: np.ndarray, fine_step: int) -> int:
3962:     return int(np.searchsorted(insertion_steps[1:], fine_step, side="right"))
3963: 
3964: 
3965: def prefix_trapezoid_weights(times: np.ndarray, endpoint_index: int) -> np.ndarray:
3966:     if endpoint_index == 0:
3967:         return np.zeros(1, dtype=np.float64)
3968:     selected = np.asarray(times[: endpoint_index + 1], dtype=np.float64)
3969:     weights = np.zeros(selected.size, dtype=np.float64)
3970:     weights[0] = 0.5 * (selected[1] - selected[0])
3971:     weights[-1] = 0.5 * (selected[-1] - selected[-2])
3972:     if selected.size > 2:
3973:         weights[1:-1] = 0.5 * (selected[2:] - selected[:-2])
3974:     return weights
3975: 
3976: 
3977: def kernel_survival_from_panel_probability(kernel_probability: np.ndarray) -> np.ndarray:
3978:     panels, insertions = kernel_probability.shape
3979:     result = np.zeros((panels + 1, insertions), dtype=np.float64)
3980:     for insertion in range(insertions):
3981:         if insertion >= panels:
3982:             continue
3983:         result[insertion + 1 :, insertion] = -np.cumsum(
3984:             kernel_probability[insertion:, insertion], dtype=np.float64
3985:         )
3986:     return result
3987: 
3988: 
3989: def reconstruct_response_from_kernel(
3990:     insertion_times: np.ndarray,
3991:     kernel_probability: np.ndarray,
3992:     kernel_survival: Optional[np.ndarray] = None,
3993: ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
3994:     """Apply the declared insertion-time trapezoidal quadrature.
3995: 
3996:     ``kernel_probability[p,q]`` is the first-order roof probability in output
3997:     panel ``p`` generated by an *unweighted* environmental insertion at state
3998:     node ``q``.  ``kernel_survival[i,q]`` is the independently evaluated trace
3999:     of that propagated insertion at state node ``i``.  Supplying the latter is
4000:     mandatory for production and benchmark response calculations: deriving it
4001:     from the click kernel would make the probability-closure audit tautological.
4002:     """
4003:     panels, insertions = kernel_probability.shape
4004:     if insertions != panels + 1:
4005:         raise ValueError("Kernel must have one more insertion node than output panels")
4006:     if kernel_survival is None:
4007:         kernel_survival = kernel_survival_from_panel_probability(kernel_probability)
4008:     kernel_survival = np.asarray(kernel_survival, dtype=np.float64)
4009:     if kernel_survival.shape != (insertions, insertions):
4010:         raise ValueError(
4011:             "Survival kernel must have shape (number_insertion_nodes, number_insertion_nodes)"
4012:         )
4013:     chi_survival = np.zeros(insertions, dtype=np.float64)
4014:     chi_panel_probability = np.zeros(panels, dtype=np.float64)
4015:     for state_index in range(insertions):
4016:         weights = prefix_trapezoid_weights(insertion_times, state_index)
4017:         chi_survival[state_index] = float(
4018:             np.dot(weights, kernel_survival[state_index, : state_index + 1])
4019:         )
4020:     for panel in range(panels):
4021:         # Prefix weights through the *end* of this panel.  The new endpoint
4022:         # source has zero influence on the preceding panel and is omitted.
4023:         weights = prefix_trapezoid_weights(insertion_times, panel + 1)
4024:         chi_panel_probability[panel] = float(
4025:             np.dot(weights[: panel + 1], kernel_probability[panel, : panel + 1])
4026:         )
4027:     durations = np.diff(insertion_times)
4028:     chi_density = chi_panel_probability / durations
4029:     return chi_survival, chi_panel_probability, chi_density
```

```python
4435: 
4436:             # Recover each node's four columns from the active compact matrix.
4437:             active_lookup = {int(global_col): local for local, global_col in enumerate(active_columns_cpu)}
4438:             for node in batch_nodes:
4439:                 if int(insertion_steps[node]) > fine_step:
4440:                     continue
4441:                 base = node_base[node]
4442:                 jump_loss = 0.0
4443:                 anti_loss = 0.0
4444:                 for axis_offset in (0, 2):
4445:                     jump_global = base + axis_offset
4446:                     anti_global = base + axis_offset + 1
4447:                     # One oscillator direction can vanish exactly (for example
4448:                     # a_y on |1,0>).  The nonzero direction must still be kept.
4449:                     if jump_global not in active_lookup and anti_global not in active_lookup:
4450:                         continue
4451:                     if jump_global not in active_lookup or anti_global not in active_lookup:
4452:                         raise RuntimeError(
4453:                             "Jump/anticommutator branch activity mismatch for one dissipator"
4454:                         )
4455:                     q_jump = q_branch[:, active_lookup[jump_global]]
4456:                     q_anti = q_branch[:, active_lookup[anti_global]]
4457:                     jump_loss += config.dt * config.kappa * backend.abs2_sum(q_jump)
4458:                     anti_inner = backend.xp.sum(backend.xp.conj(q_ref) * q_anti)
4459:                     anti_loss += config.dt * config.kappa * backend.scalar_float(anti_inner.real)
4460:                 kernel_jump_probability[panel, node] += jump_loss
4461:                 kernel_anticommutator_probability[panel, node] += -anti_loss
4462: 
4463:             # At declared state nodes, independently evaluate Tr of every
4464:             # propagated insertion.  This supplies chi_S without using the
4465:             # detector-probability closure identity.
4466:             output_step = fine_step + 1
4467:             if output_step in output_node_for_step:
4468:                 output_node = output_node_for_step[output_step]
4469:                 reference_output = backend.to_backend_array(
4470:                     np.asarray(selected_states[output_node])
4471:                 )
4472:                 for node in batch_nodes:
4473:                     if int(insertion_steps[node]) > output_step:
4474:                         continue
4475:                     base = node_base[node]
4476:                     trace_value = 0.0
4477:                     for axis_offset in (0, 2):
4478:                         jump_global = base + axis_offset
4479:                         anti_global = base + axis_offset + 1
4480:                         if not active[jump_global] and not active[anti_global]:
4481:                             continue
4482:                         if not active[jump_global] or not active[anti_global]:
4483:                             raise RuntimeError(
4484:                                 "Jump/anticommutator branch activity mismatch in trace kernel"
4485:                             )
4486:                         jump_state = vectors[:, jump_global]
4487:                         anti_state = vectors[:, anti_global]
4488:                         jump_trace = propagator.h_z * backend.abs2_sum(jump_state)
4489:                         anti_overlap = backend.xp.sum(
4490:                             backend.xp.conj(reference_output) * anti_state
4491:                         )
4492:                         trace_value += jump_trace - propagator.h_z * backend.scalar_float(
4493:                             anti_overlap.real
4494:                         )
4495:                     kernel_survival[output_node, node] = trace_value
4496:         del batch_sources
4497:         eta_tracker.maybe_report(
4498:             backend=backend,
4499:             completed_work_units=completed_branch_steps,
4500:             batch_number=batch_number,
4501:             fine_step_completed=config.num_steps,
4502:             total_fine_steps=config.num_steps,
4503:             active_branches=0,
4504:             force=True,
4505:             event=f"completed batch {batch_number}/{total_batches}",
4506:         )
4507: 
4508:     if completed_branch_steps != total_planned_branch_steps:
4509:         raise RuntimeError(
4510:             "Internal kernel work accounting mismatch: "
4511:             f"completed {completed_branch_steps}, planned {total_planned_branch_steps}"
4512:         )
4513: 
4514:     kernel_total_probability = kernel_jump_probability + kernel_anticommutator_probability
4515:     closure_derived_survival = kernel_survival_from_panel_probability(
4516:         kernel_total_probability
4517:     )
4518:     # A nonzero insertion trace is retained explicitly, although complete
4519:     # dissipators should make it vanish to numerical precision.
4520:     causal_source_trace = np.zeros_like(kernel_survival)
4521:     for insertion_index, trace_value in enumerate(source_trace_total):
4522:         causal_source_trace[insertion_index:, insertion_index] = trace_value
4523:     closure_expected_survival = closure_derived_survival + causal_source_trace
4524:     kernel_trace_closure_residual = kernel_survival - closure_expected_survival
4525:     chi_s, chi_p, chi_g = reconstruct_response_from_kernel(
4526:         insertion_times, kernel_total_probability, kernel_survival
4527:     )
4528:     coarse = aggregate_kernel_to_coarse(
4529:         insertion_times, kernel_total_probability, kernel_survival
```

```python
6594:             atomic_savez(
6595:                 case_file(stage_dir, config.case_prefix, "kernel_summary.npz"),
6596:                 compressed=True,
6597:                 insertion_steps=kernel.insertion_steps,
6598:                 insertion_times=kernel.insertion_times,
6599:                 panel_durations=kernel.panel_durations,
6600:                 kernel_jump_probability=kernel.kernel_jump_probability,
6601:                 kernel_anticommutator_probability=kernel.kernel_anticommutator_probability,
6602:                 kernel_total_probability=kernel.kernel_total_probability,
6603:                 kernel_click_density_jump=kernel.kernel_jump_probability / kernel.panel_durations[:, None],
6604:                 kernel_click_density_anticommutator=kernel.kernel_anticommutator_probability / kernel.panel_durations[:, None],
6605:                 kernel_click_density_total=kernel.kernel_total_probability / kernel.panel_durations[:, None],
6606:                 kernel_survival=kernel.kernel_survival,
6607:                 chi_panel_probability=kernel.chi_panel_probability,
6608:                 coarse_node_indices=np.asarray(kernel.coarse["node_indices"], dtype=np.int64),
6609:                 coarse_times=np.asarray(kernel.coarse["times"], dtype=np.float64),
6610:                 coarse_kernel_probability=np.asarray(kernel.coarse["kernel_probability"], dtype=np.float64),
6611:                 coarse_kernel_survival=np.asarray(kernel.coarse["kernel_survival"], dtype=np.float64),
6612:                 coarse_chi_survival=np.asarray(kernel.coarse["chi_survival"], dtype=np.float64),
6613:                 coarse_chi_panel_probability=np.asarray(kernel.coarse["chi_panel_probability"], dtype=np.float64),
6614:                 interpretation=np.asarray(
6615:                     [
6616:                         "Rows are output panels; columns are environmental insertion state nodes. "
6617:                         "Total equals jump plus anticommutator. Entries above the causal triangle are zero."
6618:                     ],
6619:                     dtype="U512",
6620:                 ),
6621:             )
6622:             atomic_savez(
6623:                 case_file(stage_dir, config.case_prefix, "source_insertion_summary.npz"),
6624:                 compressed=True,
6625:                 insertion_steps=kernel.insertion_steps,
6626:                 insertion_times=kernel.insertion_times,
6627:                 jump_norm2=np.asarray(kernel.source_summary["jump_norm2"], dtype=np.float64),
6628:                 anti_expectation=np.asarray(kernel.source_summary["anti_expectation"], dtype=np.float64),
6629:                 trace_terms=np.asarray(kernel.source_summary["trace_terms"], dtype=np.float64),
6630:                 trace_total=np.asarray(kernel.source_summary["trace_total"], dtype=np.float64),
6631:                 activity_total=np.asarray(kernel.source_summary["activity_total"], dtype=np.float64),
6632:                 reference_survival=np.asarray(kernel.source_summary["reference_survival"], dtype=np.float64),
6633:                 reference_s_down=np.asarray(kernel.source_summary["reference_s_down"], dtype=np.float64),
6634:                 reference_s_up=np.asarray(kernel.source_summary["reference_s_up"], dtype=np.float64),
6635:                 reference_s_phi=np.asarray(kernel.source_summary["reference_s_phi"], dtype=np.float64),
6636:                 reference_top_shell=np.asarray(kernel.source_summary["reference_top_shell"], dtype=np.float64),
6637:                 branch_labels=np.asarray(kernel.source_summary["branch_labels"]),
6638:                 interpretation=np.asarray(
6639:                     [
6640:                         "Subnormalized zero-rate no-click source diagnostics. Trace_total must vanish because each complete dissipator is trace preserving."
6641:                     ],
6642:                     dtype="U512",
6643:                 ),
```