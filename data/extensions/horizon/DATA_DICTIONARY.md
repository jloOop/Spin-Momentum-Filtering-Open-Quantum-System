# Data dictionary and reduction lineage

All time coordinates use the campaign's native simulation units. No SI conversion is available or assumed. No rates or susceptibilities are relabeled as probabilities.

## Native evidence

`inputs/lineage.json` maps every captured file to the original archive path, immutable archive SHA-256, member path, member SHA-256 and byte count. Captured files are exact byte copies. `input_array_inventory.csv` lists every field in these native NumPy containers with shape, dtype, axes and units; interpretation strings remain intact. Source writer excerpts give the authoritative conventions.

- `kernel_survival[i,j]` = q(T_i,s_j), signed survival derivative per unit pulse action, no source-time weight. Shape401x401 (T10:201x201).
- `kernel_total_probability[k,j]` = P[k,j], signed roof probability integrated over output interval[T_k,T_(k+1)] per unit pulse action, no source-time weight. Shape400x401. Its signed jump and anticommutator pieces have the same orientation. Source columns correspond to complete unobserved dissipators; branch labels are numerical factors.
- `kernel_click_density_*` = corresponding P divided by output panel duration only. Causal-zero region j>k for roof and j>i for q. Tiny diagonal q source-trace residues are retained.
- Native `chi_survival` is the endpoint-local source integral of q, and has units of native time (probability derivative per bath rate). `chi_panel_probability` is the similarly weighted P response, also native-time units. `chi_click_density` is a panel-average derivative, not pointwise density.
- `activity_total`, `jump_norm2`, `anti_expectation` and source trace fields are subnormalized physical traces. `reference_s_up`, `reference_s_down`, `reference_s_phi` and `reference_top_shell` are conditioned on survival; the first two are upward/downward source strengths, not physical-spin components. `reference_s_phi` is a sum of number variances, not phase or spin angle.
- Matched baseline `times`/`survival` have80001 detector nodes; `step_probability`/`click_density` have80000 midpoint intervals. Source-up/down/top fields are conditional at those nodes. `insertion_steps` selects401 source nodes. The baseline probability arrays are used directly, never reconstructed by differencing sampled survival.
- `coarse_*` within native kernels is an internal aggregation, not an independent run. `full_tangent_benchmark.npz` is preserved as recorded small benchmark evidence; no benchmark evolution is rerun.

## Preparation names

`00`, `10`, `01` denote independently completed oscillator preparations, with the same physical spin. `first`=(10+01)/2, `p060`=.4*00+.6*first, `pold` uses exactly0.8104003212089722, and `p095`=.05*00+.95*first. Mixtures are formed at the signed-array level before norms, conditional ratios or inferred roots.

## Reconstructed outputs

- `reconstructed_arrays.npz`: `times`[401]; `preparation_names`[7]; `chi_survival`[7,401]; `chi_panel_probability`[7,400]; `profile_horizons`[5]; `profiles_I_roof` and `profiles_I_survival`[7,5,401], with future-source entries retained as causal zeros; `source_block_roof_histories`[7,3,401] with source blocks[0,3.6],[3.6,10],[10,20]. I is dimensionless per unit pulse action, while its unnormalized source integral is a rate susceptibility.
- `pulse_gate_laws.npz`: `pulse_preparations` and `pulse_source_times` index pulse rows. `pulse_panel_probability`[candidate,400] and `pulse_survival_history`[candidate,401] are complete signed unit-action pulse laws. Terminal survival at index-1 is the no-click censoring atom.
- Gate rows are indexed by `gate_preparations` and `gate_windows`[gate,2]. `gate_panel_probability`[gate,400] and `gate_survival_history`[gate,401] use normalized rectangular f=1/window-duration and causal endpoint-local source quadrature at every horizon. The final survival element is retained, not zeroed.
- `component_baseline_panel_probability`[3,400] order00,10,01 is the exact sum of consecutive native200-detector-step probabilities. The full detector histories remain in captured inputs. `inferred_shell2_panel_probability`[400] and `inferred_shell2_survival`[401] are **INFERRED_FROM_LAUNCH_KERNEL**, not additional simulations.
- `chi_mu_restricted` integrates chi_S over observation time with native trapezoids and has native-time-squared units when differentiating a mean time with respect to a rate. A_TV has rate-response units and includes terminal survival.
- `positive_integral`/`negative_integral` partition signed trapezoidal node contributions, without interpolation or modifying data. `positive_nodal_measure`/`negative_nodal_measure` are quadrature weights summed over resolved sign nodes. `native_span` is last-minus-first saved node and does not locate an unsaved zero crossing. Cancellation ratio=(positive-negative)/abs(net).
- Every source/output block is a signed probability response per rate. Output panels sum first, then source weights are applied once. Shared source edges receive one half-weight from each neighboring window. Noncausal source/output blocks are exactly zero.
- Root CSV blanks carry explicit statuses (`unresolved_denominator` or `outside_unit_interval`); other CSV blanks indicate not applicable. NaN in numerical ratio arrays, if present, means a screened denominator, not zero. No physical clipping or renormalization is performed.
- Raw and screened cumulative crossings are distinguished. `panel_average_density_response` crossings are between saved panel averages, with midpoint coordinates; they are not pointwise instantaneous zeros. Screened brackets may span intervening unresolved nodes; the count is explicit.

