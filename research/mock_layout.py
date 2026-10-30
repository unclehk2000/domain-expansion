"""Domain Expansion layout mock: the cards at their default places over a 1-minute chart, Desktop or Mobile layout, with the
Hollow Purple card's PLAN row. Values computed the way Domain_Expansion_Indicator.pine computes them.
python3 mock_layout.py OUTDIR SYM DAY 'HH:MM' desktop|mobile"""
import sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams['font.family'] = 'DejaVu Sans'
OUT, SYM, DAY, HM, MODE = sys.argv[1:6]
MOB = MODE == 'mobile'
NOW = pd.Timestamp(f'{DAY} {HM}')
BG, MU, GRID, CHT = '#ffffff', '#9aa1b2', '#eef1f6', '#000000'
UP, DN = '#089981', '#f23645'
HP = '#9c27b0'; FH = '#c47fd1'
CB, CT, CS = '#161a23', '#d1d4dc', '#8a93a6'          # the Dark card theme on a light chart (the user's setup)
TIERC = {3: '#ff6d00', 2: '#ffb300', 1: '#00acc1', 0: '#787b86'}
TIERN = {3: 'BOTH', 2: 'COILED', 1: 'CBDR', 0: 'NEITHER'}
HPU = [11.9, 19.4, 28.9, 44.0, 55.2, 67.0, 79.0, 88.9]; HPK = [0.5, 1.0, 1.5, 2.0]
HX = [30, 60, 90, 120, 140, 150]; HI = [4.910, 4.582, 4.222, 3.732, 3.232, 1.977]; HA, HB = 0.6714, -5.1575
lum = lambda h: 0.299 * int(h[1:3], 16) + 0.587 * int(h[3:5], 16) + 0.114 * int(h[5:7], 16)
hdrTx = lambda h: '#131722' if lum(h) > 165 else '#ffffff'
mix = lambda a, b, w: '#' + ''.join(f'{round(int(a[i:i + 2], 16) * w + int(b[i:i + 2], 16) * (1 - w)):02x}' for i in (1, 3, 5))
fmt = lambda v: f'{v:,.2f}'
pts = lambda v: f'{v:,.2f} pts'
hh = lambda t: f'{t:%H:%M}'
pct = lambda v: '—' if v is None else f'{round(v)}%'
sdTx = lambda v: (f'{v:.2f}'[:-1] if f'{v:.2f}'.endswith('0') else f'{v:.2f}') + ' SD'


def pPM(m, d):
    if m is None or d != d or m < 30 or m >= 165: return None
    if m >= 150:
        it = HI[5]; d = d / np.sqrt(max((165 - m) / 15, 0.01))
    else:
        i = 0
        while i < 4 and m >= HX[i + 1]: i += 1
        f = (m - HX[i]) / (HX[i + 1] - HX[i]); it = HI[i] * (1 - f) + HI[i + 1] * f
    dc = min(max(d, 0), 30); return 100 / (1 + np.exp(-(it + HA * dc + HB * np.sqrt(dc))))


# ── data
b = pd.read_pickle(f'/home/claude/kyw/bars_{SYM}_all.pkl'); b = b[(b.ts >= pd.Timestamp(DAY) - pd.Timedelta(days=4)) & (b.ts <= pd.Timestamp(DAY) + pd.Timedelta(hours=17))].set_index('ts')
q = b[['Open', 'High', 'Low', 'Close']].resample('15min').agg(dict(Open='first', High='max', Low='min', Close='last')).dropna()
tr = np.maximum(q.High - q.Low, np.maximum((q.High - q.Close.shift()).abs(), (q.Low - q.Close.shift()).abs()))
atr = pd.Series(tr.ewm(alpha=1 / 14, adjust=False).mean().values, index=q.index + pd.Timedelta(minutes=15))
d = b[(b.tday == DAY) & (b.index < NOW)]; at = lambda h1, h2: d[(d.hm >= h1) & (d.hm < h2)]
first = lambda m: m.index[m.values][0] if m.any() else None
tL = d.index[-1]; mN = tL.hour * 60 + tL.minute; px = d.Close.iloc[-1]
mins = (NOW - pd.Timestamp(f'{DAY} 13:30')).total_seconds() / 60

