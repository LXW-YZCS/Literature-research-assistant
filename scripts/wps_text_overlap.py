"""Read-only WPS text overlap candidates; visual inspection remains necessary."""
from pathlib import Path
import argparse,json
import win32com.client

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('presentation',type=Path)
parser.add_argument('--open-readonly',action='store_true',help='Open a non-active document read-only and close only that document afterwards.')
args=parser.parse_args();target=args.presentation.resolve()
if not target.is_file():raise SystemExit('Presentation not found')
app=win32com.client.Dispatch('KWPP.Application');deck=None;opened=False
for i in range(1,app.Presentations.Count+1):
 candidate=app.Presentations.Item(i)
 if str(candidate.FullName).lower()==str(target).lower():deck=candidate;break
if deck is None:
 if not args.open_readonly:raise SystemExit('Presentation is not already open; specify --open-readonly if desired')
 deck=app.Presentations.Open(str(target),True,False,False);opened=True
issues=[];unavailable=[]
try:
 for n in range(1,deck.Slides.Count+1):
  slide=deck.Slides.Item(n);items=[]
  for j in range(1,slide.Shapes.Count+1):
   shape=slide.Shapes.Item(j)
   try:
    if not shape.HasTextFrame or not shape.TextFrame.HasText:continue
    r=shape.TextFrame.TextRange;x,y,w,h=map(float,(r.BoundLeft,r.BoundTop,r.BoundWidth,r.BoundHeight))
    if w<=0 or h<=0:unavailable.append({'slide':n,'shape':shape.Name});continue
    items.append((x,y,x+w,y+h,shape.Name,r.Text[:40]))
   except Exception as exc:unavailable.append({'slide':n,'shape':shape.Name,'error':str(exc)})
  for i in range(len(items)):
   for j in range(i+1,len(items)):
    a,b=items[i],items[j];w=min(a[2],b[2])-max(a[0],b[0]);h=min(a[3],b[3])-max(a[1],b[1])
    if w>3 and h>3:issues.append({'slide':n,'overlap_points':[round(w,1),round(h,1)],'shapes':[a[4],b[4]],'snippets':[a[5],b[5]]})
 print(json.dumps({'presentation':str(target),'slides':deck.Slides.Count,'candidates':issues,'unavailable':unavailable,'limitation':'Text-frame candidates only; does not inspect tables, pictures, line occlusion or semantic accuracy. Manual visual review is required.'},ensure_ascii=False,indent=2))
finally:
 if opened:deck.Close()
