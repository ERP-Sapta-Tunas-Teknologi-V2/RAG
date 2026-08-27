import time
from utils.supabase_client import supabase

def log_query(query, anon_id):
    start = time.perf_counter()
    try:
        supabase.table("query_logs").insert({
            "query": query,
            "anon_id": str(anon_id)
        }).execute()
    except Exception as e:
        print(f"[LOGGING] failed: {e}")
    finally:
        print(f"[LOGGING] background={time.perf_counter() - start:.3f}s")