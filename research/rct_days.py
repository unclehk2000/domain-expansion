"""Per-day table for the NY PM / market-on-close study. NQ, ES, RTY 1-minute 2018-26, ET.
Windows: AM 09:30-11:29, lunch 11:30-13:29, PM dealing range (PMDR) 13:30-13:59, final-hour dealing range (FHDR) 15:00-15:49,
MOC macro 15:50-15:59, MOC extended 15:50-16:14; NY AM pre-market range 08:30-09:29. A level is taken when a bar trades
beyond it (high > level or low < level); reached when a bar's range includes it. Writes days.pkl."""
import numpy as np, pandas as pd
rows = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['ts', 'Open', 'High', 'Low', 'Close', 'tday', 'hm', 'Contract']].reset_index(drop=True)
    O, H, L, C = (b[c].to_numpy() for c in ('Open', 'High', 'Low', 'Close'))
    hm = b.hm.to_numpy(); td = b.tday.to_numpy()
    tick = {'NQ': 0.25, 'ES': 0.25, 'RTY': 0.1}[sym]
    ds = np.r_[0, np.flatnonzero(td[1:] != td[:-1]) + 1]; de = np.r_[ds[1:], len(b)]
    drng = []
    for s, e in zip(ds, de):
        h = hm[s:e]
        idx = lambda a, z: np.flatnonzero((h >= a) & (h < z)) + s
        rth, am, lun, pm, fh, moc, mx, pre = (idx(930, 1615), idx(930, 1130), idx(1130, 1330), idx(1330, 1400), idx(1500, 1550),
                                             idx(1550, 1600), idx(1550, 1615), idx(830, 930))
        drng.append(H[s:e].max() - L[s:e].min())
        if len(rth) < 380 or len(fh) < 45 or len(moc) < 9 or len(pm) < 28 or len(am) < 110 or len(drng) < 21:
            continue
        r = dict(sym=sym, day=pd.Timestamp(td[s]), tick=tick, adr=np.mean(drng[-21:-1]), con=b.Contract.iat[s])
        a930 = rth[0]; b1550 = moc[0]
        pre50 = rth[rth < b1550]                                   # RTH 09:30 -> 15:49
        r.update(O930=O[a930], dH=H[pre50].max(), dL=L[pre50].min(), tdH=int(np.argmax(H[pre50])), tdL=int(np.argmin(L[pre50])), C1549=C[b1550 - 1], O1550=O[b1550])
        r.update(amH=H[am].max(), amL=L[am].min(), amC=C[am[-1]], luH=H[lun].max() if len(lun) else np.nan, luL=L[lun].min() if len(lun) else np.nan,
                 pmH=H[pm].max(), pmL=L[pm].min(), pmC=C[pm[-1]], pmO=O[pm[0]], fH=H[fh].max(), fL=L[fh].min(), fO=O[fh[0]],
                 tfH=int(np.argmax(H[fh])), tfL=int(np.argmin(L[fh])),
                 mH=H[moc].max(), mL=L[moc].min(), mC=C[moc[-1]], xH=H[mx].max(), xL=L[mx].min(), xC=C[mx[-1]],
                 tmH=int(np.argmax(H[moc])), tmL=int(np.argmin(L[moc])), txH=int(np.argmax(H[mx])), txL=int(np.argmin(L[mx])),
                 preH=H[pre].max() if len(pre) > 50 else np.nan, preL=L[pre].min() if len(pre) > 50 else np.nan)
        # 14:00 -> 15:49 (after the PM range) and the whole PM 13:30 -> 15:49
        p2 = np.flatnonzero((h >= 1400) & (h < 1550)) + s
        r.update(p2H=H[p2].max(), p2L=L[p2].min())
        # first touch order inside MOC (extended) of the FHDR high / low
        hiT = np.flatnonzero(H[mx] > r['fH']); loT = np.flatnonzero(L[mx] < r['fL'])
        r['mxHt'] = int(hiT[0]) if len(hiT) else -1; r['mxLt'] = int(loT[0]) if len(loT) else -1
        # equal highs / lows in the final hour: 3-bar swing points (1-minute) within a tolerance of the FHDR extreme
        hh, ll = H[fh], L[fh]
        sh = [i for i in range(1, len(fh) - 1) if hh[i] >= hh[i - 1] and hh[i] >= hh[i + 1]]
        sl = [i for i in range(1, len(fh) - 1) if ll[i] <= ll[i - 1] and ll[i] <= ll[i + 1]]
        R = r['fH'] - r['fL']
        for nm, pts, ext, sgn in (('eqH', sh, r['fH'], 1), ('eqL', sl, r['fL'], -1)):
            vals = (hh if sgn > 0 else ll)[pts] if pts else np.array([])
            for tol in (0.05, 0.10):
                r[f'{nm}{int(tol * 100)}'] = int((np.abs(vals - ext) <= tol * R).sum()) if R > 0 else 0
        # the 15:00 candle's upper / lower wick and later bodies inside it (the premium / discount wick idea)
        r.update(c15O=O[fh[0]], c15H=H[fh[0]], c15L=L[fh[0]], c15C=C[fh[0]])
        # RTH close
        r['C1614'] = C[rth[-1]]
        rows.append(r)
D = pd.DataFrame(rows); D['half'] = np.where(D.day.dt.year >= 2025, '25-26', '18-24')
D.to_pickle('/home/claude/rct/days.pkl'); print(D.shape, D.groupby('sym').size().to_dict())
