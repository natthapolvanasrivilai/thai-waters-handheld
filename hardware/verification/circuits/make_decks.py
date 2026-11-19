"""Emit standalone ASCII SPICE decks and the explicit case/metric definitions.
Units in every deck are SPICE SI. Numeric corner values are deliberate engineering
assumptions unless identified as schematic, firmware or supplier values.
"""
from pathlib import Path
import json, math
ROOT = Path(__file__).resolve().parent
DECKS = ROOT / 'decks'
DECKS.mkdir(exist_ok=True)
cases = []

def metric(label, column, calculation, unit, limits=None, **kw):
    return dict(label=label,column=column,calculation=calculation,unit=unit,limits=limits,**kw)

def case(id, family, description, source, model, net, analysis, outputs, metrics):
    p=DECKS/(id+'.cir')
    p.write_text('\n'.join([f'Thai Waters Rev F | {id}', '* '+description, '* Model: '+model,
                            *net, analysis,'.PRINT TRAN '+' '.join(outputs),'.END','']),encoding='ascii')
    cases.append(dict(id=id,family=family,description=description,sources=source,model=model,
                      deck='decks/'+p.name,outputs=outputs,metrics=metrics))

# Each released open-drain line is an RC step; the separate clamped duplicate
# measures aggregate pull-up demand at VOL=0.4 V without assuming a slave RDS(on).
for name,r,c in [('encoder_only',10000,100),('encoder_motor',5000,100),('additional_4k7',1/(1/4700+1/5000),100),
                 ('loaded_200pf',1/(1/4700+1/5000),200),('excess_pullups',820,100)]:
    case('i2c_'+name,'Shared I2C','Effective pull-up %.0f ohm and %s pF at J8.'%(r,c),
         ['A1','A2','A3','UM10204','FW'],'Lumped released edge; board population, MOS level shifters and actual capacitance must be measured.',
         ['Vrelease drv 0 DC 0 PULSE(0 3.3 1u 1n 1n 30u 60u)',f'Rpull drv bus {r:.6f}',f'Cbus bus 0 {c}p',
          'Vdd rail 0 3.3',f'Rparallel rail sink {r:.6f}','Vclamp sink 0 0.4'],
         '.TRAN 5n 8u 0 5n',['V(bus)','I(Vclamp)'],
         [metric('30-70% rise','V(bus)','rise','ns',[0,300],low=.99,high=2.31,scale=1e9),
          metric('Static sink demand at 0.4 V','I(Vclamp)','last','mA',[0,3],scale=1000)])
# Source port plus complete cable/connector DCR. Current is a stress fixture,
# not enumeration approval, and the full-board PMIC input limiter is not modeled.
for name,v,r,idle,peak in [('play_charge',5,.25,.33,.50),('low_host_lossy',4.75,.65,.33,.65),('unconfigured_host',5,.25,.10,.33)]:
    case('usb_'+name,'USB power','%.2f V host, %.2f ohm loop; %.0f to %.0f mA.'%(v,r,idle*1000,peak*1000),
         ['A1','AXP','USB2','FW'],'Cable, connector, bead resistance and VBUS input capacitance; ideal imposed USB load.',
         [f'Vhost src 0 {v}',f'Rloop src vbus {r}','Cin vbus 0 10u',f'Iload vbus 0 PULSE({idle} {peak} 1m 5u 5u 2m 9m)'],
         '.TRAN 10u 4m 0 5u',['V(vbus)','I(Vhost)'],
         [metric('Minimum PMIC input','V(vbus)','min','V',[3.9,5.5]),
          metric('Source demand','I(Vhost)','absmax','mA',[0,100 if name=='unconfigured_host' else 500],scale=1000)])
for name,rp,rd in [('default',56000,5100),('1p5a',22000,5100),('3a',10000,5100),('cc_open',56000,1e10)]:
    case('cc_'+name,'Type-C orientation','5 V resistor-source fixture, Rp %.0f ohm, Rd %.0f ohm.'%(rp,rd),
         ['A1','TYPEC'],'One active CC pin. Repeat both plug orientations. Open resistance is a deliberate assembly fault.',
         ['Vr src 0 5',f'Rhost src cc {rp}',f'Rdevice cc 0 {rd}'],'.TRAN 1u 5u',['V(cc)'],
         [metric('CC voltage','V(cc)','last','V',{'default':[.20,.66],'1p5a':[.66,1.23],'3a':[1.23,2.04],'cc_open':[.20,.66]}[name])])
for name,v,r,peak in [('fresh',4.15,.15,.65),('mid',3.7,.25,.65),('low_aged',3.40,.55,.72)]:
    case('bat_'+name,'Protected pack path','OCV %.2f V, combined cell/protector/loom %.2f ohm, %.0f mA peak.'%(v,r,peak*1000),
         ['A1','B1','BOARD'],'Cell plus protection + splices reduced to series resistance. J7 voltage is upstream of the PMIC.',
         [f'Vcell cell 0 {v}',f'Rdc cell j7 {r}','Cj7 j7 0 2.2u',f'Iload j7 0 PULSE(.15 {peak} 1m 2u 2u 2m 8m)'],
         '.TRAN 10u 4m 0 5u',['V(j7)'],
         [metric('Minimum J7 voltage','V(j7)','min','V',[3.30,4.23])])
# During initial regulation latency the output capacitor alone supplies the
# incremental demand; response-source slow ramp refills load. Post-recovery
# regulation and switching-loop stability are outside this bound.
for name,cap,esr,lag,rise,di in [('typ_assumed',28,.035,5,5,.30),('derated_slow',12,.08,12,8,.35)]:
    onset=50
    case('rail_'+name,'3.3 V regulation','%.0f uF effective, ESR %.3f ohm, %.0f us latency, %.0f us response.'%(cap,esr,lag,rise),
         ['A1','ESP','BOARD'],'Incremental charge-deficit bound prior to loop recovery around 3.30 V. Wi-Fi current step is assumed.',
         ['Vref v 0 3.3','Rslow v rail 200',f'Resr rail cap {esr}',f'Ceff cap 0 {cap}u',
          f'Iload rail 0 PWL(0 0 {onset}u 0 {onset+.1}u {di} 250u {di})',
          f'Iloop 0 rail PWL(0 0 {onset+lag}u 0 {onset+lag+rise}u {di} 250u {di})'],
         '.TRAN .2u 200u 0 .2u',['V(rail)'],
         [metric('Minimum 3V3 at step','V(rail)','min','V',[3,3.6])])
for name,rs,c in [('nominal',10000,100),('slow',10500,120),('fast',9500,80)]:
    case('reset_'+name,'Reset and touch','R14/C19 ESP_EN and R11/C8 LCD_RST nominal 10 kohm/100 nF; %d ohm, %d nF.'%(rs,c),
         ['A1','ESP','FW'],'Passive high transition after switch or expander release. Firmware LCD reset hold and bus boot are bench items.',
         ['Vdd src 0 DC 0 PULSE(0 3.3 1u 1n 1n 10m 20m)',f'Rpull src reset {rs}',f'Creset reset 0 {c}n'],
         '.TRAN 5u 4m 0 5u',['V(reset)'],
         [metric('Release to 75% of VDD','V(reset)','cross','ms',[.05,10],level=2.475,origin=1e-6,scale=1e3)])
for name,on,r in [('pressed',True,.2),('released',False,1e10),('high_contact',True,10000)]:
    case('key_'+name,'Top power key','K3-2 and SW1 to K3-1/GND; switch loop %.1f ohm.'%r,['A1','SW1','FW'],
         'Rev 2 R38=510 ohm, R37=1k, R65=100k. PMIC internal pull represented by an assumed 50k to 3.3 V; CMOS bounds are design targets.',
         ['Vdd v 0 3.3','Rinternal v pwron 50k','R38 pwron raw 510','R65 v g 100k','R37 g raw 1k',
          f'Rkey raw 0 {r}','Cloom raw 0 100p'],'.TRAN 1u 10u',['V(pwron)','V(raw)'],
         [metric('PMIC PWRON steady','V(pwron)','last','V',[0,.33] if on else [2.97,3.31])])
for name,supply,ocv in [('cc_low',5,3.30),('cv_knee',5,4.185),('taper',5,4.199)]:
    case('charge_'+name,'Charge control','%.3f V equivalent cell OCV and 100 mOhm cell resistance.'%ocv,['A1','AXP','B1','FW'],
         'Ideal 300 mA / 4.2 V charge law with 0.10 ohm CV slope. Demonstrates programmed boundaries; excludes device accuracy, precharge, termination and autonomous POR.',
         [f'Vcell ocv 0 {ocv}','Rcell bat ocv 0.1','Vsense source bat 0',
          '* x=(4.2-Vbat)/0.1, positive-voltage error over these cases only.',
          'Gcc 0 source VALUE={0.5*(0.3+(4.2-V(bat))/0.1-ABS(0.3-(4.2-V(bat))/0.1))}'],
         '.TRAN 1u 10u',['V(bat)','I(Vsense)'],
         [metric('Cell terminal','V(bat)','last','V',[0,4.20]),metric('Pack charge current','I(Vsense)','last','mA',[0,500],scale=1000)])
for name,power,rth,ambient in [('vented_assumption',.22,55,25),('sealed_stress',.55,85,40)]:
    case('thermal_'+name,'Charger and enclosure heat','%.2f W heat source, %.0f K/W path and %.0f C ambient.'%(power,rth,ambient),
         ['A1','AXP','B1','BOARD'],'Electrothermal analogy 1 V = 1 C, 1 A = 1 W. Aggregate heat and thermal resistance are assumed; result is a hot-node sensitivity only.',
         [f'Vamb amb 0 {ambient}',f'Rth hot amb {rth}','Cth hot 0 8',f'Iheat 0 hot PULSE(0 {power} 1 1 1 18000 36000)'],
         '.TRAN 12 7200 0 10',['V(hot)'],[metric('Modeled hot node after soak','V(hot)','last','C',None)])
