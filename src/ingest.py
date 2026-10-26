"""Lê o PDF, divide o texto e armazena embeddings no pgVector."""
import hashlib
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from search import obter_banco_vetorial

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ_PROJETO / '.env')


def main():
    arquivo_pdf = Path(os.getenv('PDF_PATH', 'document.pdf'))
    if not arquivo_pdf.is_absolute():
        arquivo_pdf = RAIZ_PROJETO / arquivo_pdf
    if not arquivo_pdf.is_file():
        raise FileNotFoundError(f'PDF não encontrado: {arquivo_pdf}')
    paginas = PyPDFLoader(str(arquivo_pdf)).load()
    trechos = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(paginas)
    trechos = [trecho for trecho in trechos if trecho.page_content.strip()]
    if not trechos:
        raise ValueError('Nenhum texto foi extraído do PDF. PDFs digitalizados podem exigir OCR.')
    hash_pdf = hashlib.sha256(arquivo_pdf.read_bytes()).hexdigest()
    for indice, trecho in enumerate(trechos):
        trecho.metadata['pdf_sha256'] = hash_pdf
        trecho.metadata['chunk_index'] = indice
    identificadores = [hashlib.sha256(f'{hash_pdf}:{indice}'.encode()).hexdigest() for indice in range(len(trechos))]
    obter_banco_vetorial().add_documents(trechos, ids=identificadores)
    print(f'Ingestão concluída: {len(paginas)} páginas, {len(trechos)} trechos.')


if __name__ == '__main__':
    main()
