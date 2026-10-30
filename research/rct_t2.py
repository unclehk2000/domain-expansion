"""T2-T6 for the NY PM study (✓ = pooled p < 0.05 clustered by date, same sign in 2018-24 and 2025-26 and on each symbol)."""
import sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
cols = ['coef', 'p', 'n', '18-24', 'p_18-24', '25-26', 'p_25-26', 'ES', 'NQ', 'RTY', 'ok']
X = pd.read_pickle('days2.pkl'); X['date'] = X.day; X = X.set_index('date')
X['D'] = X.dH - X.dL; X['R'] = X.fH - X.fL; X['pmR'] = X.pmH - X.pmL
rows = []
pr = lambda *a: print(*a)

pr('=== T2  daily-range octant / 16th / quadrant from the day\'s extreme as MOC targets')
hi = X[X.C1549 >= X.dL + 0.5 * X.D].copy(); lo = X[X.C1549 < X.dL + 0.5 * X.D].copy()
hi['ret'] = (hi.dH - hi.xL) / hi.D; lo['ret'] = (lo.xH - lo.dL) / lo.D           # MOC extended extreme, measured from the day's extreme
hi['now'] = (hi.dH - hi.C1549) / hi.D; lo['now'] = (lo.C1549 - lo.dL) / lo.D     # where price is at 15:50, same units
R2 = pd.concat([hi, lo])
for k, nm in ((0.125, 'octant'), (0.1875, '16th'), (0.25, 'quadrant')):
    g = R2[R2.now < k]
    pr(f'  price inside the {nm} at 15:50 ({len(g)} days): MOC reached the {nm} {(g.ret >= k).mean():.3f}')
g = R2[(R2.ret > R2.now) & (R2.ret <= 0.5)].copy()        # the MOC moved away from the extreme
u = np.random.default_rng(9).uniform(0, 1, len(g))
g['d16'] = np.abs(16 * g.ret - np.round(16 * g.ret)); g['q16'] = np.abs(16 * g.ret + u - np.round(16 * g.ret + u))
P = pd.concat([g.assign(y=g.d16, real=1.0), g.assign(y=g.q16, real=0.0)])
pr('  MOC extreme to the nearest daily 16th: real', g.d16.mean().round(4), 'shifted', g.q16.mean().round(4))
rows.append(check(P, 'y ~ real', 'real', test='T2 MOC extreme lands on daily-range 16ths (vs shifted)'))
def haz(d, lo_, w):
    m = d.ret >= lo_
    return d[m].assign(y=(d.ret[m] < lo_ + w).astype(float))
gg = R2[R2.ret > R2.now]
HZ = pd.concat([haz(gg, k - 1 / 64, 1 / 32).assign(at=1.0) for k in (0.125, 0.1875, 0.25)] + [haz(gg, k - 1 / 64, 1 / 32).assign(at=0.0) for k in (0.09375, 0.15625, 0.21875, 0.28125)])
rows.append(check(HZ, 'y ~ at', 'at', test='T2 MOC stops within 1/64 D of octant/16th/quadrant vs 1/32 offsets'))

pr('=== T3  which side the MOC runs, and its direction')
X['mdir'] = (X.mC > X.O1550).astype(float); X['xdir'] = (X.xC > X.O1550).astype(float)
X['tr'] = ((X.C1549 - X.O930) / X.D).clip(-1, 1); X['pday'] = (X.C1549 - X.dL) / X.D; X['posF'] = ((X.C1549 - X.fL) / X.R).clip(0, 1)
f = X[(X.mxHt >= 0) | (X.mxLt >= 0)].copy()
f['upfirst'] = np.where(f.mxLt < 0, 1.0, np.where(f.mxHt < 0, 0.0, np.where(f.mxHt == f.mxLt, np.nan, (f.mxHt < f.mxLt).astype(float))))
f = f.dropna(subset=['upfirst'])
pr('  MOC up (15:59 close > 15:50 open)', X.mdir.mean().round(3), '| FHDR high taken first (when one is)', f.upfirst.mean().round(3), 'n', len(f))
for q in (0.25, 0.5, 0.75):
    pass
