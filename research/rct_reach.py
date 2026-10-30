"""Same-afternoon reach model for NY PM levels: from checkpoints 14:00 / 14:30 / 15:00 / 15:30 / 15:50 / 16:00, the odds a level
not yet traded since 13:30 trades by 16:14, from its distance to price (unit: ATR15 at 13:30, RMA-14 of 15-minute true
ranges; or ADR20) and the time left. Levels: PM dealing range high / low, its +-0.5 / 1 / 1.5 / 2 SD, the final-hour range
high / low and its +-0.5 ARP (from 15:50), the day's octant / 16th / quadrant from each RTH extreme (as of the checkpoint).
Fit 2018-24, score 2025-26; level-type dummies tested."""
import sys, json, numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
cols = ['coef', 'p', 'n', '18-24', 'p_18-24', '25-26', 'p_25-26', 'ES', 'NQ', 'RTY', 'ok']
X = pd.read_pickle('/home/claude/rct/days2.pkl')
CKS = [1400, 1430, 1500, 1530, 1550, 1600]
rows = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['ts', 'Open', 'High', 'Low', 'Close', 'tday', 'hm']].reset_index(drop=True)
    q = b.set_index('ts')[['Open', 'High', 'Low', 'Close']].resample('15min').agg(dict(Open='first', High='max', Low='min', Close='last')).dropna()
    tr = np.maximum(q.High - q.Low, np.maximum((q.High - q.Close.shift()).abs(), (q.Low - q.Close.shift()).abs()))
    atr = pd.Series(tr.ewm(alpha=1 / 14, adjust=False).mean().values, index=q.index + pd.Timedelta(minutes=15))
    O, H, L, Cc, hm, td, ts = (b[c].to_numpy() for c in ('Open', 'High', 'Low', 'Close', 'hm', 'tday', 'ts'))
    ds = np.r_[0, np.flatnonzero(td[1:] != td[:-1]) + 1]; de = np.r_[ds[1:], len(b)]
    pos = {pd.Timestamp(td[s]): (s, e) for s, e in zip(ds, de)}
    for r in X[X.sym == sym].itertuples():
        s, e = pos[r.day]; h = hm[s:e]
        w = np.flatnonzero((h >= 1330) & (h < 1615)) + s
        if len(w) < 160: continue
        t1330 = pd.Timestamp(ts[w[0]]); a15 = atr.asof(t1330)
        hh, ll, cc, hmw = H[w], L[w], Cc[w], hm[w]
        rth = np.flatnonzero((h >= 930) & (h < 1615)) + s
        R = r.pmH - r.pmL; Rf = r.fH - r.fL
        for ck in CKS:
            j = np.flatnonzero(hmw == ck)
            if not len(j): continue
            j = j[0]; px = cc[j - 1]
            upto = rth[rth < w[j]]; dH, dL = H[upto].max(), L[upto].min(); Dd = dH - dL
            lv = []
            if ck >= 1400:
                lv += [('pm_edge', r.pmH), ('pm_edge', r.pmL)] + [(f'pm_sd', r.pmH + k * R) for k in (0.5, 1, 1.5, 2)] + [(f'pm_sd', r.pmL - k * R) for k in (0.5, 1, 1.5, 2)]
            if ck >= 1550:
                lv += [('fh_edge', r.fH), ('fh_edge', r.fL), ('fh_arp', r.fH + 0.5 * Rf), ('fh_arp', r.fL - 0.5 * Rf)]
            lv += [('day_lvl', dH - k * Dd) for k in (0.125, 0.1875, 0.25)] + [('day_lvl', dL + k * Dd) for k in (0.125, 0.1875, 0.25)]
            for kind, y in lv:
                if ((ll[:j] <= y) & (hh[:j] >= y)).any(): continue          # traded since 13:30
                hit = ((ll[j:] <= y) & (hh[j:] >= y)).any()
                rows.append(dict(sym=sym, day=r.day, ck=ck, kind=kind, y=float(hit), d=abs(y - px), atr15=a15, adr=r.adr))
K = pd.DataFrame(rows); K['half'] = np.where(K.day.dt.year >= 2025, '25-26', '18-24'); K['date'] = K.day; K = K.set_index('date')
K = K.dropna(subset=['atr15']); K['dA'] = (K.d / K.atr15).clip(0, 30); K['dD'] = (K.d / K.adr).clip(0, 3); K['ckf'] = K.ck.astype(str)
K.to_pickle('/home/claude/rct/reach.pkl')
print(K.shape, K.groupby('kind').y.mean().round(3).to_dict())
tr_, te = K[K.half == '18-24'], K[K.half == '25-26'].copy()
for f in ('y ~ C(ckf)', 'y ~ dA + np.sqrt(dA) + C(ckf)', 'y ~ dD + np.sqrt(dD) + C(ckf)', 'y ~ dA + np.sqrt(dA) + C(ckf) + C(kind)'):
    m = smf.logit(f, tr_).fit(disp=0); te['p'] = m.predict(te); print(f'{f:42s} OOS Brier {np.mean((te.p - te.y) ** 2):.4f}')
m = smf.logit('y ~ dA + np.sqrt(dA) + C(ckf)', tr_).fit(disp=0); te['p'] = m.predict(te)
te['dec'] = pd.qcut(te.p.rank(method='first'), 8, labels=False); print(te.groupby('dec').agg(pred=('p', 'mean'), obs=('y', 'mean')).round(3).T.to_string())
K['sq'] = np.sqrt(K.dA)
rr = [check(K, 'y ~ dA + sq + C(ckf)', 'dA', test='reach by 16:14 | distance (ATR15)')]
for kd in ('pm_sd', 'fh_edge', 'fh_arp', 'day_lvl'):
    rr.append(check(K.assign(isk=(K.kind == kd).astype(float)), 'y ~ dA + sq + C(ckf) + isk', 'isk', test=f'{kd} vs other levels, same distance'))
print(table(rr)[cols].to_string())
mf = smf.logit('y ~ dA + sq + C(ckf)', K).fit(disp=0); p = mf.params
out = dict(ck=CKS, ints=[p['Intercept'] + p.get(f'C(ckf)[T.{c}]', 0.0) for c in map(str, CKS)], a=p['dA'], b=p['sq'])
json.dump(out, open('/home/claude/rct/reach_coef.json', 'w'), indent=1); print({k: (np.round(v, 3).tolist() if isinstance(v, list) else round(v, 4)) for k, v in out.items()})
