import sys, cv2, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from ai_core.scorers_v8 import score_v8, RULES

def mk(char):
    a=np.zeros((64,64),dtype=np.uint8)
    if char=='A': cv2.line(a,(32,6),(12,54),255,3);cv2.line(a,(32,6),(52,54),255,3);cv2.line(a,(16,32),(48,32),255,3)
    elif char=='B': cv2.line(a,(18,6),(18,54),255,3);cv2.ellipse(a,(33,20),(14,14),0,-180,180,255,3);cv2.ellipse(a,(33,40),(14,14),0,-180,180,255,3)
    elif char=='C': cv2.ellipse(a,(32,30),(18,22),0,60,300,255,7)
    elif char=='D': cv2.line(a,(18,6),(18,54),255,3);cv2.ellipse(a,(32,30),(15,24),0,-90,90,255,4)
    elif char=='E': cv2.line(a,(20,6),(20,54),255,3);cv2.line(a,(20,6),(50,6),255,3);cv2.line(a,(20,30),(45,30),255,3);cv2.line(a,(20,54),(50,54),255,3)
    elif char=='F': cv2.line(a,(20,6),(20,54),255,3);cv2.line(a,(20,6),(50,6),255,3);cv2.line(a,(20,30),(45,30),255,3)
    elif char=='G': cv2.ellipse(a,(32,30),(18,22),0,40,320,255,4);cv2.line(a,(32,30),(48,30),255,3)
    elif char=='H': cv2.line(a,(16,6),(16,54),255,3);cv2.line(a,(48,6),(48,54),255,3);cv2.line(a,(16,30),(48,30),255,3)
    elif char=='I': cv2.line(a,(32,6),(32,54),255,3);cv2.line(a,(22,6),(42,6),255,3);cv2.line(a,(22,54),(42,54),255,3)
    elif char=='J': cv2.line(a,(22,6),(46,6),255,3);cv2.line(a,(38,10),(38,44),255,3);cv2.line(a,(26,44),(38,44),255,3)
    elif char=='K': cv2.line(a,(20,6),(20,54),255,3);cv2.line(a,(21,30),(48,6),255,3);cv2.line(a,(21,30),(48,54),255,3)
    elif char=='L': cv2.line(a,(20,6),(20,54),255,3);cv2.line(a,(20,54),(50,54),255,3)
    elif char=='M': cv2.line(a,(10,54),(10,6),255,3);cv2.line(a,(10,6),(25,54),255,3);cv2.line(a,(25,6),(39,54),255,3);cv2.line(a,(39,6),(54,54),255,3)
    elif char=='N': cv2.line(a,(14,54),(14,6),255,3);cv2.line(a,(14,6),(50,54),255,3);cv2.line(a,(50,6),(50,54),255,3)
    elif char=='O': cv2.circle(a,(32,30),20,255,3)
    elif char=='P': cv2.line(a,(18,6),(18,54),255,3);cv2.ellipse(a,(33,18),(14,12),0,-180,180,255,3)
    elif char=='Q': cv2.circle(a,(32,30),20,255,3);cv2.line(a,(40,40),(52,54),255,3)
    elif char=='R': cv2.line(a,(18,6),(18,54),255,3);cv2.ellipse(a,(33,18),(14,12),0,-180,180,255,3);cv2.line(a,(25,30),(50,54),255,3)
    elif char=='S': cv2.ellipse(a,(28,20),(14,12),0,0,360,255,3);cv2.ellipse(a,(36,42),(14,12),0,0,360,255,3);cv2.line(a,(20,26),(34,26),255,3);cv2.line(a,(30,38),(46,38),255,3)
    elif char=='T': cv2.line(a,(32,6),(32,54),255,3);cv2.line(a,(12,6),(52,6),255,3)
    elif char=='U': cv2.line(a,(14,6),(14,44),255,3);cv2.line(a,(50,6),(50,44),255,3);cv2.ellipse(a,(32,44),(18,12),0,180,0,255,3)
    elif char=='V': cv2.line(a,(10,6),(32,56),255,3);cv2.line(a,(54,6),(32,56),255,3)
    elif char=='W': cv2.line(a,(6,6),(20,54),255,3);cv2.line(a,(20,6),(32,54),255,3);cv2.line(a,(32,6),(44,54),255,3);cv2.line(a,(44,6),(58,54),255,3)
    elif char=='X': cv2.line(a,(10,6),(54,54),255,3);cv2.line(a,(54,6),(10,54),255,3)
    elif char=='Y': cv2.line(a,(10,6),(32,32),255,3);cv2.line(a,(54,6),(32,32),255,3);cv2.line(a,(32,32),(32,54),255,3)
    elif char=='Z': cv2.line(a,(10,6),(54,6),255,3);cv2.line(a,(54,6),(10,54),255,3);cv2.line(a,(10,54),(54,54),255,3)
    elif char=='a': cv2.circle(a,(26,38),12,255,3);cv2.line(a,(38,38),(48,38),255,3)
    elif char=='b': cv2.line(a,(16,6),(16,54),255,3);cv2.circle(a,(32,38),14,255,3)
    elif char=='c': cv2.ellipse(a,(32,36),(14,14),0,30,330,255,3)
    elif char=='d': cv2.line(a,(48,6),(48,54),255,3);cv2.circle(a,(32,38),14,255,3)
    elif char=='e': cv2.circle(a,(32,36),14,255,3);cv2.line(a,(24,36),(40,36),255,3)
    elif char=='l': cv2.line(a,(30,10),(30,54),255,3)
    elif char=='m': cv2.line(a,(8,54),(8,34),255,3);cv2.ellipse(a,(18,44),(9,11),0,180,360,255,3);cv2.ellipse(a,(32,44),(9,11),0,180,360,255,3);cv2.line(a,(42,34),(42,54),255,3)
    elif char=='n': cv2.line(a,(10,54),(10,34),255,3);cv2.ellipse(a,(24,44),(10,12),0,180,360,255,3);cv2.line(a,(36,34),(36,54),255,3)
    elif char=='o': cv2.circle(a,(32,36),14,255,3)
    elif char=='p': cv2.line(a,(16,16),(16,54),255,3);cv2.circle(a,(32,36),14,255,3)
    elif char=='r': cv2.line(a,(12,36),(12,54),255,3);cv2.ellipse(a,(24,44),(10,11),0,180,360,255,3);cv2.line(a,(30,34),(36,54),255,3)
    elif char=='t': cv2.line(a,(30,12),(30,54),255,3);cv2.line(a,(18,12),(44,12),255,3)
    elif char=='u': cv2.line(a,(14,14),(14,48),255,3);cv2.line(a,(46,14),(46,48),255,3);cv2.ellipse(a,(30,48),(16,10),0,180,0,255,3)
    elif char=='v': cv2.line(a,(10,14),(32,56),255,3);cv2.line(a,(54,14),(32,56),255,3)
    elif char=='w': cv2.line(a,(6,14),(20,56),255,3);cv2.line(a,(20,14),(32,52),255,3);cv2.line(a,(32,14),(44,52),255,3);cv2.line(a,(44,14),(58,56),255,3)
    elif char=='x': cv2.line(a,(10,14),(54,56),255,3);cv2.line(a,(54,14),(10,56),255,3)
    elif char=='y': cv2.line(a,(8,14),(32,42),255,3);cv2.line(a,(56,14),(32,42),255,3);cv2.line(a,(32,42),(26,58),255,3)
    elif char=='z': cv2.line(a,(10,14),(54,14),255,3);cv2.line(a,(54,14),(12,56),255,3);cv2.line(a,(12,56),(54,56),255,3)
    elif char=='0': cv2.circle(a,(32,30),20,255,3)
    elif char=='1': cv2.line(a,(28,6),(28,54),255,3);cv2.line(a,(28,6),(38,14),255,3)
    elif char=='2': cv2.line(a,(10,6),(50,6),255,3);cv2.line(a,(50,6),(14,30),255,3);cv2.line(a,(14,30),(50,30),255,3);cv2.line(a,(50,30),(50,54),255,3);cv2.line(a,(10,54),(50,54),255,3)
    elif char=='3': cv2.ellipse(a,(32,18),(14,10),0,200,340,255,3);cv2.ellipse(a,(32,40),(14,10),0,160,380,255,3)
    elif char=='4': cv2.line(a,(44,6),(44,54),255,3);cv2.line(a,(10,30),(44,30),255,3);cv2.line(a,(10,6),(10,30),255,3)
    elif char=='5': cv2.line(a,(10,6),(46,6),255,3);cv2.line(a,(10,6),(10,28),255,3);cv2.line(a,(10,28),(42,28),255,3);cv2.ellipse(a,(32,44),(12,10),0,180,360,255,3)
    elif char=='6': cv2.ellipse(a,(28,34),(16,18),0,80,400,255,3);cv2.line(a,(12,22),(28,22),255,3)
    elif char=='7': cv2.line(a,(10,6),(54,6),255,3);cv2.line(a,(38,6),(14,54),255,3)
    elif char=='8': cv2.circle(a,(32,20),12,255,3);cv2.circle(a,(32,42),12,255,3)
    elif char=='9': cv2.circle(a,(32,20),14,255,3);cv2.line(a,(32,34),(46,54),255,3)
    return a

