"""Rebuild ICT's market-on-close levels from the 1-minute data for the two lecture days."""
import pandas as pd, numpy as np
def day(sym, d):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl'); b = b[b.tday == d].set_index('ts')
    return b
for sym, d in (('NQ', '2026-08-03'), ('ES', '2026-08-04')):
    b = day(sym, d); hm = b.hm
    rth = b[(hm >= 930) & (hm < 1615)]
    print(f'\n===== {sym} {d} ({b.Contract.iloc[0]})')
    pre = rth[rth.index < f'{d} 15:50']
    H, L = pre.High.max(), pre.Low.min(); tH, tL = pre.High.idxmax(), pre.Low.idxmin()
    print(f'RTH 09:30→15:49  high {H} at {tH:%H:%M}   low {L} at {tL:%H:%M}   range {H-L}')
    D = H - L
    for k, nm in ((0.125, 'octant'), (0.1875, '16th (3/16)'), (0.25, 'quadrant'), (0.5, 'EQ')):
        print(f'   from the high: {nm:12s} {H - k*D:.2f}     from the low: {L + k*D:.2f}')
    pm = b[(hm >= 1330) & (hm < 1400)]; print(f'PM DR 13:30–13:59: high {pm.High.max()} low {pm.Low.min()}')
    pm2 = b[(hm >= 1330) & (b.index < f'{d} 15:50')]; print(f'13:30→15:49: high {pm2.High.max()} at {pm2.High.idxmax():%H:%M}, low {pm2.Low.min()} at {pm2.Low.idxmin():%H:%M}')
    fh = b[(hm >= 1500) & (hm < 1550)]; fH, fL = fh.High.max(), fh.Low.min(); fR = fH - fL
    print(f'Final-hour DR 15:00→15:49: high {fH} at {fh.High.idxmax():%H:%M}  low {fL} at {fh.Low.idxmin():%H:%M}  range {fR}')
    print(f'   ARP −0.5: below {fL - 0.5*fR:.3f}   above {fH + 0.5*fR:.3f}')
    moc = b[(hm >= 1550) & (hm < 1600)]; ext = b[(hm >= 1550) & (hm < 1615)]
    print(f'MOC 15:50–15:59: high {moc.High.max()} at {moc.High.idxmax():%H:%M}  low {moc.Low.min()} at {moc.Low.idxmin():%H:%M}  open {moc.Open.iloc[0]}  close {moc.Close.iloc[-1]}')
    print(f'15:50–16:14: high {ext.High.max()} low {ext.Low.min()} at {ext.Low.idxmin():%H:%M}')
    # PM dealing range: 13:30-onward low to the day's high (ES lecture), with −0.5 above
    pml = b[(hm >= 1330) & (b.index < f'{d} 15:00')].Low.min()
    print(f'PM low (13:30→14:59) {pml}; day high {H}; −0.5 above high {H + 0.5*(H-pml):.3f}; mid(high, that) {(H + H + 0.5*(H-pml))/2:.3f}')
    fh3 = b[(hm >= 1500) & (b.index < f'{d} 15:30')]
    print('15:00 bar:', b.loc[f'{d} 15:00', ['Open','High','Low','Close']].tolist())
