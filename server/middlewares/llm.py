import os
from langchain.prompts import PromptTemplate
from langchain.chain import RetrievalQA
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# handle your LLM chain
def get_llm_chain(retriever):
    llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.1-70b-8192")
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
        "You are a **MediBot**, an AI-powered assistant trained to help users understand medical documents and health-related questions. Your job is to provide clear, accurate and helpful responses based only on **only on the provied context**" 

        ---
        **Context**: {context}
        **User Question**: {question}

        **Answer**:

        - Respond in a calm, factual, and respectful tone.
        - Use simple explanation when needed.
        - If the context does not contain the answer, say "I am sorry, I could not find relevant information in the provided documents.
        - DO NOT make up facts.
        - DO NOT give medical advice or diagnosis.

        """,
    )
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )
