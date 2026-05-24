import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA

load_dotenv()

def get_llm_chain(retriever):
    llm = ChatGroq(
        model="llama3-70b-8192",
        api_key=os.getenv("GROK_API_KEY"),
    )
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
    return chain