X['trb'] = pd.cut(X.tr, [-1, -0.5, -0.2, 0.2, 0.5, 1], labels=['strong down', 'down', 'flat', 'up', 'strong up'])
pr(X.groupby('trb')[['mdir', 'xdir']].mean().round(3).T.to_string())
rows.append(check(X, 'mdir ~ tr', 'tr', test='T3 MOC direction vs the day\'s trend at 15:50 (long in the tooth: < 0)'))
rows.append(check(X, 'xdir ~ tr', 'tr', test='T3 MOC to 16:14 direction vs the day\'s trend'))
f['posF_c'] = f.posF - 0.5
rows.append(check(f, 'upfirst ~ posF_c', 'posF_c', test='T3 FHDR side taken first vs where price sits in it at 15:50'))
f['sm'] = np.select([(f.eqH10 >= 2) & (f.eqL10 < 2), (f.eqL10 >= 2) & (f.eqH10 < 2)], [1.0, -1.0], 0.0)
pr('  smooth highs only', (f.sm == 1).mean().round(3), 'smooth lows only', (f.sm == -1).mean().round(3))
pr('  high taken first: smooth highs', f[f.sm == 1].upfirst.mean().round(3), '| smooth lows', f[f.sm == -1].upfirst.mean().round(3), '| neither / both', f[f.sm == 0].upfirst.mean().round(3))
rows.append(check(f[f.sm != 0], 'upfirst ~ sm', 'sm', test='T3 MOC runs the smooth (equal) side first'))
rows.append(check(f[f.sm != 0], 'upfirst ~ sm + posF_c', 'sm', test='T3 smooth side first, position held'))
# after the smooth side is taken, the opposite side by 16:14 (turtle soup)
sm = X.assign(sm=np.select([(X.eqH10 >= 2) & (X.eqL10 < 2), (X.eqL10 >= 2) & (X.eqH10 < 2)], [1, -1], 0))
ts = sm[sm.sm != 0].copy()
ts['smooth_taken'] = np.where(ts.sm == 1, ts.xH > ts.fH, ts.xL < ts.fL); ts['other_taken'] = np.where(ts.sm == 1, ts.xL < ts.fL, ts.xH > ts.fH)
pr('  smooth side taken by 16:14', ts.smooth_taken.mean().round(3), '| jagged side', ts.other_taken.mean().round(3), '| jagged after smooth (both)', (ts.smooth_taken & ts.other_taken).mean().round(3))
P = pd.concat([ts.assign(y=ts.smooth_taken.astype(float), real=1.0), ts.assign(y=ts.other_taken.astype(float), real=0.0)])
rows.append(check(P, 'y ~ real', 'real', test='T3 smooth side taken more than the jagged side (MOC to 16:14)'))

pr('=== T4  the PM dealing range 13:30-13:59')
p = X[X.pmR > 2 * X.tick].copy(); p['pos14'] = ((p.pmC - p.pmL) / p.pmR).clip(0, 1)
p['oct'] = pd.cut(p.pos14, np.arange(0, 1.001, 0.125), include_lowest=True, labels=False)
q = p.dropna(subset=['pm_up_1614'])
pr('  broken by 16:14', p.pm_up_1614.notna().mean().round(3), '| first break up', q.pm_up_1614.mean().round(3))
pr('  first break up by the 13:59 close octant:', q.groupby('oct').pm_up_1614.mean().round(3).to_dict())
rows.append(check(q.assign(c=q.pos14 - 0.5), 'pm_up_1614 ~ c', 'c', test='T4 PMDR first break direction vs 13:59 close position'))
q['hold'] = np.where(q.pm_up_1614 == 1, ~q.pm_loT_1614, ~q.pm_hiT_1614).astype(float)
pr('  first break held (other side not taken by 16:14)', q.hold.mean().round(3))
pr('  ARP -0.5 reached by 16:14: above', p.pm_arpU_1614.mean().round(3), 'below', p.pm_arpD_1614.mean().round(3), '| on the first-break side', np.where(q.pm_up_1614 == 1, q.pm_arpU_1614, q.pm_arpD_1614).mean().round(3))
for k in (1.0, 1.5, 2.0):
    pr(f'  {k} SD on the first-break side by 16:14', np.where(q.pm_up_1614 == 1, q[f'pm_sd{k}U_1614'], q[f'pm_sd{k}D_1614']).mean().round(3))
