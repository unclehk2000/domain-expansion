"""Order-dependent fields for the NY PM study (adds to days.pkl -> days2.pkl):
 - PM dealing range 13:30-13:59: first break after 14:00 (side, minute), the other side taken by 16:14, its +-0.5 ARP reached
   (and on which side) by 15:49 / 16:14, taken inside the MOC macro;
 - NY AM pre-market range 08:30-09:29: first break in 09:30-11:29, the other side, its ARP reached by 11:29;
 - lunch range 11:30-13:29: first break in 13:30-16:14;
 - daily-range retracement in the MOC: the MOC extended low (high-side days) / high (low-side days) in daily-range units."""
import numpy as np, pandas as pd
D = pd.read_pickle('/home/claude/rct/days.pkl')
out = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['High', 'Low', 'Close', 'tday', 'hm']].reset_index(drop=True)
    H, L, C, hm, td = b.High.to_numpy(), b.Low.to_numpy(), b.Close.to_numpy(), b.hm.to_numpy(), b.tday.to_numpy()
    ds = np.r_[0, np.flatnonzero(td[1:] != td[:-1]) + 1]; de = np.r_[ds[1:], len(b)]
    pos = {pd.Timestamp(td[s]): (s, e) for s, e in zip(ds, de)}
    for r in D[D.sym == sym].itertuples():
        s, e = pos[r.day]; h = hm[s:e]
        w = lambda a, z: np.flatnonzero((h >= a) & (h < z)) + s
        o = dict(sym=sym, day=r.day)
        def first_break(win, hiL, loL):
            hi = np.flatnonzero(H[win] > hiL); lo = np.flatnonzero(L[win] < loL)
            a = hi[0] if len(hi) else 10 ** 9; z = lo[0] if len(lo) else 10 ** 9
            if a == z:
                return (np.nan if a == 10 ** 9 else 0.5), (np.nan if a == 10 ** 9 else a), bool(len(hi)), bool(len(lo))
            return float(a < z), min(a, z), bool(len(hi)), bool(len(lo))
        # PM dealing range
        R = r.pmH - r.pmL
        for tag, win in (('1549', w(1400, 1550)), ('1614', w(1400, 1615))):
            up, t, th, tl = first_break(win, r.pmH, r.pmL)
            o[f'pm_up_{tag}'], o[f'pm_t_{tag}'], o[f'pm_hiT_{tag}'], o[f'pm_loT_{tag}'] = up, t, th, tl
            o[f'pm_arpU_{tag}'] = bool((H[win] >= r.pmH + 0.5 * R).any()); o[f'pm_arpD_{tag}'] = bool((L[win] <= r.pmL - 0.5 * R).any())
            for k in (1.0, 1.5, 2.0):
                o[f'pm_sd{k}U_{tag}'] = bool((H[win] >= r.pmH + k * R).any()); o[f'pm_sd{k}D_{tag}'] = bool((L[win] <= r.pmL - k * R).any())
        moc = w(1550, 1600)
        o['pm_hi_moc'] = bool((H[moc] > r.pmH).any()); o['pm_lo_moc'] = bool((L[moc] < r.pmL).any())
        # NY AM pre-market range
        if r.preH == r.preH:
            Rp = r.preH - r.preL; am = w(930, 1130)
            up, t, th, tl = first_break(am, r.preH, r.preL)
            o.update(pre_up=up, pre_t=t, pre_hiT=th, pre_loT=tl, pre_arpU=bool((H[am] >= r.preH + 0.5 * Rp).any()), pre_arpD=bool((L[am] <= r.preL - 0.5 * Rp).any()),
                     pre_C929=C[w(830, 930)[-1]])
        # lunch range break in the PM
        if r.luH == r.luH:
            up, t, th, tl = first_break(w(1330, 1615), r.luH, r.luL)
            o.update(lu_up=up, lu_t=t, lu_hiT=th, lu_loT=tl)
        out.append(o)
X = D.merge(pd.DataFrame(out), on=['sym', 'day'])
X.to_pickle('/home/claude/rct/days2.pkl'); print(X.shape)
