from logger import logger


def query_chain(chain, user_input: str):
    try:
        logger.debug(f"Running query chain for user input: {user_input}")
        result = chain({"query": user_input})
        response = {
            "response": result["result"],
            "sources": [
                doc.metadata.get("source", "Unknown")
                for doc in result["source_documents"]
            ],
        }
        logger.debug(f"Chain response: {result}")
        return response
    except Exception as e:
        logger.error(f"Error in query chain: {e}")
        return {
            "error": "An error occurred while processing your query. Please try again later."
        }
