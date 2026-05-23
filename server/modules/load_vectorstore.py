import os
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from server import logger

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = "us-east-1"
PINECONE_INDEX_NAME = "medical_index"
RELAXATION_TIME = 1  # in seconds

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialise pinceone instance (we can only make unique indexes)
pinecone = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
serverless_spec = ServerlessSpec(
    name=PINECONE_INDEX_NAME,
    cloud="aws",
    region=PINECONE_ENV,
)

# Check if the index already exists, if not create it
existing_indexes = [i["name"] for i in pinecone.list_indexes()]
if PINECONE_INDEX_NAME not in existing_indexes:
    print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
    pinecone.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=768,
        metric="dotproduct",
        spec=serverless_spec,
    )

    # Relaxation time while index is being created
    while not pinecone.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        print("Waiting for Pinecone index to be ready...")
        time.sleep(RELAXATION_TIME)

# Provide index
index = pinecone.Index(name=PINECONE_INDEX_NAME)


# Load, split, embed and upsert pdf document content
def f_load_vectorstore(uploaded_files):
    # define the embedding model
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    file_paths = []

    # 1. Upload files and save to disk
    for uploaded_file in uploaded_files:
        # retrieve the filename
        save_path = Path(UPLOAD_DIR) / uploaded_file.filename
        with open(save_path, "wb") as f:
            f.write(uploaded_file.file.read())
        file_paths.append(str(save_path))

    # 2. Split the documents into chunks
    for file_path in file_paths:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # now the splitting part
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100
        )
        chunks = recursive_splitter.split_documents(documents)

        # gather the text content of the chunks for embedding
        texts = [chunk.page_content for chunk in chunks]
        metadata = [chunk.metadata for chunk in chunks]

        # get the IDs for the chunks (we can use the filename and the chunk index to create unique IDs)
        ids = [f"{Path(file_path).stem}-{i}" for i in range(len(chunks))]

        # 3. Embedding the chunks
        logger.info(f"Now embedding chunks ...")
        embeddings = embedding_model.embed_documents(texts)

        # 4. Upsert to Pinecone
        logger.info(f"Now upserting {len(embeddings)} chunks ...")
        with tqdm(total=len(embeddings), desc="Upserting to Pinecone") as pbar:
            index.upsert(vectors=zip(ids, embeddings, metadata))
            pbar.update(len(ids))

        logger.info(
            f"Finished upserting {len(embeddings)} chunks for file: {file_path}"
        )