## Table schemas

Each CSV is UTF-8 with one header row and full round-trip floating-point values. The following column lists are generated directly from the delivered tables.

### case_inventory.csv

`mode`, `case`, `native_status`, `native_exit`, `source_sha256`, `numerical_core_sha256`, `initial_activity`, `final_D_survival`, `final_D_roof`

### extrema.csv

`preparation`, `kind`, `T`, `response`

### gate_predictions.csv

`preparation`, `start`, `end`, `duration`, `terminal_D_roof`, `terminal_D_survival`, `terminal_survival_atom`, `A_TV_pulse_action`, `activity_per_unit_action`, `law_closure`, `label`

### late_change_decomposition.csv

`preparation`, `delta_survival`, `delta_roof`, `delayed_earlier_action`, `new_action_after10`, `sum`, `closure_residual`, `delayed_fraction`

### mixture_crossings.csv

`T`, `p_star_survival`, `denominator_survival`, `status_survival`, `p_star_roof`, `denominator_roof`, `status_roof`

### prefix_comparison.csv

`mode`, `quantity`, `max_abs`, `exact_equal`

### pulse_candidates.csv

`preparation`, `sign`, `s`, `terminal_D_roof`, `terminal_D_survival`, `neighborhood_start`, `neighborhood_end`, `neighbor_min`, `neighbor_max`, `normalized_narrow_gate_roof`, `law_closure`, `label`

### response_history.csv

`preparation`, `p`, `T`, `chi_D_survival`, `chi_D_roof`, `chi_S`, `chi_mu_restricted`, `A_TV_with_censoring`, `own_baseline_S`, `own_baseline_D_roof`, `own_baseline_D_survival`, `activity`, `activity_per_survivor`

### same_insertion_horizon_crossings.csv

`preparation`, `source_s`, `left`, `right`, `left_value`, `right_value`, `direction`, `unresolved_nodes_between`

### selected_horizons.csv

`preparation`, `p`, `T`, `chi_D_survival`, `chi_D_roof`, `chi_S`, `chi_mu_restricted`, `A_TV_with_censoring`, `own_baseline_S`, `own_baseline_D_roof`, `own_baseline_D_survival`, `activity`, `activity_per_survivor`

### shell_detectability.csv

`T`, `D_shell0_roof`, `D_shell1_roof`, `D_shell2_INFERRED_roof`, `D_shell0_survival`, `D_shell1_survival`, `D_shell2_INFERRED_survival`, `launch_I0`, `launch_I1`, `preceding_shell2_inferred_panel`

### shell_ordering_intervals.csv

`contrast`, `sign`, `first_T`, `last_T`, `native_span`, `node_count`

### sign_changes.csv

`preparation`, `quantity`, `screen`, `left`, `right`, `left_value`, `right_value`, `direction`, `unresolved_nodes_between`

### sign_persistence.csv

`preparation`, `sign`, `first_T`, `last_T`, `native_span`, `node_count`

### source_block_histories.csv

`preparation`, `source_start`, `source_end`, `T`, `chi_roof`, `chi_survival`, `jump`, `signed_anticommutator`

### source_output_blocks.csv

`preparation`, `output_start`, `output_end`, `source_start`, `source_end`, `total`, `jump`, `signed_anticommutator`

### source_profile_summary.csv

`preparation`, `T`, `positive_integral`, `negative_integral`, `net`, `cancellation_ratio`, `positive_nodal_measure`, `negative_nodal_measure`, `maximum`, `maximum_s`, `minimum`, `minimum_s`

### source_profiles.csv

`preparation`, `T`, `s`, `I_roof`, `I_survival`, `activity`, `activity_per_survivor`, `I_over_activity`

### source_sign_intervals.csv

`preparation`, `T`, `sign`, `first_T`, `last_T`, `native_span`, `node_count`

