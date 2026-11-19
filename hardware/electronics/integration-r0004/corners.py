"""R0004 component networks and explicit behavioral boundaries. SI units throughout."""
from itertools import product


def metric(tag, operation, unit, low=None, high=None):
    return tag, operation, unit, low, high


def circuits():
    # A1 pair remains when A3 is unplugged. The sensor's bus-facing 10k is optional.
    for cap, rail, tol, sensor in product((100, 200), (3.0, 3.6), (.99, 1.01), (False, True)):
        resistance = 1500 * tol
        # Use the low-tolerance 10k at the strong-pull end, high at weak-pull end.
        sensor_r = (9500 if tol < 1 else 10500) if sensor else 1e12
        net = f"""Vstep src 0 pulse(0 {rail} 1u .1n .1n 10u 20u)
Rp src line {resistance}
Ra2 src line {sensor_r}
Cbus line 0 {cap}p
Vdd rail 0 {rail}
Rlow rail vol {resistance}
Ra2low rail vol {sensor_r}
Vclamp vol 0 .4"""
        trans = f'TRIG v(line) VAL={.3*rail} RISE=1 TARG v(line) VAL={.7*rail} RISE=1'
        yield f'i2c_{cap}p_{rail:g}v_{tol}_{int(sensor)}', net, '.tran 1n 4u', [
            metric('rise',trans,'s',0,300e-9),metric('sink','max i(Vclamp)','A',0,.003)]

    # Restoration of two independent receptacle-side returns after fixture identifies an open.
    for pin,rp,tol in product((1,2),(56000,22000,10000),(.99,1.01)):
        rd = 5100*tol
        net = f'Vbus v 0 5\nRhost v cc{pin} {rp}\nRcc1 cc1 0 {rd}\nRcc2 cc2 0 {rd}'
        bounds = {56000:(.2,.66),22000:(.66,1.23),10000:(1.23,2.04)}[rp]
        yield f'cc{pin}_{rp}_{tol}',net,'.tran 1u 5u',[
            metric('level',f'max v(cc{pin})','V',*bounds)]

    # Retain both original incremental current demand and regulator response waveforms.
    for name,cap,esr,lag,rise,step in [('typ',28,.035,5,5,.3),('derated',12,.08,12,8,.35)]:
        for initial in (3.201, 3.3):
            net = f"""Vref v 0 {initial}
Rref v rail 200
Resr rail c {esr}
Corig c 0 {cap}u
Radd rail cb .04
Cadd cb 0 30u
Iload rail 0 PWL(0 0 50u 0 50.1u {step} 250u {step})
Iloop 0 rail PWL(0 0 {50+lag}u 0 {50+lag+rise}u {step} 250u {step})"""
            yield f'rail_{name}_{initial:g}',net,'.tran .2u 200u 0 .2u',[
                metric('minimum','min v(rail)','V',3,3.6)]

    # No contact current from OEM buttons is diverted into the cell. Q2 mirrors the contact.
    for resistance,supply,variant in product((.2,10000,1e10),(3.0,4.2),(1,2)):
        gate_network = 'R37 g raw 1k\nR65 logic g 100k' if variant==2 else 'R37 g pwron 1k\nRg g 0 1T'
        net=f"""Vpack cell 0 {supply}
Vlogic logic 0 3.3
Rpull cell key 330k
Rcontact key 0 {resistance}
Mp driven key cell cell pmodel W=1u L=1u
Roff driven 0 100k
Mn raw driven 0 0 nmodel W=1u L=1u
.model pmodel PMOS(level=1 VTO=-1.5 KP=.05)
.model nmodel NMOS(level=1 VTO=1.5 KP=.05)
Rinternal logic pwron 50k
R38 pwron raw 510
{gate_network}"""
        bounds = (2.97,3.31) if resistance>1e9 else (0,.33)
        yield f'key_v{variant}_{resistance:g}_{supply:g}',net,'.tran 1u 10u',[
            metric('pwron','max v(pwron)','V',*bounds)]

    # Fixed differential pad also bounds non-sinusoidal full-scale program; worst power
    # vs arbitrary positive Rload occurs at Rload = net series resistance.
    for peak,load in [(1.4,6),(3.3,6),(3.9,5.4),(3.3,8),(3.6,8),(3.3,6.4),
                      (5.5,5.4),(5.5,6.4),(5.5,8),(5.5,2*4.99*.99)]:
        stimulus = f'SIN(0 {peak} 1k)' if peak<5.5 else '5.5'
        net=f"""Vdiff a 0 {stimulus}
Rpos a p {4.99*.99}
Rcoil p n {load}
Rneg n 0 {4.99*.99}
Ediff load 0 p n 1
Bpower diss 0 V=V(load)*V(load)/{load}
Bloss loss 0 V=V(a,p)*V(a,p)/{4.99*.99}"""
        specs=[metric('coil_w','avg v(diss) from=1m to=5m','W',0,.8),
               metric('series_w','avg v(loss) from=1m to=5m','W',0,1)]
        specs.append(metric('vrms','rms v(load) from=1m to=5m','V',0,2.52982) if load==8 else
                     metric('vrms','rms v(load) from=1m to=5m','V'))
        yield f'audio_{peak:g}_{load:g}',net,'.tran 2u 5m 0 2u',specs

    # Output power deficit of the upstream current throttle must be supplied by the pack.
    # Brequest is the unchanged historical VBUS-equivalent demand. Bpmu implements
    # the OEM voltage-regulation boundary; no silicon dynamics/efficiency inferred.
    for mode,src,loop,idle,peak in [('unconfigured',5,.25,.1,.33),('play',5,.25,.33,.5),
                                    ('lossy',4.75,.65,.33,.65),('suspend',5.25,.25,.1,.33),
                                    ('adapter',5.25,.25,.33,.65)]:
        for corner,threshold,ilim in [('low',4.36*.97,.2621),('high',4.36*1.03,.3423)]:
            if mode=='suspend':
                net='Vsrc raw 0 5.25\nRlim raw lamp 2673\nGled lamp 0 VALUE={MAX(0,V(lamp)-2.15)/10}\nIctrl raw 0 .00075\nBsource obs 0 V=-I(Vsrc)'
                yield f'usb_suspend_{corner}',net,'.tran 1u 5u',[metric('port','max v(obs)','A',0,.0025)]
                continue
            powerpath = ('Rweak raw pmic 55.44' if mode=='unconfigured' else
                         f'Bsw raw pmic I=MIN({ilim},MAX(0,V(raw,pmic)/.16))')
            net=f"""Vsrc src 0 {src}
Rcable src raw {loop}
Rlimit raw led 2673
Gled led 0 VALUE={{MAX(0,V(led)-2.15)/10}}
Ictrl raw 0 .00075
{powerpath}
Cout pmic 0 10u
Rleak pmic 0 100meg
.nodeset v(pmic)={threshold+.02} v(raw)={src-.1}
Vreq req 0 PULSE({idle} {peak} 1m 5u 5u 2m 9m)
Bpmu pmic 0 I=MIN(V(req),MAX(0,10*(V(pmic)-{threshold})))
Bsource obs 0 V=-I(Vsrc)
Bmissing deficit 0 V=MAX(0,V(req)-MIN(V(req),MAX(0,10*(V(pmic)-{threshold}))))"""
            yield f'usb_{mode}_{corner}',net,'.tran 2u 4m 0 2u',[
                metric('port','max v(obs)','A',0,.1 if mode=='unconfigured' else .5),
                metric('pmic_v','min v(pmic)','V',3.9,5.5),
                metric('missing_input','max v(deficit)','A equivalent')]

    # No charge-path interruption. The A1 load controls must suppress actual current before
    # a low pack can enter a high-power state. Include 150 mA unshed residual at the weak pack.
    for name,ocv,dcr,peak in [('fresh',4.15,.15,.65),('mid',3.70,.25,.65),('aged',3.40,.55,.72)]:
        for sense in ('low','high'):
            # TLV3012B equivalent: trip limits include reference/offset/divider/hysteresis guard.
            # Use a stateful hysteretic switch, with a rising and falling threshold.
            rising,falling = (3.56,3.41) if sense=='low' else (3.67,3.51)
            net = f"""Vcell cell 0 {ocv}
Rpath cell j7 {dcr}
Cj7 j7 0 2.2u
Rbulk j7 bulk .020
Cbulk bulk 0 330u
Iresidual j7 0 .15
Vrequest req 0 PULSE(0 {peak-.15} 1m 2u 2u 2m 8m)
Vvalid ref 0 1
Spermit ref enable j7 0 uv
.model uv SW(Ron=.01 Roff=1T Vt={(rising+falling)/2} Vh={(rising-falling)/2})
Rbias enable 0 10k
Bswitched j7 0 I=V(req)*V(enable)
Ben active 0 V=V(enable)"""
            yield f'bat_{name}_{sense}',net,'.tran 5u 4m 0 2u',[
                metric('j7_v','min v(j7)','V',3.3,4.23),
                metric('request','max v(req)','A incremental'),
                metric('permit','max v(active)','logic',0,.001) if name=='aged' else
                metric('permit','max v(active)','logic')]

    # Both historical USB line fixtures after inserting the port detector, including
    # a conservative 6.9 ohms per leg and an assumed 8 pF/leg of die + routing.
    for cap,route in product((10,100), ("native","recovery")):
        driver_r = 33 if route=="native" else 44  # 23+10 on A1 or assumed 17+27 on FTDI
        detector_r = 6.9 if route=="native" else .001
        net=f"""Vp p 0 PULSE(0 3.3 20n 7n 7n 82n 200n)
Vn n 0 PULSE(3.3 0 20n 7n 7n 82n 200n)
Rp p pp {driver_r}
Rn n nn {driver_r}
Rsp pp mp {detector_r}
Rmuxp mp ps 6
Rsn nn mn {detector_r}
Rmuxn mn ns 6
Csp ps 0 {15.5 if route=="native" else 7.5}p
Csn ns 0 {15.5 if route=="native" else 7.5}p
Tp ps 0 dp 0 Z0=45 TD=5n
Tn ns 0 dm 0 Z0=45 TD=5n
Cp dp 0 {cap}p
Cn dm 0 {cap}p
Rdp dp 0 15k
Rdm dm 0 15k"""
        yield f'usbdata_{route}_{cap}p',net,'.tran .1n 100n 0 .1n',[
            metric('high','find v(dp) at=100n','V',2,3.6),
            metric('rise','trig v(dp) val=.33 rise=1 targ v(dp) val=2.97 rise=1','s',4e-9,20e-9)]

        if route=='native' and cap==100:
            old=net.replace('Rp p pp 33','Rp p pp 45').replace('Rn n nn 33','Rn n nn 45')
            yield 'diagnostic_mux_old_termination',old,'.tran .1n 100n 0 .1n',[
                metric('rise','trig v(dp) val=.33 rise=1 targ v(dp) val=2.97 rise=1','s',4e-9,20e-9)]

    # No supplementary source in these deliberately unsheddable controls. The resistor
    # draws the historical requested current at the old 3.9 V minimum VBUS input.
    # Force an authorized-to-default transition as the device loses its USB grant.
    for title, weak, src, cable, requested in [('no_cell_default',True,5,.25,.33),
                                              ('no_cell_configured',False,4.75,.65,.65),
                                              ('no_cell_grant_loss',False,5,.25,.33)]:
        control = 'PULSE(1 0 1m 1u 1u 10m 20m)' if title.endswith('loss') else ('0' if weak else '1')
        net=f"""Vusb source 0 {src}
Rloop source raw {cable}
Vmode mode 0 {control}
Bflow raw pmic I=MAX(0,MIN(1,V(mode))*MIN(.3423,V(raw,pmic)/.16)+(1-MIN(1,V(mode)))*V(raw,pmic)/55.44)
Cin pmic 0 10u
Rrequest pmic 0 {3.9/requested}
Iaux raw 0 .00075
Rled raw lamp 2673
Gled lamp 0 VALUE={{MAX(0,V(lamp)-2.15)/10}}
Bport obs 0 V=-I(Vusb)"""
        yield 'diagnostic_'+title,net,'.tran 2u 5m 0 2u',[
            metric('pmic_v','min v(pmic) from=2m to=5m','V',3.9,5.5),
            metric('port','max v(obs) from=2m to=5m','A',0,.1 if weak or title.endswith('loss') else .5)]

    # Gross output short after the entry devices, with both grants high during handover.
    # Directly bound both branches and the worst downstream short of the blue LED.
    for mode, enabled in [('default_short',False),('overlap_short',True)]:
        net=f"""Vsrc raw 0 5.25
Rweak raw 0 55.44
Bstrong raw 0 I={.3423 if enabled else 0}
Rblue raw 0 2673
Ictrl raw 0 .00075
Bport obs 0 V=-I(Vsrc)"""
        yield 'usb_'+mode,net,'.tran 1u 5u',[
            metric('port','max v(obs)','A',0,.5 if enabled else .1)]

    # 
    # Initialized running at the lower specified trip threshold: incremental step applied
    # while the board has the maximum allowed 50 us to remove the switched demand.
    for threshold in (3.41,3.51):
        net=f"""Vcell cell 0 {threshold+.15*.55}
Rpath cell j7 .55
Corig j7 0 2.2u
Rbulk j7 bulk .020
Cbulk bulk 0 330u
Iidle j7 0 .15
Itransient j7 0 PWL(0 0 1m 0 1.002m .57 1.052m .57 1.054m 0 4m 0)"""
        yield f'bat_trip_delay_{threshold:g}',net,'.tran .2u 4m 0 .2u',[
            metric('j7_v','min v(j7)','V',3.3,4.23)]

    # Original 500 mA combined play and charge request with the R0003 lamp now counted.
    net="""Vsrc source 0 5
Rloop source raw .25
Cb raw 0 10u
Iload raw 0 PULSE(.33 .5 1m 5u 5u 2m 9m)
Rlim raw lamp 2700
Gblue lamp 0 VALUE={MAX(0,V(lamp)-2.8)/10}
Bport obs 0 V=-I(Vsrc)"""
    yield 'diagnostic_previous_play_with_lamp',net,'.tran 2u 4m 0 2u',[
        metric('port','max v(obs)','A',0,.5)]

    # Recovery bridge is bus-powered before grant. PWREN# enables the target domain
    # only after configuration. Model ramped enable and maintain the ROM-only load
    # within its assigned limit. Sustained overload diagnostics above remain required.
    for name,src,loop,limit in [('low',4.75,.65,.2621),('high',5.25,.25,.3423)]:
        net=f"""Vsrc src 0 {src}
Rcable src raw {loop}
Rblue raw lamp 2673
Gblue lamp 0 VALUE={{MAX(0,V(lamp)-2.15)/10}}
Ilogic raw 0 .00075
Ibridge raw 0 PWL(0 .012 9m .012 9.05m .00025 15m .00025)
Vgrant grant 0 PWL(0 0 2m 0 2.5m 1 8m 1 8.002m 0 15m 0)
Binput raw pmic I=V(grant)*MAX(0,MIN({limit},V(raw,pmic)/.16))
Ctarget pmic 0 10u
Roff pmic 0 100k
Vload load 0 PWL(0 0 3.5m 0 3.6m .20 8m .20 8.01m 0 15m 0)
Brom pmic 0 I=V(load)*MIN(1,MAX(0,V(pmic)/3.9))
Bport obs 0 V=-I(Vsrc)
Bpower romw 0 V=V(pmic)*V(load)"""
        yield 'recovery_nocell_'+name,net,'.tran 2u 14m 0 2u',[
            metric('pregrant_i','max v(obs) from=.1m to=1.99m','A',0,.1),
            metric('target_off','max v(pmic) from=.1m to=1.99m','V',0,.1),
            metric('bridge_v','min v(raw) from=.1m to=14m','V',2.97,5.5),
            metric('grant_i','max v(obs) from=2m to=8m','A',0,.5),
            metric('recovery_v','min v(pmic) from=3.6m to=7.99m','V',3.9,5.5),
            metric('rom_power','min v(romw) from=3.6m to=7.99m','W',.78,1.1),
            metric('revoked_i','max v(obs) from=8.01m to=8.99m','A',0,.1),
            metric('suspend_i','max v(obs) from=10m to=14m','A',0,.0025)]