# ── Hollow Purple state
pm = at(1330, 1400); pH, pL = pm.High.max(), pm.Low.min(); R = pH - pL; pos = (pm.Close.iloc[-1] - pL) / R
up = HPU[min(7, int(np.floor(pos * 8)))]
a13 = atr.asof(pd.Timestamp(f'{DAY} 13:30'))
after = d[(d.index >= f'{DAY} 14:00') & (d.hm < 1615)]
hit_hi, hit_lo = first(after.High > pH), first(after.Low < pL)
brk_t = min([t for t in (hit_hi, hit_lo) if t is not None], default=None)
brk = 0 if brk_t is None else (1 if hit_hi == brk_t else -1)
oth = None
if brk:
    o = after[(after.index > brk_t)]; oth = first((o.Low < pL) if brk == 1 else (o.High > pH))
TU = [first(after.High >= pH + k * R) for k in HPK]; TD = [first(after.Low <= pL - k * R) for k in HPK]
fh = at(1500, 1550); fhH, fhL = fh.High.max(), fh.Low.min(); fR = fhH - fhL
fhSet = mN >= 950
if fhSet:
    o1550 = d.loc[f'{DAY} 15:50', 'Open']; fpos = min(max((o1550 - fhL) / fR, 0), 1); fup = 100 / (1 + np.exp(-(-3.133 + 6.277 * fpos)))
    moc = d[(d.index >= f'{DAY} 15:50') & (d.hm < 1615)]
    mH, mL = first(moc.High > fhH), first(moc.Low < fhL); aU, aD = first(moc.High >= fhH + 0.5 * fR), first(moc.Low <= fhL - 0.5 * fR)
inMOC = 950 <= mN < 960; inFH = 900 <= mN < 950; done = mN >= 975
sd = brk if brk else (1 if up >= 50 else -1); ar = '▲' if sd == 1 else '▼'
hits = TU if sd == 1 else TD
jN = next((j for j in range(4) if hits[j] is None), -1)
yN = None if jN < 0 else (pH + HPK[jN] * R if sd == 1 else pL - HPK[jN] * R)
nN = '' if jN < 0 else ('+' if sd == 1 else '−') + ('0.5 ARP' if jN == 0 else f'{HPK[jN]:g} SD')
pN = None if yN is None else pPM(mins, abs(yN - px) / a13)
plan = planM = planR = ''
if done:
    res = 'no break' if brk == 0 else ar + ' break ' + ('held' if oth is None else 'then both sides') + (' · ARP ✓' if jN != 0 else ' · ARP missed')
    plan = 'Done · ' + res
    planM = 'no break' if brk == 0 else ar + (' held' if oth is None else ' both') + (' · ARP ✓' if jN != 0 else ' · no ARP')
elif fhSet:
    if mH is None and mL is None:
        ms = 1 if fup >= 50 else -1
        plan = 'MOC: ' + (f'▲ final-hour high {fmt(fhH)}' if ms == 1 else f'▼ final-hour low {fmt(fhL)}') + ' first · ' + pts(abs((fhH if ms == 1 else fhL) - px))
        planM = 'MOC ' + (f'▲ {fmt(fhH)}' if ms == 1 else f'▼ {fmt(fhL)}'); planR = pct(fup if ms == 1 else 100 - fup)
    else:
        tk = (-1 if mH <= mL else 1) if (mH is not None and mL is not None) else (1 if mH is not None else -1)   # the side taken last
        yA = fhH + 0.5 * fR if tk == 1 else fhL - 0.5 * fR; tA = aU if tk == 1 else aD
        if tA is None:
            plan = 'MOC took the ' + ('high → ▲ ARP ' if tk == 1 else 'low → ▼ ARP ') + fmt(yA) + ' · ' + pts(abs(yA - px))
            planM = ('▲ ARP ' if tk == 1 else '▼ ARP ') + fmt(yA); planR = pct(pPM(mins, abs(yA - px) / a13))
        else:
            plan = 'MOC ' + ('▲' if tk == 1 else '▼') + ' ARP ✓ ' + hh(tA) + ' · no tested edge left'
            planM = ('▲' if tk == 1 else '▼') + ' ARP ✓ ' + hh(tA)
elif 940 <= mN < 950:
    plan = 'MOC macro at 15:50 · takes a final-hour side 72%'; planM = 'MOC 15:50'; planR = '72%' if MOB else ''
