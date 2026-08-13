from ..config import settings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA



def get_llm_chain(retriever):
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        # api_key=os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY"),
        api_key = settings.groq_api_key_resolved
    )
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
    return chain
