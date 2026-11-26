"""Pure geometry screen; never promote a fabricated article from this result."""
from math import dist, hypot
import argparse,json

def screen(bore_a,bore_b,screw_a,screw_b,offset_a,offset_b,fixed_a=None,fixed_b=None):
    if min(bore_a,bore_b,screw_a,screw_b)<=0:
        raise ValueError('diameters must be positive')
    ra,rb=(bore_a-screw_a)/2,(bore_b-screw_b)/2
    delta=dist(offset_a,offset_b)
    result={'radial_clearance_a_mm':ra,'radial_clearance_b_mm':rb,
            'measured_relative_center_error_mm':delta,'free_translation_margin_mm':ra+rb-delta,
            'can_fit_with_free_translation_only':min(ra,rb)>0 and delta<ra+rb}
    if fixed_a is not None and fixed_b is not None:
        ma,mb=ra-hypot(*fixed_a),rb-hypot(*fixed_b)
        result.update(constrained_margin_a_mm=ma,constrained_margin_b_mm=mb,
                      constrained_fit_screen=min(ma,mb)>1e-9)
    return result

def controls():
    f=lambda a,b,oa,ob:screen(a,b,2,2,oa,ob,oa,ob)
    d={
      'nominal':f(2.3,2.3,(0,0),(0,0)),
      'relative_error_near_nominal_limit':f(2.3,2.3,(0,0),(.29,0)),
      'relative_error_over_limit':f(2.3,2.3,(0,0),(.31,0)),
      'same_shift_does_not_guarantee_constrained_fit':f(2.3,2.3,(.20,0),(.20,0)),
      'native_witness_does_not_clear_m2':f(1.70,1.70,(0,0),(0,0)),
      'nonuniform_bores':f(2.12,2.24,(-.02,0),(.10,0))}
    assert d['nominal']['constrained_fit_screen']
    assert d['relative_error_near_nominal_limit']['can_fit_with_free_translation_only']
    assert not d['relative_error_near_nominal_limit']['constrained_fit_screen']
    assert not d['relative_error_over_limit']['can_fit_with_free_translation_only']
    assert d['same_shift_does_not_guarantee_constrained_fit']['can_fit_with_free_translation_only']
    assert not d['same_shift_does_not_guarantee_constrained_fit']['constrained_fit_screen']
    assert not d['native_witness_does_not_clear_m2']['can_fit_with_free_translation_only']
    assert d['nonuniform_bores']['constrained_fit_screen']
    return d

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--diameters',nargs=4,type=float,metavar=('BORE_A','BORE_B','SCREW_A','SCREW_B'))
    ap.add_argument('--residuals',nargs=4,type=float,metavar=('DX_A','DY_A','DX_B','DY_B'))
    opts=ap.parse_args()
    if bool(opts.diameters)!=bool(opts.residuals):
        ap.error('diameters and residuals must be supplied together')
    if opts.diameters:
        p=tuple(opts.residuals[:2]);q=tuple(opts.residuals[2:])
        obj=screen(*opts.diameters,p,q,p,q)
    else:
        obj=controls()
    print(json.dumps(obj,indent=2))
