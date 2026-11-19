"""Build the portable engineering review. Paths refer to the private repository or named exports."""
import argparse, base64, csv, gzip, hashlib, importlib.util, json, zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
CIR=REPO/'hardware/verification/circuits'
FIT=REPO/'hardware/mechanical/rev-F'
REVIEW=FIT/'review'
BUY=REPO/'sourcing/production-intent'

def readjson(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def b64(data):return base64.b64encode(data).decode('ascii')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def picture(p):return 'data:image/png;base64,'+b64(p.read_bytes())
def compress_series(points, intervals=100):
    if len(points)<intervals*2:return points
    picked={0,len(points)-1}
    for j in range(intervals):
        group=range(len(points)*j//intervals,len(points)*(j+1)//intervals)
        picked.add(min(group,key=lambda i:points[i][1]))
        picked.add(max(group,key=lambda i:points[i][1]))
    return [points[i] for i in sorted(picked)]

def build(out):
    circuit=readjson(CIR/'results.json'); sc=readjson(BUY/'commercial-summary.json')
    cover=readjson(REVIEW/'placement-results.json'); parts=readjson(REVIEW/'parts.json')
    full=next(v for v in sc['scenarios'] if v['sku']=='FULL' and v['lot']==100)
    fit=readjson(FIT/'checks.json'); grip=readjson(FIT/'rod-grip-checks.json')
    src=readjson(CIR/'sources.json')
    src_data=[[k+' · '+v['title'],v['url']] for k,v in src.items() if v.get('url','').startswith('https://')]
    sim_runner=importlib.util.spec_from_file_location('circuit_run',CIR/'run.py')
    parser=importlib.util.module_from_spec(sim_runner);sim_runner.loader.exec_module(parser)
    traces={}
    with zipfile.ZipFile(CIR/'raw-ngspice.zip') as raw:
        for case in readjson(CIR/'cases.json'):
            outputs=parser.series(raw.read(case['id']+'.log').decode(errors='replace'),case['outputs'])
            traces[case['id']]=[dict(name=name,unit='A' if name.startswith('i(') else 'V',points=compress_series(v)) for name,v in outputs.items()]
    tests=readcsv(HERE/'verification-matrix.csv')
    gated=[r for r in cover['intersections'] if r['status']=='resolve']
    baseline=next(r for r in cover['cell_tests'] if r['rotation_deg']==0 and r['dx_mm']==0 and r['dy_mm']==0)
    nominal_hit=next(v['mm3'] for v in baseline['intersections'] if v['part']=='Housing')
    tested=[next((v['mm3'] for v in r['intersections'] if v['part']=='Housing'),0) for r in cover['cell_tests']]
    data=dict(circuits=circuit,traces=traces,commercial=sc,bom=readcsv(BUY/'rev-f-buy-make-bom.csv'),nre=readcsv(BUY/'nre-allowances.csv'),collisions=cover['intersections'],validation=tests,
              routing=readcsv(HERE/'factory-routing.csv'),arch=readcsv(HERE/'architecture.csv'),risks=readcsv(HERE/'risk-register.csv'),markets=readcsv(HERE/'market-access.csv'),blankRecord=(HERE/'as-built-record.csv').read_text(encoding='utf-8-sig'),
              hero=picture(out/'Thai-Waters-Rev-F-grip.png'),sectionImage=picture(FIT/'CAD/grip-interface-inspection.png'),sources=src_data)
    c=data['circuits']; families=len({x['family'] for x in c['cases']})
    data['engineNote']=f"ngspice 33 batch simulation executed {len(c['cases'])} standalone decks across {families} interface families. The portable decks, raw output, source list and independent checks are in the evidence pack. The recorded results come from ngspice; native Cadence PSpice and Altium Designer 18 runs remain unperformed. No additional EDA installation is needed to review these results."
    data['decisions']=[
       f"Hold the battery pocket and pack sourcing. The product-linked drawing intersects the housing by 11.983 mm³ at nominal and 30.124 mm³ at maximum size. The alternate supplier CAD intersects by {nominal_hit:.3f} mm³. Use both inert gauges and measure the received pack, protection cap, lead exit and connector before powering a closed sample.",
       "Resolve the charger’s behavior when firmware has not run and validate cell-temperature protection for the two-wire battery. A thermistor on the controller does not measure the pouch directly.",
       "Measure the 3.3 V rail under simultaneous radio, backlight, audio and rumble. A modeled derated supply reached 2.836 V. Check the I²C edges with each BOM; one 5 kΩ / 100 pF configuration gave 424 ns against a 300 ns criterion.",
       "Instrument the real speaker differentially and limit the gain after measuring the worst approved waveform. The overdrive stress case predicts 1.408 W against the supplied speaker’s nominal 1 W.",
       "Authorize an engineering build and fixtures against the open-item register. Hold volume PCB, enclosure and packaging commitments until the incoming pack/board revision, market path and pilot costs are signed."
    ]
    data['fit']=[
       ["Controller → sensor","0.474 mm","Registered nominal supplier models. Include PCB warp, component height and adhesive in the actual stack."],
       ["Lens → bezel","0.25 mm","Measure across corners after closure; run the nine-point edge test."],
       ["Reel magnet → AS5600 body","1.20 mm","Package distance. Verify magnet field status, axis and motion during rumble."],
       ["Power cap → switch","0.05 mm","Switch-height tolerance of ±0.20 mm alone permits –0.15 to +0.25 mm nominal rest gap. Mount/print variation is additional."],
       ["Catalog cell → lateral fences","0.40 mm","Applies to the listed envelope; the alternative vendor body collides."],
       ["Dovetail bearing length / gap","35 mm / 0.295 mm","Nominal normal flank gap. Screw preload takes up play; measure grip deflection and cycle wear."],
       ["Top key / rear shoe","0.18 mm / 3.20 mm","Key recess and added pocket depth; stowed thickness is 33.20 mm."]]
    data['fitNotes']=[
       f"Historical part fit: {len(fit['static_and_sampled_checks'])} Rev F rigid placement and motion checks, with a {fit['threshold_mm3']} mm³ interference reporting threshold. The handle ledger includes {grip['motion']['slide_samples']} slide samples and {grip['motion']['unlock_samples']} screw samples. These records have a narrower object set than the populated integration review.",
       f"Expanded review: {len(parts)} selectable records; {cover['pair_tests']} candidate component pair tests, and {len(gated)} seated pair(s) still marked resolve in the latest ledger. Expected electrical contacts and mating interfaces are reported separately. Flexible paths represent intended installation.",
       f"Catalog body is 34 × 62 × 5 mm. Alternate supplier CAD includes a 37 mm body width and 6 mm cap. Across {len(tested)} tested in-plane orientations/translations, new housing overlaps range from {min(tested):.3f} to {max(tested):.3f} mm³. These tests do not exhaust all possible packaging changes.",
       "Engineering change proposal: measure the maximum approved pouch, protection cap and lead radius, then move fences and the battery connection as a coordinated change. The 38 × 64 × 7.3 mm study window intersects other geometry. Check shell thickness, rigid retention, lead bend radius, antenna clearance and grip loads on the revised model.",
       "The USB cable, manufacturing fixtures and packaging are external. Seated pin/solder-joint envelopes, wires and generic fasteners do not resolve the manufacturer’s hidden bond wires, copper layers, threads or deformation. Use the part manifest for every representation."]
    data['brake']=readjson(REPO/'hardware/mechanical/experiments/reel-brake/driver-results.json')['cases']
    data['firmware']=[
       "Hardware identity: Waveshare 31137, 16 MB flash, OPI PSRAM and two 3 MiB application slots. Candidate 0.7 uses 1,439,630 flash bytes and 52,172 bytes of static RAM. Runtime PSRAM, peak heap and stack high-water marks still require board logging.",
       "Host/WASM evidence includes 250,000 weighted casts; 1,404 landable location/time/technique combinations; signed reel wrap, 12 detents, fish cue priority and saves. Browser checks cover 468 distinct time/location scenes, touch, menu overlays, motion inputs and two-profile event scoring.",
       "Bench: compare physical acceleration and signed reel counts against fixtures. Play every fish motif and record motor current, sound and sensor data together. Test the top-left key, touch grid, gyro API and RTC across power modes.",
       "Release: pin board revision, flash layout, API, compiler and binary digest. Validate wrong-target, corrupted and interrupted OTA updates and post-boot recovery with an owner-approved staging key/feed. Preserve an independent USB recovery fixture and verify journal retention."]
    data['gameVersion']=str(next(line for line in (REPO/'firmware/WillowCreek/UpdateFeed.h').read_text().splitlines() if 'releaseNumber=' in line).split('releaseNumber=')[1].split(';')[0])
    data['softwareCases']=readcsv(HERE/'software-evidence.csv')
    data['wikiBase']='https://github.com/natthapolvanasrivilai/thai-waters-handheld/blob/main/docs/wiki/'
    data['explodedImage']=picture(out/'Riffle-Rev-F-exploded-preview.png')
    data['correlation']=[
       ["3.3 V supply","Step load: scope at A1 and J8, measure branch current and effective capacitance.","Fit measured rail impedance/recovery and rerun the derated corner; choose rail, decoupling or load-sequencing changes against component limits."],
       ["Shared I²C","Determine assembled pull-up resistance and bus capacitance for each SKU. Probe the remote branch.","At 100 pF the ideal 300 ns rise upper bound is about 3.54 kΩ (1.77 kΩ at 200 pF). The lower bound from 3.3 V, 0.4 V and 3 mA is 0.97 kΩ. Check every IC before selecting effective pull-ups or reducing bus speed."],
       ["Speaker output","Measure worst approved differential RMS on the actual load at high battery voltage.","At the assumed 5.4 Ω resistive corner, 1 W corresponds to 2.32 V RMS. Verify thermal behavior on the real driver and speaker before locking the gain table."],
       ["Battery charging","Log voltage, current, pouch and PCB temperatures with app running, reset, unprogrammed, and power key off.","Qualify the independent hardware response at charger and pack limits. The application’s verified configuration cannot constrain behavior before CPU boot."],
       ["Battery geometry","Measure the complete protected pack, sleeve, lead exit, plug, tape and assembly stack at maximum supplied dimensions.","Fit an inert maximum-envelope sample first. Require supplier tolerance agreement and a revised no-compression assembly before release."]]
    data['hardwareBridge']=[
       "Measure startup, play, Wi-Fi event, off and charging power separately at the pack and USB ports. Run representative transitions and correlate measured traces with the modeled capacitance, harness resistance and load profiles.",
       "Capture firmware build, radio setting, backlight level, audio/rumble levels, calibration and board revision in every measurement. The phone browser exercises interaction logic. A real handheld is required to qualify the sensor path, USB power system, speaker and ERM."]
    data['electricalScope']=[
       "The board is purchased as an assembly. PSpice-compatible primitives can bound connector drops, bus timing, key contacts, motor and speaker loads; closed-loop converter dynamics, PMIC charge algorithm and RF silicon internals need manufacturer models or measurements.",
       "Qualify RF/exposure and EMC with the real antenna, powered assembly and hand/accessory configurations. USB eye/ESD, QSPI LCD edges, touch noise, audio acoustics, reel magnetic immunity and IMU motion require layout, fixtures or physical instruments.",
       "Within a stated bound means that the selected behavioral circuit and corner met that numerical criterion. Characterization rows lack a released limit. Bench evidence must identify the ordered component revision and calibration before migration to DVT."]
    data['productionIntro']="For the engineering lot, buy the controller and sensor assemblies, fabricate the power-key carrier, print the parts, build keyed harnesses and retain all revision evidence. The routing changes at the pilot when cable vendors, fixtures and work instructions are qualified. A change to a custom board or molded shell triggers a new validation baseline."
    data['launch']=[
       f"Lead with direct sales to Thai fishing and handheld-game enthusiasts. Test the full bundle at ฿{full['thDtcPriceThb']:,} in Thailand and US${full['usDtcPriceUsd']} before US sales tax. These are proposed retail prices; all landed cost and margin calculations depend on the modeled channel assumptions.",
       "Demonstrate the physical distinction between a prawn pick, a bottom-holding stingray and a fast-running fish. Use the playable phone demo for discovery. Film the actual motor-equipped device for haptic claims.",
       "Run two landing-page price offers with separate Thai/English creative. Record qualified waitlist conversion, acquisition cost, intended SKU and regional demand. Use refundable reservations only after manufacturing dates and applicable market clearance are known.",
       "Budget for paid acquisition and returns from the workbook contribution model. Compare observed CAC and warranty costs after a small direct pilot. Conventional 50%-of-MSRP wholesale for the full SKU has negative modeled contribution; redesign cost or renegotiate terms before onboarding retailers."]
    data['transfer']=[
       "EVT: freeze the received board version, battery and wiring; record prototype faults. DVT: release production-intent materials and drawings and validate safety, radio, firmware recovery and wear on representative units. PVT: run the intended process and use first-pass yield, timed labor and cost evidence to approve production.",
       "Each unit record carries serial, component lots, hardware revision, firmware digest, variant, calibrated equipment, procedure ID, measured limits, deviations and approval. Test failures receive corrective action and repeat measurements on the affected configuration.",
       "A released market SKU needs supplier quotes and change notification, final electrical/harness drawings, material declarations, pack transport evidence, applicable lab filings, approved artwork, signed update ownership and service instructions."]
    data['manifest']=[
       ["Firmware 0.7 application SHA-256","e7531e385ae7bb868c9ce551486e7fd2c167d2f6d52570eec34aa26600787d8b"],
       ["CAD baseline SHA-256",sha(FIT/'Rev-F-top-power.step.gz')],["Circuit case definitions SHA-256",sha(CIR/'cases.json')],["Solver identity",str(c['engine'])+"; "+str(c['engine_sha256'])],
       ["Model-to-BOM register","hardware/mechanical/rev-F/review/parts.json"],["Simulation evidence","hardware/verification/circuits/{decks,results.csv,raw-ngspice.zip,sources.json}"],
       ["Purchase and labor assumptions","sourcing/production-intent/"],["Execution and sign-off records","manufacturing/rev-F-review/ · verification/firmware-0.7/"]]
    model=out/'Riffle-Rev-F-exploded.html'
    if not model.exists():raise FileNotFoundError(model)
    doc=(HERE/'review-template.html').read_text(encoding='utf-8-sig')
    for key,value in {'@@FONT@@':b64((REPO/'game/assets/fonts/AtkinsonHyperlegibleNext.ttf').read_bytes()),'@@DATA@@':json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'@@MODEL@@':b64(gzip.compress(model.read_bytes(),mtime=0)),'@@GAME@@':b64(gzip.compress((REPO/'game/Thai-Waters-play.html').read_bytes(),mtime=0)),'@@TAIL@@':(HERE/'review-tail.html').read_text(encoding='utf-8-sig')+(HERE/'handbook-ui.html').read_text(encoding='utf-8-sig')}.items():
        assert key in doc
        doc=doc.replace(key,value)
    file=out/'Riffle-Rev-F-engineering-review.html'
    file.write_text(doc,encoding='utf-8')
    print(file,file.stat().st_size, len(c['cases']),len(parts))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--outputs',type=Path,required=True,help='Directory with standalone exploded viewer and product render')
    build(p.parse_args().outputs.resolve())
