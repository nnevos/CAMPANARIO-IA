from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


BASE_DIR = Path("knowledge_base")
PERSIST_DIR = "memoria_knowledge"
MODEL = "llama3"


def carregar_arquivos_txt(pasta_base=BASE_DIR):
    documentos = []
    if not pasta_base.exists():
        return documentos

    for arquivo in pasta_base.glob("*.txt"):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read().strip()
                if conteudo:
                    documentos.append({
                        "nome": arquivo.name,
                        "conteudo": conteudo
                    })
        except Exception:
            pass

    return documentos


def dividir_texto(texto, chunk_size=900, chunk_overlap=120):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(texto)


def construir_vectorstore():
    embeddings = OllamaEmbeddings(model=MODEL)
    return Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)


def indexar_conhecimento():
    docs = carregar_arquivos_txt()

    if not docs:
        print("Nenhum arquivo encontrado em knowledge_base/")
        return

    vectorstore = construir_vectorstore()
    textos = []
    metadados = []

    for doc in docs:
        chunks = dividir_texto(doc["conteudo"])
        for i, chunk in enumerate(chunks):
            textos.append(chunk)
            metadados.append({
                "fonte": doc["nome"],
                "chunk": i
            })

    vectorstore.add_texts(textos=textos, metadatas=metadados)
    print(f"{len(textos)} chunks indexados em {PERSIST_DIR}")


if __name__ == "__main__":
    indexar_conhecimento()