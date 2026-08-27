from utils.supabase_client import supabase

def log_query(query, anon_id):
    supabase.table("query_logs").insert({
        "query": query,
        "anon_id": str(anon_id)
    }).execute()