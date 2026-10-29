"""BM25 retriever implementing the shared RetrievalResult contract."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from server.ai.diagnosis.models import EvidenceItem, RetrievalResult, RetrievalStatus

DEFAULT_INDEX=Path('data/knowledge/chunks.jsonl')
def tokenize(text: str) -> list[str]: return re.findall(r'[a-z0-9]+',text.lower())

class BM25Retriever:
    def __init__(self,index_path: str | Path = DEFAULT_INDEX,*,top_k: int=5,min_query_coverage: float=.12):
        self.index_path=Path(index_path); self.top_k=max(1,top_k); self.min_query_coverage=min_query_coverage
        self.records=[]
        if self.index_path.exists():
            for line in self.index_path.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    item=json.loads(line)
                    if item.get('text') and item.get('chunk_id'): self.records.append(item)
        self.tokens=[tokenize(x['text']) for x in self.records]
        self.bm25=BM25Okapi(self.tokens) if self.tokens else None
    def retrieve(self,query: str,device_context: dict[str,Any] | None=None) -> RetrievalResult:
        context=dict(device_context or {})
        try:
            qt=tokenize(query)
            if not qt or not self.bm25:
                return RetrievalResult(query=query,device_context=context,evidence=[],retrieval_status=RetrievalStatus.NO_MATCH)
            scores=self.bm25.get_scores(qt); matches=[]; qset=set(qt)
            for i,score in enumerate(scores):
                row=self.records[i]
                if any(context.get(k) and row.get(k) and str(context[k]).casefold()!=str(row[k]).casefold() for k in ('device_type','brand','model')): continue
                coverage=len(qset & set(self.tokens[i]))/max(1,len(qset))
                if coverage>=self.min_query_coverage: matches.append((i,float(score)))
            matches.sort(key=lambda x:x[1],reverse=True); matches=matches[:self.top_k]
            if not matches: return RetrievalResult(query=query,device_context=context,evidence=[],retrieval_status=RetrievalStatus.NO_MATCH)
            max_score=max(s for _,s in matches); min_score=min(s for _,s in matches); evidence=[]
            for i,score in matches:
                r=self.records[i]
                evidence.append(EvidenceItem(document_id=str(r['document_id']),title=str(r['title']),page_number=r.get('page_number'),chunk_id=str(r['chunk_id']),text=str(r['text']),relevance_score=(1.0 if max_score == min_score else max(0.,min(1.,(score-min_score)/(max_score-min_score))))))
            return RetrievalResult(query=query,device_context=context,evidence=evidence,retrieval_status=RetrievalStatus.FOUND)
        except Exception:
            return RetrievalResult(query=query,device_context=context,evidence=[],retrieval_status=RetrievalStatus.FAILED)

def retrieve_evidence(query: str,device_context: dict[str,Any] | None=None,index_path: str | Path=DEFAULT_INDEX,top_k: int=5) -> RetrievalResult:
    try: return BM25Retriever(index_path,top_k=top_k).retrieve(query,device_context)
    except Exception: return RetrievalResult(query=query,device_context=dict(device_context or {}),evidence=[],retrieval_status=RetrievalStatus.FAILED)
