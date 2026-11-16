"""Internal research-deck manifest, provenance checks and source-change detection."""
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.parse import unquote, urlsplit
from visual_review import review_state

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def inspect(root):
    m=load(root/'research-deck.json'); errors=[]; warnings=[]; fingerprints={}
    if m.get('authoring_mode')=='wps':
        from wps_manifest import inspect_wps
        return inspect_wps(root,m)
    fingerprints[str((root/'research-deck.json').resolve())]=digest(root/'research-deck.json')
    pages=m.get('pages',[]); ids=[p.get('id') for p in pages]
    if not pages: errors.append('No page roster')
    if len(ids)!=len(set(ids)) or None in ids: errors.append('Page IDs must be present and unique')
    source_ids=set()
    for src in m.get('sources',[]):
        if not src.get('id') or src['id'] in source_ids: errors.append('Source IDs must be present and unique')
        source_ids.add(src.get('id'))
        if src.get('path'):
            p=(root/src['path']).resolve()
            if not p.is_file(): errors.append(f'Missing source: {p}')
            else: fingerprints[str(p)]=digest(p)
        elif not src.get('url'): errors.append('Source needs path or URL')
    for page in pages:
        for field in ('role','claim','evidence','svg'):
            if not page.get(field): errors.append(f'{page.get("id")}: missing {field}')
        for ev in page.get('evidence',[]):
            if ev.get('source') not in source_ids or not ev.get('locator'): errors.append(f'{page.get("id")}: unresolved evidence')
        if page.get('svg'):
            p=(root/page['svg']).resolve()
            if not p.is_file(): errors.append(f'Missing SVG: {p}')
            else:
                fingerprints[str(p)]=digest(p)
                try:
                    tree=ET.parse(p)
                    for node in tree.iter():
                        if node.tag.rsplit('}',1)[-1] != 'image': continue
                        href=node.get('href') or node.get('{http://www.w3.org/1999/xlink}href','')
                        if href.startswith('data:'): continue
                        if urlsplit(href).scheme in ('http','https'):
                            errors.append(f'{page["id"]}: image must be materialized locally: {href}')
                            continue
                        asset=(p.parent/unquote(href)).resolve()
                        if not href or not asset.is_file(): errors.append(f'{page["id"]}: missing referenced image: {href}')
                        else: fingerprints[str(asset)]=digest(asset)
                    visible=' '.join(t for node in tree.iter() if node.tag.rsplit('}',1)[-1] in ('text','tspan') for t in node.itertext())
                    for phrase in ('本页旨在','需要核查','我们选择该图因为','质量检查通过','作为AI'):
                        if phrase in visible: warnings.append(f'{page["id"]}: review production language: {phrase}')
                except ET.ParseError as e: errors.append(f'{page["id"]}: invalid SVG {e}')
        if m.get('notes'):
            p=root/'notes'/f'{Path(page.get("svg","missing")).stem}.md'
            if not p.is_file(): errors.append(f'Missing notes: {p.name}')
            else:
                fingerprints[str(p.resolve())]=digest(p)
                if not p.read_text(encoding='utf-8').strip(): errors.append(f'{page["id"]}: empty notes')
                for phrase in ('本页旨在','需要核查','我们选择该图因为','质量检查通过','作为AI'):
                    if phrase in p.read_text(encoding='utf-8'): warnings.append(f'{page["id"]}: review notes production language: {phrase}')
    for asset in m.get('assets',[]):
        if asset.get('role') not in ('paper-figure','data-chart','context-image','background','concept-diagram'):
            errors.append('Asset role is missing/unknown')
        p=(root/asset.get('path','')).resolve()
        if not p.is_file(): errors.append(f'Missing asset: {p}')
        else: fingerprints[str(p)]=digest(p)
        if not asset.get('source'): errors.append(f'Asset source missing: {p.name}')
        if asset.get('role') in ('context-image','background') and not asset.get('rights'):
            errors.append(f'Asset reuse basis missing: {p.name}')
    actual={p.name for p in (root/'svg_output').glob('*.svg')}
    expected={Path(p.get('svg','')).name for p in pages}
    if actual!=expected: errors.append('SVG files differ from page roster')
    declared=[Path(p.get('svg','')).name for p in pages]
    if len(declared)!=len(set(declared)): errors.append('Duplicate SVG references in page roster')
    if declared!=sorted(actual): errors.append('Page roster order differs from SVG export order')
    for folder in ('charts','templates'):
        for p in (root/folder).rglob('*'):
            if p.is_file(): fingerprints[str(p.resolve())]=digest(p)
    for relative in m.get('inputs',[]):
        p=(root/relative).resolve()
        if not p.is_file(): errors.append(f'Missing tracked input: {p}')
        else: fingerprints[str(p)]=digest(p)
    lock=root/'validation/research-inputs.json'
    changed=[]
    if lock.exists():
        old=load(lock).get('fingerprints',{})
        changed=[k for k in set(old)|set(fingerprints) if old.get(k)!=fingerprints.get(k)]
    visual,review_changed,review_warning=review_state(root,fingerprints)
    if review_warning:warnings.append(review_warning)
    return {'errors':errors,'warnings':warnings,'changed_since_checkpoint':changed,'changed_since_visual_review':review_changed,'fingerprints':fingerprints,'visual_review':visual}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('command',choices=['init','check','checkpoint','review-visual']); p.add_argument('project'); p.add_argument('--reviewed',action='store_true',help='Attest the current version was visually reviewed; required for review-visual'); a=p.parse_args(); root=Path(a.project).resolve()
    if a.command=='init':
        root.mkdir(parents=True,exist_ok=True)
        target=root/'research-deck.json'
        if target.exists(): raise FileExistsError(target)
        for name in ('sources','svg_output','images','charts','notes','validation'): (root/name).mkdir(exist_ok=True)
        write(target,{'authoring_mode':'wps','presentation':'','audience':'','purpose':'','notes':False,'sources':[],'pages':[],'assets':[]})
        print(target); return
    result=inspect(root)
    if a.command=='checkpoint' and not result['errors']:
        (root/'validation').mkdir(exist_ok=True)
        write(root/'validation/research-inputs.json',result)
    if a.command=='review-visual':
        if not a.reviewed:p.error('review-visual requires --reviewed after actual visual review')
        if not result['errors']:
            (root/'validation').mkdir(exist_ok=True)
            write(root/'validation/visual-review.json',{'reviewed':True,'fingerprints':result['fingerprints']})
            result=inspect(root)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(bool(result['errors']))

if __name__=='__main__': main()