elif brk == 0:
    yE = pH if sd == 1 else pL
    plan = 'Wait for the break · ' + ('▲ PM high ' if sd == 1 else '▼ PM low ') + fmt(yE) + ' · ' + pts(abs(yE - px))
    planM = 'wait ' + ar + ' ' + fmt(yE); planR = ar + ' ' + pct(up if sd == 1 else 100 - up)
elif jN >= 0:
    plan = f'{ar} next {nN} {fmt(yN)} · {pts(abs(yN - px))}'
    planM = f"{ar} {'ARP' if jN == 0 else f'{HPK[jN]:g} SD'} {fmt(yN)}"; planR = pct(pN) + ('' if MOB else ' by 16:14')
else:
    plan = ar + ' every level reached · 2 SD ✓'; planM = ar + ' all ✓'
pill = 'DONE' if done else 'MOC' if inMOC else ((ar if MOB else ar + ' BREAK') if brk else 'WAIT')
rd = f"{'▲' if up >= 50 else '▼'} first {round(up if up >= 50 else 100 - up)}%"
HL = mix(HP, CB, 0.30)
hpRows = [('PLAN', planM if MOB else plan, planR, None, HL)]
if MOB:
    hpRows += [('READ', f'13:59 at {pos:.2f}', f"{'▲' if up >= 50 else '▼'} {round(up if up >= 50 else 100 - up)}%", None, None),
               ('BREAK', '—' if brk_t is None else ('▲ ' if brk == 1 else '▼ ') + hh(brk_t), '' if brk_t is None else ('held' if oth is None else 'both'), None if brk_t is None else HP, None)]
    if fhSet:
        mv = 'both' if (mH is not None and mL is not None) else f'▲ {hh(mH)}' if mH is not None else f'▼ {hh(mL)}' if mL is not None else '—'
        hpRows.append(('MOC', mv, 'ARP ✓' if (aU is not None or aD is not None) else '', None if mH is None and mL is None else HP, None))
else:
    adr = None
    hpRows += [('RANGE', f'{pts(R)}', '13:30–13:59', None, None), ('READ', f'13:59 close at {pos:.2f}', rd, None, None),
               ('BREAK', 'not broken yet' if brk_t is None else ('▲ ' if brk == 1 else '▼ ') + 'broke ' + hh(brk_t), '' if brk_t is None else ('held' if oth is None else 'both · ' + hh(oth)), None if brk_t is None else HP, None)]
    for j, k in enumerate(HPK):
        y = pH + k * R if sd == 1 else pL - k * R; t = hits[j]
        p = None if t is not None else pPM(mins, abs(y - px) / a13)
        kn = ('+' if sd == 1 else '−') + ('0.5 ARP' if j == 0 else f'{k:g} SD')
        hpRows.append((kn, fmt(y) + (f' · {pts(abs(y - px))}' if t is None and not done else ''), f'✓ {hh(t)}' if t is not None else (('not reached' if done else '—') if p is None else pct(p)), HP if t is not None else None, None))
    if mN >= 900:
        if inFH:
            fs_ = at(1500, 1550)
            hpRows.append(('FINAL HR', f'forming · {pts(fs_.High.max() - fs_.Low.min())}', 'set 15:50', None, None))
        elif fhSet:
            hpRows.append(('FINAL HR', f'{pts(fR)} · 15:50 at {fpos:.2f}', f"{'▲' if fup >= 50 else '▼'} first {round(fup if fup >= 50 else 100 - fup)}%", None, None))
            mv = 'both taken' if (mH is not None and mL is not None) else f'▲ high taken {hh(mH)}' if mH is not None else f'▼ low taken {hh(mL)}' if mL is not None else 'neither yet'
            hpRows.append(('MOC', mv, '15:50–16:00', None if mH is None and mL is None else HP, None))
            yU, yD = fhH + 0.5 * fR, fhL - 0.5 * fR
            wU = f'▲ ✓ {hh(aU)}' if aU is not None else '▲ ' + pct(pPM(mins, abs(yU - px) / a13))
            wD = f'▼ ✓ {hh(aD)}' if aD is not None else '▼ ' + pct(pPM(mins, abs(yD - px) / a13))
            hpRows.append(('ARP', f'▲ {fmt(yU)} · ▼ {fmt(yD)}', f'{wU} · {wD}', HP if (aU is not None or aD is not None) else None, None))
