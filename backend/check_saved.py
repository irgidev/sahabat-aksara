import sys, cv2, numpy as np, glob, re
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

files = sorted(glob.glob('data_science/datasets/processed/*/stroke_*.png'))
print(f'Total saved images: {len(files)}')

from ai_core.scorers_v8 import _shape_integrity_check, score_v8

for f in files[-8:]:
    img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if img is None: continue
    px = int(np.sum(img > 127))
    pts = np.argwhere(img > 127)
    if len(pts) > 0:
        ys,xs = zip(*pts)
        bb_w = max(xs)-min(xs)+1; bb_h = max(ys)-min(ys)+1
    else:
        bb_w=bb_h=0
    
    parts = f.replace('\\','/').split('/')
    char = parts[-2]
    
    ic = _shape_integrity_check(img, char)
    s,d = score_v8(img,char)
    st = 3 if s>=70 else (2 if s>=45 else (1 if s>=20 else 0))
    r = d.get('reason','?')
    rej = ic['reject']
    print(f'  {char:>3s} px={px:>4d} bbox={bb_w:>2d}x{bb_h:<2d} | {s:>3.0f}% [{st}*] | reject={rej} reason={r}')
