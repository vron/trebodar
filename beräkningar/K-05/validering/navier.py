import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, time
from platta import Platta, Dmat, wood_armer
a=4000.; q=0.01; E=30000; h=150; nu=0.3
D=E*h**3/12/(1-nu**2)
for hmax in (400,200,100,50):
    t0=time.time()
    P=Platta([(0,0),(a,0),(a,a),(0,a)],hmax=hmax)
    P.stod_linje("rand",[(0,0),(a,0),(a,a),(0,a),(0,0)])
    P.styvhet(Dmat(D,nu))
    r=P.los(P.last_yta(q))
    wc=r.w_at(a/2,a/2); m=r.m(a/2,a/2)
    # corner twisting moment and total reaction
    mxy_c = r.m(a-1,a-1)[2]
    print(f"h={hmax:4.0f} ne={P.ne:6d} w/(qa4/D)={wc/(q*a**4/D):.5f} (0.00406)  mx/(qa2)={m[0]/(q*a*a):.4f} (0.0479) mxy_hörn={mxy_c/(q*a*a):.4f} (0.0325) R={sum(r.reaktioner().values())/(q*a*a):.4f}  {time.time()-t0:.1f}s")
