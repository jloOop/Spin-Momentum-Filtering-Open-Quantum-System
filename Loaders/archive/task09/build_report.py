#!/usr/bin/env python3
"""Build a programmatic, source-specific PDF/Markdown review. Does not run any solver."""
from pathlib import Path
import json,csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

B=Path(__file__).resolve().parents[1]
M=json.loads((B/'METRICS.json').read_text());V=json.loads((B/'VERIFICATION.json').read_text())
E=M['endpoint'];TT=M['tangent'];F=B/'figures'

def mdtable(rows,fields,labels):
 s='| '+' | '.join(labels)+' |\n|'+ '|'.join(['---']*len(fields))+'|\n'
 for r in rows:
  s+='| '+' | '.join(str(r[k]) for k in fields)+' |\n'
 return s

report=f'''# Task09 pi/1600: verified saved record through T = 10

**Review date:** 28 September 2026. **Final job:** 3463660. **Immediate parent:** job 2966988, step 19327.

## Main finding

The uploaded archive contains the full 27-array native history from t = 0 through t = 10: 20,001 state nodes and 20,000 detector intervals at dt = 0.0005. The final allocation contributes 673 steps. The full 0-to-6 and 6-to-9.6635 histories are inherited, not rerun. All 27 inherited arrays match the immediate parent byte for byte, and the earlier separately uploaded 3.6, 6 and 8.3 records match on their full supports.

The finite-rate response is small, nonzero and sign-changing in time. At T = 10, the cumulative roof-click difference against this run's own paired zero remains **{E['delta_C_saved']:.15g}**, or **{E['delta_C_relative_percent']:.9f}%** relative to the paired zero detected mass. Positive late intervals do not erase the accumulated detection deficit. This is a verified saved-output result; all nonaccepting scientific flags remain unchanged.

![Native finite-rate response](figures/01_Finite_Rate_Response_0_to10.png)

## Definitions and primary sources

Source archive: `{V['source_files'][0]['name']}`

SHA-256: `{V['source_files'][0]['sha256']}`

The primary numerical member is `OUTPUT/block_histories.npz`; `OUTPUT/checkpoint_step20000/histories.npz` is byte-identical. Output status, checkpoint metadata, independent-audit and wrapper/port records all agree on completed and persisted step 20000.

For each native detector interval, delta_g = (positive_step_click - zero_step_click)/dt at (times[n]+times[n+1])/2. C is the sum of recorded roof increments, not 1 minus retained survival. Each difference uses this trajectory's own paired zero. No curves are inferred from survival differentiation. No smoothing, interpolation, extrapolation, sample removal, or renormalization was applied. Only the separately labeled tangent comparison aggregates native probabilities into matched 0.05 panels.

The reference report `Task09_V16_Verified_Comparison_Report.pdf`, Figure 1 and page 3, supplies the definition and methodological comparison. Its old endpoints are not current input limits. This review updates pi/1600 only; it does not infer longer pi/3200 or pi/800 trajectories from this upload.

## Endpoint values

| Quantity | Saved value |
|---|---:|
| S_pi1600(10), retained | {E['S_lambda']:.16g} |
| S_0(10), paired zero | {E['S_paired_zero']:.16g} |
| C_pi1600(10), roof | {E['C_lambda_saved']:.16g} |
| C_0(10), roof | {E['C_paired_zero_saved']:.16g} |
| delta_C(10) | {E['delta_C_saved']:.16g} |
| delta_S_retained(10) | {E['delta_S_retained']:.16g} |
| B_rep(10) | {E['B_rep']:.16g} |
| B_event(10) | {E['B_event']:.16g} |
| Total retained rank | {E['rank']} |

C_pi1600 is 51.2786259022% and C_0 is 51.3820951365%. The difference is -0.1034692343 percentage points, equivalent to about 1034.69 fewer recorded roof clicks per million initial preparations. Digits identify the saved calculation, not continuum precision. Retained survival is about 0.487 at the horizon, so T=10 is not an asymptotic nondetection determination.

The endpoint metadata's positive and zero state traces differ from the corresponding history entries by about 1.11e-16, due to distinct floating reductions. Both original values are preserved; this review uses native history values for curves.

## Time-resolved response

The strongest native negative response is {M['density_minimum']['value']:.13g} at midpoint {M['density_minimum']['midpoint']:.5f}; the largest positive response is {M['density_maximum']['value']:.13g} at midpoint {M['density_maximum']['midpoint']:.5f}. These are extrema of the difference curve, not shifts of the absolute click-density peak.

The first late sign change is bracketed by midpoint 4.92375 and 4.92425. There are {M['number_post1p2_sign_changes']} adjacent-bin sign changes after t=1.2, excluding the pre-arrival numerical floor. They are listed in `sign_changes.csv`; the brackets do not locate a continuous-time zero to sub-bin accuracy and do not supply per-bin error bars.

The last detector interval is [9.9995, 10], at midpoint 9.99975. Its delta_g is {M['last_bin']['delta_g']:.13g}; its relative difference to the local paired-zero density is {M['last_bin']['relative_delta_g_percent']:.7f}%. A last-bin relative value is not the cumulative percent change.

## Window decomposition

All window masses below are unconditional with respect to the launch ensemble. Neither branch is renormalized at a window boundary. Positive/negative masses are sums of positive/negative delta_p bins.

'''+mdtable(M['window_rows'],['start','end','C_lambda_window','C_zero_window','delta_C_window','positive_response_mass','negative_response_mass'],['start','end','roof pi/1600','roof paired zero','net delta_C','positive mass','negative mass'])+f'''

Between 6 and 8.3 the response adds +0.0001423076830343043 roof probability. Between 8.3 and 10 it adds -0.0001321663564992958, cancelling most of that gain. The complete 6-to-10 interval has only +0.00001014132653500858 net added probability. The entire 3.6-to-10 interval is net negative (-0.0002120246930747597).

The deepest cumulative deficit is {M['cumulative_minimum']['value']:.13g} at node {M['cumulative_minimum']['node']}. By T=10 it has recovered {M['net_cumulative_recovery_since_minimum']:.13g} toward zero, but never closes the post-arrival cumulative deficit over the supplied window.

The integral of the retained-survival difference, using native-node trapezoids, is {E['restricted_retained_survival_change_trapezoids']:.13g}. The mean time among recorded clicks before T=10 is {E['click_conditional_mean_lambda']:.13g} for pi/1600 and {E['click_conditional_mean_zero']:.13g} for the paired zero, a difference of {E['click_conditional_mean_change']:.13g}. This is not a uniform delay assigned to individual trajectories.

## Archived tangent comparison (separate diagnostic)

The exact original U2-I case ZIP from the earlier uploaded Task07 archive was reopened; SHA-256 {TT['reference_case_sha256']}. All 14 solver-manifest hashes match. Its survival and jump-plus-anticommutator kernels independently reconstruct the saved response arrays exactly. It is copied as `reference/U2I_native_case.zip`.

At the same T=10, its integrated susceptibility from panel probabilities is {TT['chi_D_from_panel_sum']:.15g}. Multiplying by pi/1600 predicts {TT['linear_endpoint_prediction']:.15g}; the native finite-rate difference is {E['delta_C_saved']:.15g}. The finite response is about 0.152717% smaller in magnitude than this linear prediction. This percentage measures departure of the cumulative *response* from the tangent prediction, not the percent change of the original distribution or the total numerical error.

The comparison sums native finite-rate detector increments into the original 200 panels of width 0.05 without interpolation. The complete panel-record residual (including the retained no-click atom) is {TT['complete_panel_record_residual']:.13g}. This is a numerical residual diagnostic, not a certified physical curvature value. The tangent has 1e-12 response-reference/branch GMRES accuracy; the finite-rate path uses its own frozen accuracy. Insertion quadrature, finite bath-map effects, compression/state approximation, and discretization uncertainties remain separate. One positive rate at T=10 does not prove a rate-halving law or convergence. No fresh multi-rate T=10 claim is made.

## Fresh verification scope

- Exact outer ZIP, evidence text and SHA256SUMS identities match the completion record.
- All 2237 outer artifact-manifest payloads were read completely, checking CRC and SHA-256; 152 package checksum entries match.
- Embedded immediate-parent compact: 30 manifest entries and 28 additional pinned subset entries match. Its 0-to-9.6635 history and all 27 prefixes are exact. The full older 2966988 result ZIP was not separately supplied here and was not newly audited.
- Each earlier separately supplied 0-to-3.6, 0-to-6 and 0-to-8.3 history matches all 27 arrays. Four new checkpoint histories are exact prefixes of the final record.
- The original step-5496 anchors and all 29008 representation / 14504 event terms are preserved. Every full-step ledger from 5497 through 20000 was independently recomputed with math.fsum. This does not recertify missing pre-5496 spectral ancestry.
- All 1346 new compression spectra were reconstructed from their raw sector eigenvalues, including every one of 3,686,611 rank-ladder entries, admissibility masks, minimum admissible ranks, sector allocations and charges. Small negative raw Gram mass is preserved in diagnostics; it is not silently deleted from the evidence.
- All 673 new detector records and 10095 batches have completed/no-failure status, contiguous column partitions, bounded residuals and exactly reconstruct the native positive and zero click sums.
- The global H10 policy is unchanged across the 19327 restart, and every new compression is within its active allowance. The driver and selected core modules match the parent and original IO200 package bytes.

The maximum accumulated positive closure residual is {V['maximum_abs_accumulated_positive_closure']:.9g}; the corresponding paired-zero value is {V['maximum_abs_accumulated_zero_closure']:.9g}. These are accounting residuals, not complete error bars on the detector response. The supplied independent standalone zero only extends to t=3.6; no independent later zero run is fabricated.

## Preserved discrepancy and unavailable evidence

The raw `representation_ceiling` history remains the inherited constant 2.25e-7 after its relevant old stage. It is not the active H10 limit. The actual T=10 ceiling is 6.25e-7, with remaining margin 4.5879005415e-12. Raw arrays remain unchanged. `Nodes_6_to10.csv` supplies separately named active_H10_prospective_ceiling and active_H10_reserve_margin columns, computed from CONFIG with 60-digit Decimal precision. No operational budget violation was found in the checked calls.

The four new checkpoint manifests reference 24 heavy factor payloads absent from this exported ZIP. Their hashes/traces were recorded on PC2, but those factors were not independently read here. This export supports the stored detector curves, not arbitrary density-matrix observables or a restart on another machine. Earlier full spectral/telemetry records are not automatically part of the child archive just because the full scalar history is inherited. Keep the original PC2 checkpoints and result archives.

The saved flags remain physical_claim=false, production_authorized=false, task10_eligible=false, automatic_resume=false. The named CERTIFIED_PI1600_CONTINUATION_TO1000 classification is a numerical workflow status, not a blanket physics/convergence claim.

## Use in the existing analysis

Treat `original/OUTPUT/block_histories.npz` as the single complete pi/1600 curve through T=10 after the verified overlap checks. Do not append the earlier prefixes again. Keep all other rates at their own verified endpoints; compare rates only on common available support. The new first-plot input is data/Plot_Data_0_to10.npz (delta_g against own paired zero). Full-resolution node/interval CSVs are also provided for 0-to-10 and 6-to-10.

No original input or solver was modified, no PC2 job was run, and no GPU propagation was performed during this review.
'''
(B/'REPORT.md').write_text(report)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleX',fontName='Helvetica-Bold',fontSize=21,leading=25,spaceAfter=12,textColor=colors.HexColor('#17354A')))
styles.add(ParagraphStyle(name='SubX',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=9,textColor=colors.HexColor('#4A5660')))
styles.add(ParagraphStyle(name='BodyX',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='SmallX',fontName='Helvetica',fontSize=8.1,leading=10.8,spaceAfter=6))
styles.add(ParagraphStyle(name='HeadX',fontName='Helvetica-Bold',fontSize=13,leading=17,spaceBefore=6,spaceAfter=7,textColor=colors.HexColor('#17354A')))
W,H=A4;usable=W-80
story=[]
def P(s,style='BodyX'):return Paragraph(s,styles[style])
def add(s,style='BodyX'):story.append(P(s,style))
def table(rows,widths=None,small=False):
 st=styles['SmallX' if small else 'BodyX']
 tab=Table([[Paragraph(str(x),st) for x in r] for r in rows],colWidths=widths or [usable/len(rows[0])]*len(rows[0]),hAlign='LEFT',repeatRows=1)
 tab.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EFF3')),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#9CAEB8')),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]))
 story.append(tab);story.append(Spacer(1,8))