hpHead = ('◆' + (' PURPLE' if MOB else ' HOLLOW PURPLE'), ('' if MOB else 'NY PM · ') + hh(tL) + ('' if MOB else ' ET'), pill, HP)
FORMING = 810 <= mN < 840
if FORMING:
    plan = 'PM range forming · read at 14:00'; planM = 'read at 14:00'; planR = ''
    hpHead = ('◇' + (' PURPLE' if MOB else ' HOLLOW PURPLE'), ('' if MOB else 'NY PM · ') + hh(tL) + ('' if MOB else ' ET'), 'FORM' if MOB else 'FORMING', '#787b86')
    hpRows = [('PLAN', planM if MOB else plan, '', None, HL), ('RANGE', f'{pts(R)} so far', 'to 13:59', None, None)]

# ── London card (done for the day) and recent sessions, from the London study rows
L = pd.read_pickle('/home/claude/dx/lon_rows.pkl'); L = L[L.sym == SYM].copy()
L['tier'] = np.where((L.coil <= 0.2) & (L.cbR >= 5), 3, np.where(L.coil <= 0.2, 2, np.where(L.cbR >= 5, 1, 0)))
r = L[L.tday == pd.Timestamp(DAY)].iloc[0]; tier = int(r.tier); qc = TIERC[tier]
resV = 1 if (r.up >= 2 and r.up >= r.dn) else -1 if (r.dn >= 2 and r.dn > r.up) else 0
resSD = max(r.up, 0) if r.up >= r.dn else -r.dn
ny = d[(d.hm >= 500) & (d.hm < 1100)]; nyH, nyL = first(ny.High > r.lH), first(ny.Low < r.lL)
c7 = d[d.hm < 700].Close.iloc[-1]; rD = r.dH - r.dL
s7 = (c7 - r.dH) / rD if c7 > r.dH else -(r.dL - c7) / rD if c7 < r.dL else 0.0
ftRes = 'close inside the range' if s7 == 0 else 'close ' + sdTx(abs(s7)) + (' above' if s7 > 0 else ' below')
resTx = '▲ expansion' if resV == 1 else '▼ expansion' if resV == -1 else 'no expansion'
sdR = ('▲ ' if resSD >= 0 else '▼ ') + f'{abs(resSD):.1f} SD'
lonHead = (('✓' if resV else '✗') + (' DOMAIN' if MOB else ' DOMAIN EXPANSION'), ('LDN ' if MOB else 'LONDON DONE · ') + hh(tL) + ('' if MOB else ' ET'), TIERN[tier], qc)
if MOB:
    lonRows = [('RESULT', resTx, sdR, qc if resV else None, None),
               ('NY H / L', ('H ' + hh(nyH) if nyH is not None else 'H no') + ' · ' + ('L ' + hh(nyL) if nyL is not None else 'L no'), '', None if nyH is None and nyL is None else qc, None)]
else:
    lonRows = [('RESULT', resTx, sdR, qc if resV else None, None), ('RANGE', f'London {int(np.floor(r.lr + 0.5))} pts', f'{r.lr / r.adr:.2f} ADR', None, None),
               ('FOLLOW', ftRes, '07:00', None, None),
               ('NY HIGH', fmt(r.lH), 'taken ' + hh(nyH) if nyH is not None else 'not taken', qc if nyH is not None else None, None),
               ('NY LOW', fmt(r.lL), 'taken ' + hh(nyL) if nyL is not None else 'not taken', qc if nyL is not None else None, None)]
H = L[L.tday <= pd.Timestamp(DAY)].tail(10)
hres = [(1 if (x.up >= 2 and x.up >= x.dn) else -1 if (x.dn >= 2 and x.dn > x.up) else 0) for _, x in H.iterrows()]

# ── figure: a desktop pane, or a phone screen
if MOB:
    W, Hh, DPI, FS = 4.1, 8.6, 200, 7.6
    fig = plt.figure(figsize=(W, Hh), dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0.0, 0.16, 0.84, 0.74]); t0 = '13:15'
else:
    W, Hh, DPI, FS = 18, 10.4, 100, 8.2
    fig = plt.figure(figsize=(W, Hh), dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0.01, 0.05, 0.93, 0.86]); t0 = '12:45'
