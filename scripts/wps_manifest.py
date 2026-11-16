"""Read-only validation for the native PPTX authority of a visible WPS project."""
import hashlib,json,posixpath,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from visual_review import review_state

P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PRODUCTION=('本页旨在','需要核查','我们选择该图因为','质量检查通过','作为AI','由原页核对','原图保留')
def inspect_wps(root,m):
    errors=[];warnings=[];fingerprints={}
    def track(p):
        p=Path(p).resolve()
        if not p.is_file():errors.append(f'Missing file: {p}');return False
        fingerprints[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return True
    track(root/'research-deck.json')
    source_ids=[]
    for src in m.get('sources',[]):
        sid=src.get('id')
        if not sid or sid in source_ids:errors.append('Source IDs must be present and unique')
        source_ids.append(sid)
        if src.get('path'):track(root/src['path'])
        elif not src.get('url'):errors.append(f'Source {sid} needs path or URL')
    pages=m.get('pages',[]);ids=[p.get('id') for p in pages]
    if not pages or None in ids or len(ids)!=len(set(ids)):errors.append('Page roster and unique IDs required')
    if [p.get('slide') for p in pages]!=list(range(1,len(pages)+1)):errors.append('Page roster must follow actual PPTX order, using slide indices 1..N')
    for p in pages:
        for key in ('role','claim','evidence'):
            if not p.get(key):errors.append(f'{p.get("id")}: missing {key}')
        for ev in p.get('evidence',[]):
            if ev.get('source') not in source_ids or not ev.get('locator'):errors.append(f'{p.get("id")}: unresolved evidence')
    for asset in m.get('assets',[]):
        track(root/asset.get('path',''))
        if not asset.get('source'):errors.append('Asset source missing')
        if asset.get('role') in ('context-image','background') and not asset.get('rights'):errors.append('External asset reuse basis missing')
    for item in m.get('inputs',[]):track(root/item)
    for folder in ('charts','templates','notes'):
        for p in (root/folder).rglob('*'):
            if p.is_file():track(p)
    path=root/m.get('presentation','')
    if not m.get('presentation'):errors.append('Native WPS project requires presentation path')
    elif track(path):
        try:
            with zipfile.ZipFile(path) as z:
                def relationships(part):
                    parent,name=posixpath.split(part)
                    rp=posixpath.join(parent,'_rels',name+'.rels')
                    if rp not in z.namelist():return {}
                    return {x.get('Id'):(posixpath.normpath(posixpath.join(parent,x.get('Target',''))).lstrip('/'),x.get('Type','')) for x in ET.fromstring(z.read(rp)) if x.get('TargetMode')!='External'}
                rels=relationships('ppt/presentation.xml')
                ids_xml=ET.fromstring(z.read('ppt/presentation.xml')).findall(f'./{{{P}}}sldIdLst/{{{P}}}sldId')
                if len(ids_xml)!=len(pages):errors.append('Manifest page count differs from PPTX')
                for i,node in enumerate(ids_xml,1):
                    part=rels[node.get(f'{{{R}}}id')][0]
                    tree=ET.fromstring(z.read(part));visible=' '.join(n.text or '' for n in tree.iter(f'{{{A}}}t'))
                    if i<=len(pages) and pages[i-1].get('expected_title'):
                        expected=''.join(pages[i-1]['expected_title'].split())
                        shape_texts=[''.join(''.join((n.text or '') for n in sh.iter(f'{{{A}}}t')).split()) for sh in tree.iter(f'{{{P}}}sp')]
                        if not any(expected in value for value in shape_texts):errors.append(f'Slide {i}: expected text not found in a shape; title or page order may have changed: {pages[i-1]["expected_title"]}')
                    for phrase in PRODUCTION:
                        if phrase in visible:warnings.append(f'Slide {i}: review production language: {phrase}')
                    sr=relationships(part)
                    for target,typ in sr.values():
                        if typ.endswith('/image') and target not in z.namelist():errors.append(f'Slide {i}: missing embedded image')
                    if m.get('notes'):
                        notes=[target for target,typ in sr.values() if typ.endswith('/notesSlide')]
                        if not notes:errors.append(f'Slide {i}: missing embedded notes');continue
                        nt=ET.fromstring(z.read(notes[0]));body=[]
                        for sh in nt.iter(f'{{{P}}}sp'):
                            ph=sh.find(f'.//{{{P}}}ph')
                            if ph is not None and ph.get('type') in ('sldNum','hdr','ftr','dt','sldImg'):continue
                            body.extend(n.text or '' for n in sh.iter(f'{{{A}}}t'))
                        ntxt=' '.join(body).strip()
                        if not ntxt:errors.append(f'Slide {i}: empty embedded notes')
                        for phrase in PRODUCTION:
                            if phrase in ntxt:warnings.append(f'Slide {i}: review notes production language: {phrase}')
        except (zipfile.BadZipFile,KeyError,ET.ParseError) as e:errors.append(f'Invalid PPTX package: {e}')
    lock=root/'validation/research-inputs.json';changed=[]
    if lock.exists():
        old=json.loads(lock.read_text(encoding='utf-8')).get('fingerprints',{})
        changed=sorted(k for k in set(old)|set(fingerprints) if old.get(k)!=fingerprints.get(k))
    visual,review_changed,review_warning=review_state(root,fingerprints)
    if review_warning:warnings.append(review_warning)
    return {'errors':errors,'warnings':warnings,'changed_since_checkpoint':changed,'changed_since_visual_review':review_changed,'fingerprints':fingerprints,'visual_review':visual,'authoring_mode':'wps','foreground_process':'requires actual session observation; package checks cannot prove it'}
