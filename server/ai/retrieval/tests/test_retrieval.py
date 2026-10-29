import pymupdf

from server.ai.diagnosis.models import RetrievalStatus
from server.ai.retrieval.ingestion import ingest_pdf
from server.ai.retrieval.retriever import BM25Retriever, retrieve_evidence


def make_pdf(path,text):
    doc=pymupdf.open(); page=doc.new_page(); page.insert_text((72,72),text); doc.save(path); doc.close()

def test_ingest_and_retrieve(tmp_path):
    pdf=tmp_path/'projector_manual.pdf'; make_pdf(pdf,'No Signal: press Source Search on the remote to select the active HDMI input.')
    index=tmp_path/'chunks.jsonl'
    assert ingest_pdf(pdf,index,metadata={'document_id':'manual-1','title':'Projector Manual','device_type':'projector'})==1
    result=BM25Retriever(index).retrieve('projector No Signal select HDMI input',{'device_type':'projector'})
    assert result.retrieval_status==RetrievalStatus.FOUND
    assert result.evidence[0].document_id=='manual-1' and result.evidence[0].page_number==1
    assert 'Source Search' in result.evidence[0].text

def test_no_match_returns_no_fabricated_evidence(tmp_path):
    pdf=tmp_path/'manual.pdf'; make_pdf(pdf,'Projector HDMI input source search')
    index=tmp_path/'chunks.jsonl'; ingest_pdf(pdf,index)
    result=retrieve_evidence('microphone battery smells of smoke',index_path=index)
    assert result.retrieval_status==RetrievalStatus.NO_MATCH and result.evidence==[]

def test_missing_index_is_no_match(tmp_path):
    result=retrieve_evidence('projector no signal',index_path=tmp_path/'missing.jsonl')
    assert result.retrieval_status==RetrievalStatus.NO_MATCH and result.evidence==[]

def test_device_type_mismatch_filtered(tmp_path):
    pdf=tmp_path/'manual.pdf'; make_pdf(pdf,'HDMI projector input source selection')
    index=tmp_path/'chunks.jsonl'; ingest_pdf(pdf,index,metadata={'device_type':'projector'})
    result=BM25Retriever(index).retrieve('projector HDMI input',{'device_type':'microphone'})
    assert result.retrieval_status==RetrievalStatus.NO_MATCH