def img(name):story.append(Image(str(F/(name+'.png')),width=usable,height=usable*.56));story.append(Spacer(1,6))
def nextpage():story.append(PageBreak())

add('Task09 | finite-rate record to T = 10','TitleX')
add('pi/1600 upward bath • final job 3463660 • independent saved-output review • 28 September 2026','SubX')
add('<b>The full history is present, and the cumulative deficit remains.</b> All 27 native arrays cover 0 to 10 at dt = 0.0005. The last allocation adds 673 steps without changing the inherited prefixes.')
img('01_Finite_Rate_Response_0_to10')
table([['Endpoint quantity','pi/1600','Own paired zero'],['Retained survival S(10)',f"{E['S_lambda']:.13f}",f"{E['S_paired_zero']:.13f}"],['Roof clicks C(10)',f"{E['C_lambda_saved']:.13f}",f"{E['C_paired_zero_saved']:.13f}"]],widths=[170,(usable-170)/2,(usable-170)/2])
add(f'<b>Delta C(10) = {E["delta_C_saved"]:.13f}.</b> This is -0.1034692343 percentage points, or -0.201372159% relative to the paired-zero detected fraction. About 1034.69 fewer recorded roof clicks per million initial preparations.')
add('Data source: OUTPUT/block_histories.npz, identical to the final checkpoint history. The native midpoint increment divided by dt defines each plotted density. All scientific nonaccepting flags remain unchanged.','SmallX')
nextpage()
add('Where the late-time recovery goes','TitleX')
add('Window decomposition from full-resolution detector increments','SubX')
img('02_Cumulative_Response_0_to10')
wr=[r for r in M['window_rows'] if (r['start'],r['end']) in [(0,3.6),(3.6,6),(6,8.3),(8.3,10),(6,10)]]
table([['Window','Net added roof probability','Interpretation']]+[[f"{r['start']:g} to {r['end']:g}",f"{r['delta_C_window']:+.12f}",'Suppression' if r['delta_C_window']<0 else 'Enhancement in this window'] for r in wr],widths=[95,180,usable-275],small=True)
add('The gain accumulated over 6 to 8.3 is almost cancelled by the loss over 8.3 to 10. The full 6-to-10 window adds only +1.01413e-5; it does not remove the deficit inherited at t = 6.')
add(f"The deepest cumulative deficit is {M['cumulative_minimum']['value']:.12f} at node t = 4.924. All window values use the launch ensemble, with no conditional renormalization at the left boundary.")
add('Source: window_masses.csv and endpoints.csv. Saved cumulative subtraction and the independent sums differ only at floating-point summation scale; both are retained in the data tables.','SmallX')
nextpage()
add('Sign-changing response, not uniform delay','TitleX')
add('Native-bin extrema and late-time structure','SubX')
img('03_Late_Response_6_to10')
table([['Diagnostic','Value'],['Strongest negative difference',f"{M['density_minimum']['value']:.11g} at midpoint 2.65625"],['Strongest positive difference',f"{M['density_maximum']['value']:.11g} at midpoint 5.17725"],['Last bin [9.9995, 10]',f"Delta g = {M['last_bin']['delta_g']:.11g}"],['First late negative-to-positive bracket','4.92375 to 4.92425 (adjacent midpoints)'],['Last positive-to-negative bracket','9.78575 to 9.78625 (adjacent midpoints)']],widths=[220,usable-220],small=True)
add('There are 18 sampled sign changes after t = 1.2. The brackets are statements about adjacent interval-average samples, not continuous-time zeros or independently certified per-bin significance. All brackets are in sign_changes.csv.')
add('The retained-survival integral changes by +0.006973068095. The click-conditioned mean before T = 10 changes by only +0.0002302015364. Different censored subsets and temporal redistribution must not be summarized as a single uniform delay.')
add('The absolute densities nearly overlap (Figure 04 in the package). Retained survival near 0.487 at T = 10 is not a determination of permanent nondetection.','SmallX')
nextpage()
add('Independent check against the archived tangent','TitleX')
add('Separate diagnostic: original U2-I case, matched 0.05 panels','SubX')
img('05_Archived_Tangent_Comparison')
table([['Quantity at T = 10','Value'],['Archived integrated susceptibility',f"{TT['chi_D_from_panel_sum']:.13g}"],['Linear prediction: (pi/1600) times chi_D',f"{TT['linear_endpoint_prediction']:.13g}"],['Native finite-rate cumulative response',f"{E['delta_C_saved']:.13g}"],['Finite minus linear',f"{TT['finite_minus_linear_endpoint']:.9g}"],['Smaller response magnitude than linear','0.152717%']],widths=[310,usable-310],small=True)
add('The exact earlier U2-I case archive was reopened: all 14 solver-manifest hashes match, and its jump-plus-anticommutator and survival kernels reconstruct the saved response arrays exactly. Native finite-rate probabilities were summed into its 200 panels without interpolation.')
add('<b>Interpretive limit:</b> 0.152717% is the departure of the cumulative response from the numerical tangent prediction, not the distribution change or total numerical error. One finite rate at T = 10 does not establish a rate-halving law, physical curvature, or full convergence. The reference/branch tolerances and insertion quadrature remain distinct numerical controls.','SmallX')
nextpage()
add('What was freshly verified','TitleX')
add('Integrity, continuity and numerical accounting are separate from physical acceptance','SubX')
table([['Fresh check','Verified coverage'],['Input/manifest integrity','ZIP, evidence and sidecar pins; all 2237 artifact payloads; 152 package checksum entries'],['Immediate parent','30 compact hashes and 28 pinned subset hashes; all 27 history prefixes through step 19327 unchanged'],['Earlier records','27 exact arrays each against the separate 3.6, 6 and 8.3 uploads'],['Checkpoint histories','Four new checkpoints: 19400, 19600, 19800, 20000; all exact trajectory prefixes'],['Ordered error ledgers','Original step-5496 anchors; 29008 representation and 14504 event terms; all later node totals reconstructed'],['New spectral compression','1346 calls; 3,686,611 rank-ladder entries; admissibility, minimum ranks, sector allocations and charges'],['New detector telemetry','673 steps, 10095 completed batches; exact click sums, no recorded GMRES failures'],['Restart equivalence','Unchanged propagation-driver/core bytes and unchanged global H10 policy']],widths=[155,usable-155],small=True)
add('Accounting values','HeadX')
add(f"Max full-history absolute residual: S + C + B_rep + B_event - S(0) = {V['maximum_abs_accumulated_positive_closure']:.4e}; paired-zero residual = {V['maximum_abs_accumulated_zero_closure']:.4e}. These are not complete error bars on the physical response.")
add('Known discrepancy retained','HeadX')
add('The raw history representation_ceiling remains 2.25e-7. It is stale, not the actual H10 allowance. CONFIG and the operational records set the T = 10 limit to 6.25e-7; the final ledger is 6.249954120994585e-7. The separately named active-policy columns in Nodes_6_to10.csv preserve this distinction without altering original arrays.')
add('Evidence not supplied or not rerun','HeadX')
add('The four checkpoint manifests reference 24 omitted heavy sector/zero-state factor files. Their PC2 trace/hash reports are retained, but the factors were not read here. Earlier absent spectral telemetry and pre-5496 ancestry are not newly certified. The standalone zero reference supplied in this lineage ends at 3.6. No GPU, remote job, production solver or bundled auditor was executed.','SmallX')
add('Physical_claim, production_authorized, task10_eligible and automatic_resume remain false. The full verification record, source hashes, all data tables, five figures, preserved original members and rerunnable analysis scripts accompany this report.','SmallX')

def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#D7E0E5'));c.line(40,37,W-40,37);c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#5D6C75'))
 c.drawString(40,25,'Task09 pi/1600 | job 3463660 | saved-output review, not physical acceptance')
 c.drawRightString(W-40,25,str(doc.page))
doc=SimpleDocTemplate(str(B/'Task09_Pi1600_T10_Verified_Report.pdf'),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=38,bottomMargin=48,title='Task09 pi/1600: verified saved record through T=10',author='Independent numerical review')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(B/'Task09_Pi1600_T10_Verified_Report.pdf')
