"""T1: the MOC macro against the final-hour dealing range (FHDR, 15:00-15:49) and its algorithmic range projection (ARP,
-0.5 = half the range beyond the side that is run). Base rates, where the run stops, and whether -0.5 is special:
 - stop hazard: of runs that reached a depth, how many stopped within the next 1/16 R, at 0.5 vs other eighths;
 - first-touch hold at each extension level (back an eighth of R before another eighth through), -0.5 vs the others;
 - clustering of the run's extreme on the FHDR eighths vs a randomly shifted grid."""
import sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
cols = ['coef', 'p', 'n', '18-24', 'p_18-24', '25-26', 'p_25-26', 'ES', 'NQ', 'RTY', 'ok']
D = pd.read_pickle('days.pkl'); D['date'] = D.day; D = D.set_index('date')
D['R'] = D.fH - D.fL; D = D[D.R > 4 * D.tick].copy()
D['R_adr'] = D.R / D.adr
print('FHDR / ADR20 median', D.R_adr.median().round(3), ' n', len(D))
for w, hi, lo in (('15:50-15:59', 'mH', 'mL'), ('15:50-16:14', 'xH', 'xL')):
    th, tl = D[hi] > D.fH, D[lo] < D.fL
    ah, al = D[hi] >= D.fH + 0.5 * D.R, D[lo] <= D.fL - 0.5 * D.R
    print(f'{w}: FHDR high taken {th.mean():.3f}, low {tl.mean():.3f}, either {(th | tl).mean():.3f}, both {(th & tl).mean():.3f} | ARP -0.5 above {ah.mean():.3f}, below {al.mean():.3f}, either {(ah | al).mean():.3f}')
    print(f'      given the side was taken: ARP reached above {ah[th].mean():.3f}, below {al[tl].mean():.3f}')
# depth of the run beyond each taken side (extended window), in R
dep = pd.concat([D[D.xH > D.fH].assign(dep=lambda d: (d.xH - d.fH) / d.R, side='H'), D[D.xL < D.fL].assign(dep=lambda d: (d.fL - d.xL) / d.R, side='L')])
print('depth beyond the side (R) quantiles', dep.dep.quantile([.25, .5, .75, .9]).round(3).tolist(), 'n', len(dep))
# stop hazard per 1/16-R band: P(stop in [k, k+1/16) | reached k)
edges = np.arange(0, 1.5001, 1 / 16)
hz = [(round(k, 4), ((dep.dep >= k) & (dep.dep < k + 1 / 16)).sum() / max((dep.dep >= k).sum(), 1), (dep.dep >= k).sum()) for k in edges[:-1]]
print('stop hazard by band (k, P(stop in band | reached k), n):'); print([(k, round(p, 3), n) for k, p, n in hz])
# is the band just past -0.5 (0.5..0.5625) or around it (0.4375..0.5625) a stopping band more than neighbours? compare the
# hazard in [0.4375, 0.5625) to the hazard in the bands centred on 0.375 and 0.625 of the same width
def haz(lo, w=0.125):
    m = dep.dep >= lo
    return dep[m].assign(y=((dep.dep[m] < lo + w)).astype(float))
H5 = pd.concat([haz(0.4375).assign(at=1.0), haz(0.3125).assign(at=0.0), haz(0.5625).assign(at=0.0)])
rows = [check(H5, 'y ~ at', 'at', test='run stops within 1/16 R of -0.5 vs of -0.375 / -0.625')]
# first-touch hold at extension levels during 15:50-16:14 (needs the bars): done in rct_t1b
# clustering of the run extreme on the FHDR eighths vs a shifted grid
u = np.random.default_rng(5).uniform(0, 1, len(dep))
dep['d8'] = np.abs(8 * dep.dep - np.round(8 * dep.dep)); dep['q8'] = np.abs(8 * dep.dep + u - np.round(8 * dep.dep + u))
E = dep[dep.dep <= 1.5]
P = pd.concat([E.assign(y=E.d8, real=1.0), E.assign(y=E.q8, real=0.0)])
print('run extreme to the nearest FHDR eighth: real', E.d8.mean().round(4), 'shifted', E.q8.mean().round(4))
rows.append(check(P, 'y ~ real', 'real', test='MOC extreme closer to FHDR eighths than a shifted grid'))
print(table(rows)[cols].to_string())
