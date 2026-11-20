"""Regenerate the revision-controlled engineering BOM in this directory."""
import csv
from decimal import Decimal as D
from pathlib import Path
D0=D(0)
s=Path(__file__).resolve().parent
root=s.parents[1]
def rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))
def money(n):
    return f'{n:.6f}'
def out(path, rs):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n')
        w.writeheader()
        w.writerows(rs)
legacy=rows(s/'R0010-prototype-budget.csv')
sources={x['ref']:x for x in rows(s/'R0010-source-evidence.csv')}
prints=rows(s/'R0011-print-manifest.csv')
assert len(legacy)==75 and len(sources)==75
assert sum(x['role']=='device' for x in prints)==17
haptic=rows(s/'R0004-haptic-terminal-candidate.csv')
eco=rows(root/'hardware/electronics/integration-r0004/bom-delta.csv')
part_links={r['mpn']:r['part_page'] for r in rows(s/'R0004-candidate-part-links.csv')}
part_links['PMV65XP']=part_links['PMV65XP,215']
offers={x['ref']:x for x in rows(s/'R0011-R0004-market-snapshot.csv')}
project='https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-receiver-toolpaths-2/Pocket-Reel-R0011-X1C.3mf'
kit='https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-receiver-toolpaths-2/TW-A-0001-R0011-fit-print.zip'
result=[]
def line(ref,option,name,mpn,qty,uom,currency='',unit='',channel='',pos='',doc='',sha='',stock='',pack='',basis='',checkout='',status='',source_date=''):
    result.append(dict(ref=ref,option=option,component=name,manufacturer_part_or_internal_number=mpn,
      quantity=qty,uom=uom,currency=currency,unit_allocation=unit,
      line_allocation=money(D(qty)*D(unit)) if unit and qty else '',purchase_vendor=channel,
      purchase_url=pos,drawing_or_datasheet=doc,drawing_sha256=sha,stock_snapshot=stock,pack_or_moq=pack,
      minimum_checkout_line_currency_same_as_allocation=checkout,price_as_of=source_date,
      status=status,shipping_tax_and_basis=basis))
superseded={'W4-1','W4-2','W4-3','W4-4','W4-5','C8'}
print_refs={}
for x in legacy:
    ref=x['Ref']
    source=sources[ref]
    if x['group']=='Printed parts':
        print_refs[Path(x['url']).name]=x
        continue
    qty=x['qty']
    held=ref=='BT2'
    removed=ref in superseded
    status='qualification hold — not purchased' if held else 'superseded in R0004 — no allocation' if removed else 'historical USD allocation — not verified checkout'
    if held or removed:
        qty='0'
    url=x['url'] if x['url'].startswith('https://') else ''
    line(ref,x['Variant'],x['Description'],x['mpn'],qty,x['UOM'],'USD' if x['price'] and not removed else '',
         x['price'] if not removed else '',x['Source'],url,source['specification'] or (x['url'] if not url else ''),source['specification_sha256'],
         basis=x['basis'],status=status,source_date=source['review'] if not removed and not held else '')
for x in prints:
    filename=Path(x['file']).name
    old=print_refs.pop(filename,None)
    ref=old['Ref'] if old else {'usb-c-shield-mask.stl':'P13-ALT','PKCELL-max-body-with-wire-sockets.stl':'GAUGE-PKCELL','Adafruit-258-CAD-with-PCM-and-stubs.stl':'GAUGE-258'}[filename]
    price=old['price'] if old else ''
    if ref=='P1-1': price=money(D('53.8642578125')*D('0.025')) # X1C plate 1; inherited USD 25/kg assumption
    line(ref,old['Variant'] if old else 'Shop or alternate',filename,x['part'] or ref,x['quantity_per_unit'],'each','USD' if price else '',price,
         'MALIEV in-house FDM','',kit+' • '+x['file'],x['sha256'],
         basis=x['material']+'; R0011 released shape; housing 53.864 g on native X1C plate 1, other allocations archived; X1C grouped projections: '+project+'.',
         status='in-house estimated allocation' if old else x['role'],source_date='2026-11-19' if price else '')
assert not print_refs, print_refs
for x in haptic:
    ref=x['ref']; line(ref,'Rumble',x['disposition'],x['mpn'],x['qty'],'each','USD',x['unit_usd'],'DigiKey US',x['source_url'],
      'hardware/electronics/harness-r0004/README.md',basis='Historical catalog price; confirm fit, pack, stock, VAT and freight. Variant remains conditional.',
      status='R0004 candidate historical allocation',source_date='2026-11-19')