def dot2():
    d=np.zeros((64,64),dtype=np.uint8)
    cv2.circle(d,(32,32),4,255,-1)
    return d

def line2():
    l=np.zeros((64,64),dtype=np.uint8)
    cv2.line(l,(8,32),(56,32),255,4)
    return l

print('=== CORRECT SHAPES (must be 2-3*) ===')
ok=0; fail=0
for char in sorted(RULES.keys()):
    s,d = score_v8(mk(char),char)
    st = 3 if s>=70 else (2 if s>=45 else (1 if s>=20 else 0))
    if st>=2: ok+=1
    else: fail+=1
    m = 'OK' if st>=2 else 'FAIL'
    print(f'  {m} {char:>3s} {s:>5.0f}% [{st}*]')

print(f'\n=== RESULT: {ok}/41 correct, {fail} failed ===')

print('\n=== REJECTION TESTS ===')
dot_f=0; line_f=0
for char in sorted(RULES.keys()):
    s,_ = score_v8(dot2(),char)
    if s>=20: dot_f+=1
    s2,_ = score_v8(line2(),char)
    if char not in ['I','l','1'] and s2>=20: line_f+=1
print(f'Dot  -> 0*: {41-dot_f}/41  ({dot_f} wrong)')
print(f'Line -> 0*: {37-line_f}/37  ({line_f} wrong)')