pr('  PMDR high taken in the MOC macro', p.pm_hi_moc.mean().round(3), 'low', p.pm_lo_moc.mean().round(3))
p['pmR_adr'] = p.pmR / p.adr; pr('  PMDR / ADR20 median', p.pmR_adr.median().round(3))
# untaken PMDR side at 15:50 -> taken in the MOC?
un = p.copy(); un['hi_open'] = ~un.pm_hiT_1549; un['lo_open'] = ~un.pm_loT_1549
a = un[un.hi_open & ~un.lo_open]; b_ = un[un.lo_open & ~un.hi_open]
pr('  only the PMDR high still untaken at 15:50:', len(a), 'days; MOC (to 16:14) takes it', (a.xH > a.pmH).mean().round(3), '| only the low untaken:', len(b_), 'MOC takes it', (b_.xL < b_.pmL).mean().round(3))

pr('=== T5  reverse cursed technique: does the NY PM continue the AM?')
X['amdir'] = np.sign(X.amC - X.O930); X['pmdir'] = np.sign(X.C1614 - X.pmO)
c = X[(X.amdir != 0) & (X.pmdir != 0)].copy(); c['cont'] = (c.amdir == c.pmdir).astype(float)
c['amstr'] = (c.amC - c.O930).abs() / (c.amH - c.amL)
pr('  PM (13:30 open -> 16:14 close) in the AM direction (09:30 -> 11:29)', c.cont.mean().round(3), 'n', len(c))
c['lunch_in'] = ((c.luH <= c.amH) & (c.luL >= c.amL)).astype(float)
pr('  lunch inside the AM range', c.lunch_in.mean().round(3), '| continuation when inside', c[c.lunch_in == 1].cont.mean().round(3), 'outside', c[c.lunch_in == 0].cont.mean().round(3))
pr('  by AM strength (|close-open| / AM range):', c.groupby(pd.cut(c.amstr, [0, .25, .5, .75, 1.01])).cont.mean().round(3).to_dict())
rows.append(check(c.assign(y0=c.cont - 0.5), 'y0 ~ 1', 'Intercept', test='T5 NY PM continues the AM direction (vs 50%)'))
rows.append(check(c, 'cont ~ amstr', 'amstr', test='T5 continuation vs AM trend strength'))
l = X.dropna(subset=['lu_up']).copy(); l = l[l.amdir != 0]; l['lu_cont'] = (np.sign(l.lu_up - 0.5) == l.amdir).astype(float)
pr('  lunch range broken first in the AM direction', l.lu_cont.mean().round(3), 'n', len(l))
rows.append(check(l.assign(y0=l.lu_cont - 0.5), 'y0 ~ 1', 'Intercept', test='T5 lunch range broken first in the AM direction (vs 50%)'))

pr('=== T6  NY AM pre-market range 08:30-09:29')
a = X.dropna(subset=['pre_up']).copy(); a['preR'] = a.preH - a.preL; a = a[a.preR > 2 * a.tick]
a['pos'] = ((a.pre_C929 - a.preL) / a.preR).clip(0, 1)
pr('  first break up', a.pre_up.mean().round(3), '| by 09:29 octant', a.groupby(pd.cut(a.pos, np.arange(0, 1.001, .125), include_lowest=True, labels=False)).pre_up.mean().round(3).to_dict())
rows.append(check(a.assign(c=a.pos - 0.5), 'pre_up ~ c', 'c', test='T6 pre-market range first break vs 09:29 position'))
a['hold'] = np.where(a.pre_up == 1, ~a.pre_loT, ~a.pre_hiT).astype(float)
pr('  first break held to 11:29', a.hold.mean().round(3), '| ARP -0.5 on the first-break side by 11:29', np.where(a.pre_up == 1, a.pre_arpU, a.pre_arpD).mean().round(3), '| both sides taken', (a.pre_hiT & a.pre_loT).mean().round(3))
print(table(rows)[cols].to_string())
