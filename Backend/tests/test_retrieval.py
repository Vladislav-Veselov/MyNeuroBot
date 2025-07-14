import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough

# Load environment variables
load_dotenv()

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def test_rag():
    print("Testing RAG system...")
    
    # Initialize components
    print("Loading vector store...")
    VECTOR_DIR = Path(__file__).parent / "vector_KB"
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = FAISS.load_local(str(VECTOR_DIR), embeddings)
    
    print("Initializing LLM...")
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # Test retrieval
    print("\nTesting retrieval...")
    test_query = "What is this knowledge base about?"
    docs = vector_store.similarity_search(test_query, k=3)
    print(f"\nRetrieved {len(docs)} documents:")
    for i, doc in enumerate(docs, 1):
        print(f"\nDocument {i}:")
        print(doc.page_content[:200] + "...")
    
    # Test full RAG chain
    print("\nTesting full RAG chain...")
    template = """Answer the question based on the following context. If you cannot answer the question based on the context, say so.

Context:
{context}

Question: {question}

Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
    )
    
    try:
        print("\nGenerating response...")
        response = rag_chain.invoke(test_query)
        print("\nResponse:", response.content)
    except Exception as e:
        print("\nError:", str(e))

if __name__ == "__main__":
    test_rag() 