#!/usr/bin/env python3
"""Generate separate vector/full-resolution native-response figures. Requires matplotlib/numpy."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

folder=Path(__file__).resolve().parents[1]
figures=folder/'figures';figures.mkdir(exist_ok=True)
matplotlib.rcParams['path.simplify']=False
matplotlib.rcParams['pdf.fonttype']=42
matplotlib.rcParams['svg.fonttype']='none'
with np.load(folder/'data/Plot_Data_0_to10.npz',allow_pickle=False) as data:curves={k:data[k] for k in data.files}

def finish(fig,ax,name,caption):
 ax.set_xlabel('Time, t',fontsize=12);ax.grid(True,alpha=.2);ax.tick_params(labelsize=10)
 fig.subplots_adjust(left=.13,right=.97,bottom=.19,top=.88);fig.text(.13,.045,caption,fontsize=9)
 for ext in ('png','svg','pdf'):fig.savefig(figures/f'{name}.{ext}',dpi=220)

fig=plt.figure(figsize=(10,5.6));ax=fig.add_subplot(111)
ax.plot(curves['midpoint_times'],curves['delta_g'],linewidth=1.6,marker='o',markevery=[len(curves['delta_g'])-1],markersize=4,label=r'$\lambda=\pi/1600$, saved through $T=10$')
ax.axhline(0,linewidth=.8,alpha=.5);ax.axvline(3.6,linestyle=':',linewidth=1,alpha=.5);ax.set_xlim(0,10)
ax.set_ylabel(r'$\Delta g_\lambda(t)=[p_\lambda-p_0]/\Delta t$',fontsize=12)
ax.set_title('Finite-rate roof-click response: complete record to T = 10',fontsize=14)
ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3));ax.legend(loc='lower right',fontsize=10)
finish(fig,ax,'01_Finite_Rate_Response_0_to10','Own paired zero; 20,000 native intervals, Δt = 0.0005. Dotted line: t = 3.6.\nNo smoothing, renormalization or extrapolation. Saved-output result; nonaccepting status retained.')
plt.show();plt.close(fig)

fig=plt.figure(figsize=(10,5.6));ax=fig.add_subplot(111)
ax.plot(curves['times'],curves['delta_C'],linewidth=1.6,marker='o',markevery=[len(curves['times'])-1],markersize=4)
ax.axhline(0,linewidth=.8,alpha=.5);ax.set_xlim(0,10);ax.set_ylabel(r'$\Delta C_\lambda(t)=C_\lambda(t)-C_0(t)$',fontsize=12)
ax.set_title('Cumulative roof detection remains suppressed at T = 10',fontsize=14);ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3))
finish(fig,ax,'02_Cumulative_Response_0_to10','Computed from saved cumulative roof-click probabilities, cross-checked against summed increments.\nThe final difference is −0.001034692343; representation and omitted-event losses are not clicks.')
plt.close(fig)

fig=plt.figure(figsize=(10,5.6));ax=fig.add_subplot(111);mask=curves['midpoint_times']>=6
ax.plot(curves['midpoint_times'][mask],curves['delta_g'][mask],linewidth=1.6)
ax.axhline(0,linewidth=.8,alpha=.5);ax.axvline(8.3,linestyle=':',linewidth=1,alpha=.5);ax.set_xlim(6,10)
ax.set_ylabel(r'$\Delta g_\lambda(t)$',fontsize=12);ax.set_title('Late response: alternating enhancement and suppression',fontsize=14);ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3))
finish(fig,ax,'03_Late_Response_6_to10','All 8,000 native detector intervals from t = 6 to 10. Dotted line: earlier snapshot at t = 8.3.\nPositive density-response intervals do not imply a positive cumulative response.')
plt.close(fig)

fig=plt.figure(figsize=(10,5.6));ax=fig.add_subplot(111)
ax.plot(curves['midpoint_times'],curves['g_lambda'],linewidth=1.6,label=r'Finite rate $\pi/1600$')
ax.plot(curves['midpoint_times'],curves['g_paired_zero'],linestyle='--',linewidth=1.3,label='Own paired zero');ax.set_xlim(0,10)
ax.set_ylabel(r'Roof-click density $g(t)$',fontsize=12);ax.set_title('Absolute densities: small differences on a common overall profile',fontsize=14);ax.legend(fontsize=10)
finish(fig,ax,'04_Absolute_Densities_0_to10','The absolute densities nearly overlap; the dedicated difference plot displays the small nonzero response.\nThese are finite-window, subnormalized saved records—not conditional or asymptotic distributions.')
plt.close(fig)

with np.load(folder/'data/Tangent_Comparison.npz',allow_pickle=False) as a:tan={k:a[k] for k in a.files}
w=np.diff(tan['times']);mid=(tan['times'][:-1]+tan['times'][1:])/2
fig=plt.figure(figsize=(10,5.6));ax=fig.add_subplot(111)
ax.plot(mid,tan['finite_delta_panels']/w,linewidth=1.6,label='Finite-rate response, summed into matched panels')
ax.plot(mid,tan['linear_delta_panels']/w,linestyle='--',linewidth=1.3,label=r'Archived U2-I prediction $\lambda\chi_g$');ax.axhline(0,linewidth=.8,alpha=.5);ax.set_xlim(0,10)
ax.set_ylabel('Matched-panel average response',fontsize=12);ax.set_title('Comparison with the archived zero-rate tangent',fontsize=14);ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3));ax.legend(fontsize=9,loc='lower right')
finish(fig,ax,'05_Archived_Tangent_Comparison','200 matched panels of width 0.05; probabilities summed without interpolation.\nSingle-rate descriptive consistency check—not a new rate-halving or convergence certificate.')
plt.close(fig)
print(f'Five separate figures saved in PNG, SVG and PDF: {figures}')
