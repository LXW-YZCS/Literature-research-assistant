"""Extract speaking text from final PPTX notes without reading source-location metadata."""
import argparse,json,re
from pathlib import Path
from pptx import Presentation

MARKERS=('资料定位（非口头讲稿）：','资料定位(非口头讲稿):')
SECTION=re.compile(r'^\s*(?:#{1,6}\s*)?(?:讲者提示|备答|资料定位(?:（非口头讲稿）|\(非口头讲稿\))?)\s*[:：]\s*$', re.MULTILINE)
SPOKEN=re.compile(r'^\s*(?:#{1,6}\s*)?口播正文\s*[:：]\s*$', re.MULTILINE)
def spoken_text(text):
    for marker in MARKERS:
        text=text.split(marker,1)[0]
    match=SECTION.search(text)
    if match:text=text[:match.start()]
    return SPOKEN.sub('',text,count=1).strip()

def extract(path):
    rows=[]
    for i,slide in enumerate(Presentation(path).slides,1):
        text=slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ''
        spoken=spoken_text(text)
        if not spoken:raise ValueError(f'Slide {i} has no speaking text')
        rows.append({'slide':i,'text':spoken})
    return rows

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();rows=extract(args.pptx)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Prepared speaking text for {len(rows)} slides')
