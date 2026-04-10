from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings


PERSIST_DIR = "memoria_knowledge"
MODEL = "llama3"


def construir_vectorstore():
    embeddings = OllamaEmbeddings(model=MODEL)
    return Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)


def buscar_conhecimento(pergunta, k=4):
    vectorstore = construir_vectorstore()
    resultados = vectorstore.similarity_search(pergunta, k=k)

    saida = []
    for r in resultados:
        fonte = r.metadata.get("fonte", "desconhecida")
        chunk = r.metadata.get("chunk", "?")
        saida.append(f"[{fonte} | chunk {chunk}] {r.page_content}")

    return "\n\n".join(saida)


if __name__ == "__main__":
    while True:
        pergunta = input("\nPergunta: ").strip()
        if pergunta.lower() in ["sair", "exit"]:
            break

        resposta = buscar_conhecimento(pergunta)
        print("\n--- RESULTADOS ---")
        print(resposta if resposta else "Nenhum resultado encontrado.")