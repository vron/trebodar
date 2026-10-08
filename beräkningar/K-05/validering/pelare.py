import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Oändlig platta på kvadratiskt pelarnät, en panel med symmetrivillkor. Timoshenko & Woinowsky-Krieger tabell 89 (ν=0,2):
# w_mitt = 0,00581 qa⁴/D, mx_mitt = 0,0331 qa²
import numpy as np
from platta import Platta, Dmat
a=3000.; q=0.01; E=30000; h=150; nu=0.2; D=E*h**3/12/(1-nu**2)
for hmax in (200,100,50):
    P=Platta([(0,0),(a,0),(a,a),(0,a)],hmax=hmax, finare=[(0,0,300,hmax/4),(a,0,300,hmax/4),(a,a,300,hmax/4),(0,a,300,hmax/4)])
    for i,(x,y) in enumerate(P.xy):
        if abs(x)<1e-6 or abs(x-a)<1e-6: P.fixed[3*i+1]=0
        if abs(y)<1e-6 or abs(y-a)<1e-6: P.fixed[3*i+2]=0
    for c in [(0,0),(a,0),(a,a),(0,a)]: P.stod_punkt(str(c),*c)
    P.styvhet(Dmat(D,nu)); r=P.los(P.last_yta(q))
    R=r.reaktioner()
    print(f"h={hmax} ne={P.ne} w={r.w_at(a/2,a/2)/(q*a**4/D):.5f} (0,00581) mx_mitt={r.m(a/2,a/2)[0]/(q*a*a):.4f} (0,0331) "
          f"mx(a/2,0)={r.m(a/2,1)[0]/(q*a*a):.4f}  my(a/2,0)={r.m(a/2,1)[1]/(q*a*a):.4f} sumR/qa²={sum(R.values())/(q*a*a)*4:.3f}")
