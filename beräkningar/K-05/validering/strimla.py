import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Nedböjning för en strimla: plattmodellen (cylindrisk böjning) mot 1D-integration med samma tvärsnittssamband
import numpy as np, math
from platta import Platta
from ec2 import Betong, Stal, Armering, Lager, styvhet_effektiv
from analys import nedbojning
b=Betong(); s=Stal(); h=150
phi=b.kryptal(150); ecs=b.krympning(150)
def strip1d(L,q,arm,shr=True,beta=0.5,full=False):
    xs=np.linspace(0,L,801); M=q*xs*(L-xs)/2
    lag=[(arm.ux.As,arm.ux.y),(arm.ox.As,arm.ox.y)]
    k=[]
    for m in M:
        EI,kc,z=styvhet_effektiv(m if not full else 1e12,h,lag,b,s,phi,ecs if shr else 0,beta if not full else 0)
        k.append(m/EI+kc)
    k=np.array(k); mbar=np.where(xs<=L/2,xs/2,(L-xs)/2)
    return np.trapezoid(k*mbar,xs)
for L,arm in [(3000,Armering(150,Lager(8,200,150-25-4),Lager(8,250,150-25-12),Lager(6,1e6,30),Lager(6,1e6,30))),
              (4000,Armering(150,Lager(10,150,150-20-5),Lager(10,150,150-30-5),Lager(6,150,48),Lager(6,150,54)))]:
    q=(3.75+1.2+0.3*2)/1000
    W=600
    P=Platta([(0,0),(L,0),(L,W),(0,W)],hmax=100)
    for i,(x,y) in enumerate(P.xy):
        if abs(y)<1e-6 or abs(y-W)<1e-6: P.fixed[3*i+2]=0
    P.stod_linje("v",[(0,0),(0,W)]); P.stod_linje("h",[(L,0),(L,W)])
    f=P.last_yta(q)
    for shr in (False,True):
        r=nedbojning(P,f,arm,b,s,phi,ecs if shr else 0)
        print(f"L={L} krymp={shr}: FE {r.w_at(L/2,W/2):6.2f} mm ({r.iter} it)  1D {strip1d(L,q,arm,shr):6.2f} mm")
    r=nedbojning(P,f,arm,b,s,phi,0,fullt_sprucken=True)
    print(f"   fullt sprucken utan krymp: FE {r.w_at(L/2,W/2):6.2f}  1D {strip1d(L,q,arm,False,full=True):6.2f}")