x = d[d.index >= f'{DAY} {t0}']; n = len(x)
for sp in ax.spines.values(): sp.set_visible(False)
ax.set_facecolor(BG); ax.yaxis.tick_right(); ax.tick_params(axis='y', colors=MU, labelsize=FS - 1); ax.tick_params(axis='x', length=0); ax.grid(color=GRID, lw=0.7, zorder=0)
ix = lambda t: float(np.searchsorted(x.index, t))
for i, (t, q_) in enumerate(x.iterrows()):
    c = UP if q_.Close >= q_.Open else DN
    ax.plot([i, i], [q_.Low, q_.High], color=c, lw=0.6 if MOB else 0.7, zorder=4)
    ax.add_patch(Rectangle((i - 0.33, min(q_.Open, q_.Close)), 0.66, max(abs(q_.Close - q_.Open), 0.25), fc=c, ec=c, lw=0.2, zorder=5))
xe = n - 1
LB = []                                          # chart labels: y, text, colour, group, where (Pine label styles)
lab = lambda y, t, c, g: LB.append(dict(y=y, t=t, c=c, g=g, va='center'))
i0, i14 = ix(pd.Timestamp(f'{DAY} 13:30')), ix(pd.Timestamp(f'{DAY} 14:00'))
if not FORMING:
    ax.add_patch(Rectangle((i0, pL), i14 - i0, R, fc=HP, alpha=0.12, ec='none', zorder=2))
    for y, t in ((pH, 'PM high'), (pL, 'PM low')):
        ax.plot([i0, xe], [y, y], color=HP, lw=1.1, zorder=3); lab(y, t, HP, 'hpE')
    ax.plot([i0, xe], [(pH + pL) / 2] * 2, color=HP, alpha=0.6, lw=1, ls=':', zorder=3); lab((pH + pL) / 2, 'PM CE', HP, 'hp')
    for k, w in zip(HPK, (2, 1, 1, 1)):
        for sg, base in ((1, pH), (-1, pL)):
            y = base + sg * k * R
            ax.plot([i14, xe], [y, y], color=HP, alpha=1 if k == 0.5 else 0.6, lw=w, ls='-' if k == 0.5 else ':', zorder=3); lab(y, ('+' if sg > 0 else '−') + ('0.5 ARP' if k == 0.5 else f'{k:g} SD'), HP, 'hp')
if mN >= 900:
    i15 = ix(pd.Timestamp(f'{DAY} 15:00'))
    fs_ = at(1500, 1550)
    for y, t in ((fs_.High.max(), 'Final-hour high'), (fs_.Low.min(), 'Final-hour low')):
        ax.plot([i15, xe], [y, y], color=FH, lw=1.1, zorder=3); lab(y, t + ('' if fhSet else ' (forming)'), FH, 'fh')
if fhSet:
    i1550 = ix(pd.Timestamp(f'{DAY} 15:50'))
    for y, t in ((fhH + 0.5 * fR, '+0.5 ARP · final hour'), (fhL - 0.5 * fR, '−0.5 ARP · final hour')):
        ax.plot([i1550, xe], [y, y], color=FH, lw=2, ls='--', zorder=3); lab(y, t, FH, 'fh')
    ax.axvspan(i1550 - 0.5, min(ix(pd.Timestamp(f'{DAY} 16:00')), n) - 0.5, color=HP, alpha=0.10, zorder=1)
    for a in [l_ for l_ in LB if l_['g'] in ('hp', 'hpE')]:     # awayFrom(): labels that meet move above / below their line
        for fl in [l_ for l_ in LB if l_['g'] == 'fh']:
            if abs(a['y'] - fl['y']) <= 0.15 * fR:
                fl['va'] = 'top' if fl['y'] < a['y'] else 'bottom'; a['va'] = 'top' if a['y'] < fl['y'] else 'bottom'
for l_ in LB:
    ax.text(xe + 1.5, l_['y'], l_['t'], color=l_['c'], fontsize=FS - 1.6, va=l_['va'], clip_on=True, zorder=7)