line('W4-SPACER','Rumble','Unclad 1.00 mm FR-4 spacer 6.15 × 13.10 mm','W4-SPACER-R0004','1','each',doc='hardware/electronics/harness-r0004/README.md',status='cost/qualification hold')
line('W4-STRAP','Rumble','Local 30 AWG underside mode strap','W4-STRAP-R0004','1','each',doc='hardware/electronics/harness-r0004/README.md',status='cut length / cost hold')
line('B1-ALT','Core alternate','PKCELL gauge, not an approved sourced cell','B1-ALT-PKCELL','0','each',doc='hardware/mechanical/TW-A-0001-R0011/PRINT-GUIDE.md',status='inert gauge only; exact supplied battery and polarity require qualification')
split_refs={
    'Q_KEY_P Q_KEY_N': [('Q_KEY_P','PMV65XP','1'),('Q_KEY_N','PMV16XNR','1')],
    'R_KUP R_KPD': [('R_KUP','ERJ-3EKF3303V','1'),('R_KPD','ERJ-3EKF1003V','1')],
    'Q_LOW_A Q_LOW_B Q_LOW_DRIVE': [('Q_LOW_A/B','PMV65XP','2'),('Q_LOW_DRIVE','PMV16XNR','1')],
    'R18 R19 R_FT_P R_FT_N': [('R18/R19','ERJ-3GEYJ100V','2'),('R_FT_P/N','ERJ-3GEYJ270V','2')],
    'R_UV_TOP R_UV_BOTTOM R_UV_FB': [('R_UV_TOP','196k 0.1% thin film: exact MPN open','1'),('R_UV_BOTTOM','105k 0.1% thin film: exact MPN open','1'),('R_UV_FB','4.99M 1% thick film: exact MPN open','1')],
}
for x in eco:
    spec=x['manufacturer_candidate']
    mpn=next((k for k in part_links if k in spec),spec)
    for ref,part,qty in split_refs.get(x['ref'],[(x['ref'],mpn,x['qty'])]):
        if part=='PMV65XP': part='PMV65XP,215'
        dnp=ref=='A3.R1 A3.R2'
        line('ECO:'+ref,'Electrical ECO hold',x['decision'],part,'0' if dnp else qty,
          'each' if qty.isdigit() else 'see design',pos=part_links.get(part,''),
          doc=x['source'] if x['source'].startswith('https://') else 'hardware/electronics/integration-r0004/README.md',
          basis=x['connection_or_qualification']+(' • Two existing pull-ups removed; none purchased.' if dnp else ''),
          status='not included in rollup — PCB layout and powered qualification open')
for ref,x in offers.items():
    assert any(r['ref']==ref for r in result),ref
    line(ref+'-OFFER','Procurement alternative',x['name'],x['mpn'],x['quantity'],'each',x['currency'],x['unit_price'],x['supplier'],x['url'],x['specification'],
      stock=x['stock'],pack=x['pack'],basis=x['basis'],checkout=x['checkout'],status=x['status'],source_date=x['seen'])
ids=[r['ref'] for r in result]
assert len(ids)==len(set(ids))
assert sum(r['status']=='in-house estimated allocation' for r in result)==17
assert len([r for r in result if r['option']=='Electrical ECO hold'])==len(eco)+sum(len(parts)-1 for parts in split_refs.values())
assert all(not r['line_allocation'] for r in result if r['option']=='Electrical ECO hold')
assert not any(r['ref'] in superseded and r['line_allocation'] for r in result)
assert all(bool(r['currency']) for r in result if r['line_allocation'])
alts={x['ref']:x for x in rows(s/'R0011-R0004-alternate-sources.csv')}
lookup={x['ref']:x for x in result}
primary_skus={'A1':'31137','A2':'1528-6357-ND','B1':'258 (verify seller SKU)',
              'SP1':'1528-2716-ND','MG1':'469-1024-ND','M1':'474-ROB-08449'}
# Preserve cost basis, distinct from the current ranked purchase channels.
for r in result:
    ref=r['ref']; offer=lookup.get(ref+'-OFFER')
    fallback=alts.get(ref,{})
    primary=offer or r
    applicable=bool(r['purchase_url']) and r['option']!='Procurement alternative' and r['quantity'] not in ('0','')
    r.update(primary_supplier=(primary['purchase_vendor'] or 'DigiKey catalog (pricing and stock not verified)') if applicable else '',
      primary_supplier_sku=primary_skus.get(ref,'verify seller SKU against MPN') if applicable else '',
      primary_url=primary['purchase_url'] if applicable else '',
      primary_currency=primary['currency'] if applicable else '',
      primary_unit_price=primary['unit_allocation'] if applicable and offer else '',
      primary_price_as_of=primary['price_as_of'] if applicable and offer else '',
      primary_stock=primary['stock_snapshot'] or 'Unverified' if applicable else '',
      alternate_supplier=fallback.get('vendor',''),alternate_supplier_sku=fallback.get('vendor_sku',''),
      alternate_exact_mpn=fallback.get('identical_mpn',''),alternate_url=fallback.get('url',''),
      alternate_currency=fallback.get('currency',''),alternate_unit_price=fallback.get('unit_price',''),
      alternate_price_as_of=fallback.get('price_as_of',''),alternate_stock=fallback.get('stock',''),
      alternate_qualification=('not applicable — in-house/alternate offer/superseded' if not applicable else
          'no qualified alternate' + (' — '+fallback['qualification'] if fallback else '')),
      substitute_status=('PKCELL gauge is not an approved alternate battery' if ref=='B1' else ''))
    if applicable and fallback:
        assert r['primary_url']!=r['alternate_url'] and r['primary_supplier']!=r['alternate_supplier']
assert all(x['primary_supplier'] and x['alternate_qualification'] for x in result if x['primary_url'])
out(s/'R0011-R0004-engineering-BOM.csv',result)
components=[r for r in result if r['option']!='Procurement alternative' and r['line_allocation']]
print(len(result),'lines;',len(components),'allocated; illustrative USD subtotal:',sum((D(r['line_allocation']) for r in components),D0))
