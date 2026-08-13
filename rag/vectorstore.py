# Hubungkan LangChain dengan Supabase

from supabase.client import create_client
from langchain_community.vectorstores import SupabaseVectorStore

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

vectorstore = SupabaseVectorStore(
    client=supabase_client,
    embedding=embeddings,
    table_name="documents",
    query_name="match_documents",
)