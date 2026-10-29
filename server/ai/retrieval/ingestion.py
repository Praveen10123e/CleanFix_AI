"""Extract text from PDF manuals into page-aware JSONL chunks."""
from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path
from typing import Any

import pymupdf

DEFAULT_INDEX = Path("data/knowledge/chunks.jsonl")
def _chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    out=[]; start=0
    while start < len(text):
        end=min(len(text), start+size)
        if end < len(text):
            boundary=text.rfind(" ", start+size//2, end)
            if boundary > start: end=boundary
        part=text[start:end].strip()
        if part: out.append(part)
        if end >= len(text): break
        start=max(start+1,end-overlap)
    return out

def ingest_pdf(pdf_path: str | Path, output_path: str | Path = DEFAULT_INDEX,
               metadata: dict[str, Any] | None = None, append: bool = True) -> int:
    path=Path(pdf_path); meta=dict(metadata or {})
    sidecar=path.with_suffix('.json')
    if sidecar.exists():
        try: meta={**json.loads(sidecar.read_text(encoding='utf-8')),**meta}
        except (OSError,json.JSONDecodeError) as exc: raise ValueError(f'Invalid metadata sidecar {sidecar}') from exc
    doc_id=str(meta.get('document_id') or uuid.uuid5(uuid.NAMESPACE_URL,str(path.resolve())))
    title=str(meta.get('title') or path.stem.replace('_',' ').replace('-',' '))
    records=[]
    try:
        with pymupdf.open(path) as pdf:
            for pno,page in enumerate(pdf,1):
                for cno,chunk in enumerate(_chunks(page.get_text('text')),1):
                    records.append({'document_id':doc_id,'title':title,'page_number':pno,
                      'chunk_id':f'{doc_id}-p{pno}-c{cno}','text':chunk,
                      'device_type':meta.get('device_type'),'brand':meta.get('brand'),'model':meta.get('model')})
    except Exception as exc: raise RuntimeError(f'Could not extract PDF {path}: {exc}') from exc
    if not records: raise ValueError(f'No extractable text in {path}; scanned PDFs need OCR first.')
    output=Path(output_path); output.parent.mkdir(parents=True,exist_ok=True)
    old=[]
    if append and output.exists():
        for line in output.read_text(encoding='utf-8').splitlines():
            if line.strip():
                item=json.loads(line)
                if item.get('document_id') != doc_id: old.append(item)
    with output.open('w',encoding='utf-8') as f:
        for item in old+records: f.write(json.dumps(item,ensure_ascii=False)+'\n')
    return len(records)

def ingest_directory(input_dir: str | Path, output_path: str | Path = DEFAULT_INDEX) -> dict[str,int]:
    folder=Path(input_dir)
    if not folder.exists(): raise FileNotFoundError(f'Manual directory not found: {folder}')
    return {str(pdf):ingest_pdf(pdf,output_path) for pdf in sorted(folder.rglob('*.pdf'))}

def main():
    parser=argparse.ArgumentParser(description='Index CleanFix AI PDF manuals')
    parser.add_argument('--input-dir',default='data/manuals'); parser.add_argument('--output',default=str(DEFAULT_INDEX))
    args=parser.parse_args(); result=ingest_directory(args.input_dir,args.output)
    print(json.dumps({'indexed_files':len(result),'chunks':sum(result.values()),'files':result},indent=2))
if __name__=='__main__': main()
