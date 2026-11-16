"""Create a reproducible presentation figure from CSV and a JSON specification.

Run with the skill's .runtime/Scripts/python.exe. Defaults to SVG, PNG (180 DPI) and a receipt.
JSON supports figsize in inches, png_dpi and export_pdf. No aggregation,
regression, significance test or inferred uncertainty is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
import seaborn as sns

KINDS = ('line', 'scatter', 'bar', 'box', 'violin', 'hist', 'ecdf', 'heatmap')

def make_chart(spec_path):
    path = Path(spec_path).resolve()
    spec = json.loads(path.read_text(encoding='utf-8'))
    kind = spec['kind']
    if kind not in KINDS:
        raise ValueError(f'kind must be one of {KINDS}')
    if not spec.get('source'):
        raise ValueError('source is required; label synthetic fixtures as demonstration data')
    data_path = (path.parent / spec['data']).resolve()
    frame = pd.read_csv(data_path)
    if frame.empty:
        raise ValueError('Data is empty')
    x, y, group = spec.get('x'), spec.get('y'), spec.get('group')
    columns = spec.get('columns', []) if kind == 'heatmap' else [c for c in (x,y,group,spec.get('lower'),spec.get('upper')) if c]
    for c in columns:
        if c not in frame:
            raise ValueError(f'Missing column: {c}')
    if frame[columns].isna().any().any():
        raise ValueError('Missing values: specify and perform a documented handling step first')
    numeric = columns if kind == 'heatmap' else ([y] if kind in ('line','scatter','bar','box','violin') else [x])
    if kind in ('line','scatter'): numeric += [x]
    for c in set(numeric):
        if c is None or not pd.api.types.is_numeric_dtype(frame[c]) or not np.isfinite(frame[c]).all():
            raise ValueError(f'Expected finite numeric values: {c}')
    if kind == 'bar' and frame.duplicated([x]+([group] if group else [])).any():
        raise ValueError('Bar input needs one value per category/group; use box or explicitly aggregate upstream')
    if bool(spec.get('lower')) != bool(spec.get('upper')):
        raise ValueError('Both lower and upper are required for an interval')
    if spec.get('lower') and kind != 'line':
        raise ValueError('Interval bands are supported only for line; use an explicit error-bar workflow for other types')
    if spec.get('lower') and not spec.get('interval_definition'):
        raise ValueError('Explain interval_definition (SD/SEM/CI etc.)')
    # Validate optional export settings without changing legacy defaults.
    export_pdf = spec.get('export_pdf', False)
    if not isinstance(export_pdf, bool):
        raise ValueError('export_pdf must be a boolean')
    png_dpi = spec.get('png_dpi', 180)
    if isinstance(png_dpi, bool) or not isinstance(png_dpi, (int, float)) or not np.isfinite(png_dpi) or png_dpi <= 0:
        raise ValueError('png_dpi must be a positive finite number')
    figsize = spec.get('figsize', [10, 5.6])
    if (not isinstance(figsize, (list, tuple)) or len(figsize) != 2 or
        any(isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or v <= 0 for v in figsize)):
        raise ValueError('figsize must contain two positive finite values in inches')
    font = spec.get('font','Microsoft YaHei')
    font_manager.findfont(font, fallback_to_default=False)
    plt.rcParams.update({'font.family':font,'svg.fonttype':'none','axes.unicode_minus':False,'font.size':15})
    fig, ax = plt.subplots(figsize=figsize,layout='constrained')
    palette = sns.color_palette('colorblind')
    sns.set_palette(palette)
    histogram_bins = np.histogram_bin_edges(frame[x], bins=spec.get('bins','auto')) if kind == 'hist' else None
    groups = list(frame.groupby(group,sort=False)) if group else [(None,frame)]
    if kind in ('line','scatter','ecdf','hist'):
        for i,(label,part) in enumerate(groups):
            color=palette[i % len(palette)]
            if kind == 'line':
                part=part.sort_values(x)
                if part[x].duplicated().any(): raise ValueError('Repeated x values need grouping or explicit aggregation')
                ax.plot(part[x],part[y],marker=['o','s','^','D'][i%4],color=color,label=label)
                if spec.get('lower'):
                    lo,hi=part[spec['lower']],part[spec['upper']]
                    if not (np.isfinite(lo).all() and np.isfinite(hi).all() and (lo<=part[y]).all() and (part[y]<=hi).all()):
                        raise ValueError('Invalid interval bounds')
                    ax.fill_between(part[x],lo,hi,color=color,alpha=.16)
            elif kind == 'scatter': ax.scatter(part[x],part[y],label=label,color=color,marker=['o','s','^','D'][i%4])
            elif kind == 'ecdf':
                vals=np.sort(part[x]); ax.step(vals,np.arange(1,len(vals)+1)/len(vals),where='post',label=label,color=color)
            else: ax.hist(part[x],bins=histogram_bins,alpha=.55,label=label,color=color)
        if group: ax.legend(title=group,frameon=False)
    elif kind == 'bar':
        sns.barplot(data=frame,x=x,y=y,hue=group,errorbar=None,ax=ax)
        lo,hi=ax.get_ylim()
        ax.set_ylim(min(0,lo),max(0,hi))
    elif kind in ('box','violin'):
        sizes=frame.groupby([x]+([group] if group else [])).size()
        if kind == 'violin' and sizes.min()<10: raise ValueError('Violin requires sufficient samples; use box + points for small groups')
        if kind == 'violin' and frame.groupby([x]+([group] if group else []))[y].nunique().min()<5:
            raise ValueError('Violin density is unsuitable for constant/few-valued groups; use ECDF, counts or box + points')
        if kind == 'box': sns.boxplot(data=frame,x=x,y=y,hue=group,ax=ax,fliersize=0)
        else: sns.violinplot(data=frame,x=x,y=y,hue=group,ax=ax,cut=0,inner=None)
        sns.stripplot(data=frame,x=x,y=y,hue=group,ax=ax,dodge=bool(group),jitter=False,size=4,legend=False,color='#333333' if not group else None)
    else:
        if not columns: raise ValueError('heatmap requires explicit numeric columns')
        if spec.get('row_label') and spec['row_label'] not in frame: raise ValueError('Missing row_label column')
        if spec.get('annot',False) and frame[columns].size>400:
            raise ValueError('Dense cell annotations would be unreadable; subset or disable annot')
        step=max(1,int(np.ceil(len(frame)/24)))
        positions=np.arange(0,len(frame),step)
        labels=frame[spec['row_label']].astype(str).tolist() if spec.get('row_label') else [str(i) for i in range(len(frame))]
        sns.heatmap(frame[columns],ax=ax,cmap=spec.get('cmap','viridis'),annot=spec.get('annot',False),yticklabels=False)
        ax.set_yticks(positions+.5,labels=[labels[i] for i in positions],rotation=0)
    ax.set_title(spec.get('title',''),loc='left',pad=18)
    default_ylabel = '累计比例' if kind == 'ecdf' else '频数' if kind == 'hist' else (y or '')
    ax.set_xlabel(spec.get('xlabel', x or '')); ax.set_ylabel(spec.get('ylabel', default_ylabel))
    if kind!='heatmap': sns.despine(ax=ax)
    output=(path.parent/spec['output']).resolve(); output.parent.mkdir(parents=True,exist_ok=True)
    extensions = ('.svg', '.png', '.json') + (('.pdf',) if export_pdf else ())
    if any(output.with_suffix(e).exists() for e in extensions) and not spec.get('overwrite',False):
        raise FileExistsError('Output exists; set overwrite=true for an intentional revision')
    fig.savefig(output.with_suffix('.svg')); fig.savefig(output.with_suffix('.png'),dpi=png_dpi)
    if export_pdf:
        fig.savefig(output.with_suffix('.pdf'))
    receipt={'kind':kind,'rows':len(frame),'source':spec['source'],'data_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'spec':spec,'visual_review':'pending','editable_data_in_pptx':False,
             'data_path':str(data_path),'effective_export':{'figsize_inches':[float(v) for v in fig.get_size_inches()], 'png_dpi':png_dpi,'formats':['svg','png']+(['pdf'] if export_pdf else []), 'font':font}}
    output.with_suffix('.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.close(fig)
    print(output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('spec'); a=p.parse_args()
    make_chart(a.spec)
