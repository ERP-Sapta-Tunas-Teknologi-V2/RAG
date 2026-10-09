import time
from utils.supabase_admin import supabase

def log_query(query, anon_id):
    start = time.perf_counter()
    try:
        supabase.table("query_logs").insert(
            {
                "query": query,
                "anon_id": str(anon_id)
            },
            returning="minimal"
        ).execute()
    except Exception as e:
        print(f"[LOGGING] failed: {e}")