if brk_t is not None:
    bi = ix(brk_t); by = x.loc[brk_t, 'High'] if brk == 1 else x.loc[brk_t, 'Low']
    ax.annotate(f"{'▲' if brk == 1 else '▼'} PM break {hh(brk_t)} · ARP 74%", (bi, by), xytext=(0, 10 if brk == 1 else -10), textcoords='offset points', fontsize=FS - 1.6, ha='left' if (MOB or bi < 0.2 * n) else 'center', va='bottom' if brk == 1 else 'top', color=CHT, bbox=dict(fc=HP, alpha=0.15, ec='none', boxstyle='round,pad=0.3'), zorder=8)
step = 60 if MOB else 30
ticks = [i for i, t in enumerate(x.index) if (t.hour * 60 + t.minute) % step == 0]
ax.set_xticks(ticks); ax.set_xticklabels([hh(x.index[i]) for i in ticks], color=MU, fontsize=FS - 1)
lo = min(x.Low.min(), pL - (0.2 if FORMING else 2.1) * R); hi = max(x.High.max(), pH + (0.2 if FORMING else 2.1) * R)
if fhSet: lo, hi = min(lo, fhL - 0.6 * fR), max(hi, fhH + 0.6 * fR)
ax.set_xlim(-2, n / (0.50 if MOB else 0.58)); ax.set_ylim(lo - (hi - lo) * 0.03, hi + (hi - lo) * 0.03)
fig.canvas.draw()
bb = ax.get_window_extent()                     # the pane in pixels


def card(anchor, head, rows, frame, ncol=3, colw=None):
    """A Pine table: columns sized to their text, placed in a pane corner (6 px in)."""
    px_pt = DPI / 72; cw = 0.602 * FS * px_pt; lh = 1.85 * FS * px_pt; pad = 0.55 * cw * 2
    cells = [list(head[:ncol])] + [list(r_[:ncol]) for r_ in rows]
    ws = colw or [max(len(str(c[j])) for c in cells) * cw + pad for j in range(ncol)]
    Wt, Ht = sum(ws), lh * len(cells)
    xL = bb.x0 + 6 if 'left' in anchor else bb.x1 - 6 - Wt
    yT = bb.y1 - 6 if 'top' in anchor else bb.y0 + 6 + Ht
    T = fig.transFigure.inverted()
    def rect(x_, y_, w_, h_, **kw):
        (a0, b0), (a1, b1) = T.transform([(x_, y_), (x_ + w_, y_ + h_)])
        fig.patches.append(Rectangle((a0, b0), a1 - a0, b1 - b0, transform=fig.transFigure, **kw))
    def txt(x_, y_, s_, **kw):
        a0, b0 = T.transform((x_, y_)); fig.text(a0, b0, s_, family='DejaVu Sans Mono', fontsize=FS, va='center', zorder=12, **kw)
    return xL, yT, ws, lh, rect, txt, Wt, Ht


def draw_card(anchor, head, rows):
    title, sess, pill, col = head
    xL, yT, ws, lh, rect, txt, Wt, Ht = card(anchor, (title, sess, pill), rows, col)
    rect(xL, yT - lh, Wt, lh, fc=col, ec='none', zorder=10)
    txt(xL + 4, yT - lh / 2, title, color=hdrTx(col)); txt(xL + ws[0] + 4, yT - lh / 2, sess, color=hdrTx(col))
    rect(xL + ws[0] + ws[1], yT - lh, ws[2], lh, fc='#131722' if lum(col) > 165 else '#ffffff', ec='none', zorder=11)
    txt(xL + ws[0] + ws[1] + ws[2] / 2, yT - lh / 2, pill, color=col, ha='center')
    for i, (k, v, w, vc, bg) in enumerate(rows):
        yy = yT - lh * (i + 2)
        rect(xL, yy, Wt, lh, fc=bg or CB, ec='none', zorder=10)
        txt(xL + 4, yy + lh / 2, k, color=CT if bg else CS)
        txt(xL + ws[0] + 4, yy + lh / 2, v, color=CT if bg else (vc or CT))
        txt(xL + Wt - 4, yy + lh / 2, w, color=CT if bg else (vc or CT), ha='right')
    rect(xL, yT - Ht, Wt, Ht, fc='none', ec=mix(col, '#ffffff', 0.7), lw=1, zorder=12)
    return xL, yT - Ht, Wt, Ht