for name,res in [('board_25C',10000),('board_45C',4924),('open',1e8),('short',1)]:
    case('ts_'+name,'Battery-temperature input','TS source set to 50 uA; R29 represented by %.0f ohm.'%res,['A1','AXP','B1'],
         'AXP TS divider with 3.3 V source compliance, conceptual linearized saturation. R29 sits on the board; cell temperature is unobservable through the two-wire J7.',
         ['Iexcite 0 ts 50u',f'R29 ts 0 {res}','Vdd v 0 3.3','Dclamp ts v ideal','.MODEL ideal D(IS=1e-8 N=0.05)'],
         '.TRAN 1u 10u',['V(ts)'],[metric('TS input','V(ts)','last','V',None)])
for name,amp,r in [('cue',1.4,6),('near_rating',3.3,6),('overdrive',3.9,5.4)]:
    case('speaker_'+name,'BTL audio output','Differential %.2f V peak sine at 1 kHz into %.1f ohms.'%(amp,r),['A1','SP1','FW'],
         'Voltage envelope applied differentially to J9. A resistive load bounds the nominal sine heating; excludes PA gain, clipping, PWM, resonance and acoustic SPL.',
         ['Vcm cm 0 2.1',f'Vone plus cm SIN(0 {amp/2} 1000)',f'Vtwo cm minus SIN(0 {amp/2} 1000)',f'Rcoil plus minus {r}','Ediff diff 0 plus minus 1'],
         '.TRAN 5u 4m 0 5u',['V(diff)'],[metric('Speaker average real power','V(diff)','resistive_power','W',[0,1],resistance=r,start=.001)])
for name,r,l,drive in [('running_equivalent',50,.6,3),('low_R_start',22,.3,3),('locked_stress',15,.2,3)]:
    case('erm_'+name,'Haptic H-bridge load','%.1f ohm, %.1f mH, %.1f V differential command.'%(r,l,drive),['A3','M1','DRV','FW'],
         'Electrical RL/envelope surrogate. 50 ohm is effective running load at 3 V/60 mA, not measured winding DCR; low R represents an uncertain starting/stall stress.',
         [f'Vdrive drv 0 DC 0 PULSE(0 {drive} 1m 5u 5u 6m 20m)',f'Lmotor drv series {l}m',f'Rmotor series 0 {r}'],
         '.TRAN 5u 9m 0 5u',['I(Vdrive)'],[metric('Peak drive current','I(Vdrive)','absmax','mA',None,scale=1000)])
for name,vf,rail,r in [('nominal',2.95,3.3,6.8),('low_vf_high_rail',2.8,3.4,6.46)]:
    case('light_'+name,'LCD backlight','%.2f V rail, %.2f V LED drop with %.2f ohm series R3.'%(rail,vf,r),['A1','BOARD'],
         'Full-duty steady slice of R3 + aggregate panel LED drop and AO3400 on resistance. Actual Vf, current limit and thermal rating require the panel drawing.',
         [f'Vdd v 0 {rail}',f'R3 v led {r}',f'Vled led sw {vf}','Ron sw 0 .08'],'.TRAN 1u 10u',['I(Vdd)'],
         [metric('Full-duty backlight current','I(Vdd)','absmax','mA',None,scale=1000)])
for name,c in [('nominal',10),('heavy_fixture',100)]:
    case('usbdata_'+name,'USB full-speed edges','45 ohm lines, 5 ns delay; assumed 23 ohm transceiver plus R18/R19=22 ohm; %d pF load/leg.'%c,['A1','USB2','ESP'],
         'One complementary driven bit edge, ideal lossless cable and aggregate load. Excludes stubs, ESD nonlinearity, layout, jitter, USB attach and eye mask.',
         ['Vp p 0 DC 0 PULSE(0 3.3 20n 7n 7n 82n 200n)','Vn n 0 DC 3.3 PULSE(3.3 0 20n 7n 7n 82n 200n)',
          'Rp p ps 45','Rn n ns 45','Tp ps 0 dp 0 Z0=45 TD=5n','Tn ns 0 dm 0 Z0=45 TD=5n',
          f'Cp dp 0 {c}p',f'Cn dm 0 {c}p','Rdp dp 0 15k','Rdm dm 0 15k','Ediff diff 0 dp dm 1'],
         '.TRAN .25n 100n 0 .25n',['V(dp)','V(diff)'],[metric('Data+ last high','V(dp)','last','V',[2,3.6]),
         metric('Data+ 10-90% rise','V(dp)','rise','ns',[4,20],low=.33,high=2.97,scale=1e9)])
(ROOT/'cases.json').write_text(json.dumps(cases,indent=2)+'\n',encoding='utf-8')
print(f'{len(cases)} decks generated')