boxes = [('London', draw_card('top right', lonHead, lonRows)), ('Hollow Purple', draw_card('bottom right', hpHead, hpRows))]
if not MOB:
    hdr = ['day', 'tier', '05:00', 'furthest', 'range']
    body = [[f'{x_.tday:%a %d}', TIERN[int(x_.tier)], '▲ ✓' if rv == 1 else '▼ ✓' if rv == -1 else '✗', ('▲ ' if x_.up >= x_.dn else '▼ ') + f'{max(x_.up, x_.dn, 0):.1f} SD', f'{x_.lr:.0f} pts'] for (_, x_), rv in zip(H.iloc[::-1].iterrows(), hres[::-1])]
    allc = [['LONDON', 'last 10', '', '', f'{sum(v != 0 for v in hres)}/10 expanded'], hdr] + body
    px_pt = DPI / 72; cw = 0.602 * FS * px_pt; lh = 1.85 * FS * px_pt
    ws = [max(len(c[j]) for c in allc[1:]) * cw + 1.1 * cw for j in range(5)]
    ws[4] = max(ws[4], len(allc[0][4]) * cw + 1.1 * cw - 0)
    Wt, Ht = sum(ws), lh * len(allc); xL, yT = bb.x0 + 6, bb.y0 + 6 + Ht
    T = fig.transFigure.inverted()
    for i, row in enumerate(allc):
        yy = yT - lh * (i + 1)
        (a0, b0), (a1, b1) = T.transform([(xL, yy), (xL + Wt, yy + lh)])
        fig.patches.append(Rectangle((a0, b0), a1 - a0, b1 - b0, transform=fig.transFigure, fc='#5e35b1' if i == 0 else CB, ec='none', zorder=10))
        xx = xL
        for j, v in enumerate(row):
            if i == 0: colr = '#ffffff'
            elif i == 1: colr = CS
            else:
                tci = TIERC[int(H.iloc[::-1].iloc[i - 2].tier)]; rv = hres[::-1][i - 2]
                colr = tci if j == 1 else (tci if rv != 0 else CS) if j == 2 else CT
            a0, b0 = T.transform((xx + (4 if j == 0 else ws[j] - 4), yy + lh / 2))
            fig.text(a0, b0, v, color=colr, fontsize=FS, family='DejaVu Sans Mono', va='center', ha='left' if j == 0 else 'right', zorder=12)
            xx += ws[j]
    boxes.append(('Recent sessions', (xL, yT - Ht, Wt, Ht)))
# overlap check between the cards
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        (na_, (x1, y1, w1, h1)), (nb_, (x2, y2, w2, h2)) = boxes[i], boxes[j]
        ov = not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)
        print(f'{na_} vs {nb_}: {"OVERLAP" if ov else "clear"}', f'gap {max(y2 - (y1 + h1), y1 - (y2 + h2), x2 - (x1 + w1), x1 - (x2 + w2)):.0f} px')
for nm, (x1, y1, w1, h1) in boxes:
    print(f'{nm}: {w1:.0f} x {h1:.0f} px = {100 * w1 / bb.width:.0f}% of the pane width, {100 * h1 / bb.height:.0f}% of its height')
if MOB:
    fig.text(0.04, 0.965, f'{SYM}1! · 1m', color=CHT, fontsize=9, weight='bold'); fig.text(0.04, 0.94, f'Domain Expansion · Layout: Mobile · {NOW:%a %-d %b %H:%M} ET', color='#5d6476', fontsize=6.4)
    fig.text(0.04, 0.035, 'Mock-up from 1-minute data at phone size (≈ 410 × 860 pt). TradingView will differ.', color='#5d6476', fontsize=5.6)
else:
    fig.text(0.01, 0.955, f"Domain Expansion · default layout (Desktop) · {SYM} 1-minute, {NOW:%a %-d %b %Y %H:%M} ET", color=CHT, fontsize=13, weight='bold')
    fig.text(0.01, 0.928, 'London card top right · Hollow Purple bottom right, with the PLAN row on top · recent London sessions bottom left. Mock-up from 1-minute data; TradingView will differ.', color='#5d6476', fontsize=9)
f = f'{OUT}/Layout_{MODE}_{SYM}_{DAY}_{NOW:%H%M}.png'
plt.savefig(f, dpi=DPI, facecolor=BG); plt.close(fig); print('saved', f)
print('PLAN:', plan, '|', planM, '|', planR)
