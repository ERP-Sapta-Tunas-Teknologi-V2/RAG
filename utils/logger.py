import time
from utils.supabase_admin import supabase
from utils.cost_calculator import calculate_cost

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
    # finally:
    #     print(f"[LOGGING] background={time.perf_counter() - start:.3f}s")

def log_usage(
    request_id,
    anon_id,
    emb_model,
    llm_model,
    embedding_tokens=0,
    llm_input_tokens=0,
    llm_output_tokens=0
):
    try:
        total_tokens = embedding_tokens + llm_input_tokens + llm_output_tokens

        emb_cost, llm_cost, input_cost, output_cost = calculate_cost(
            emb_model, 
            llm_model, 
            embedding_tokens, 
            llm_input_tokens, 
            llm_output_tokens
        )
        total_cost = emb_cost + llm_cost

        supabase.table("usage_logs").insert({
            "request_id": request_id,
            "anon_id": str(anon_id),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "embedding_model": emb_model,
            "embedding_cost": emb_cost,
            "embedding_tokens": embedding_tokens,
            "llm_model": llm_model,
            "llm_total_cost": llm_cost,
            "llm_input_cost": input_cost,
            "llm_input_tokens": llm_input_tokens,
            "llm_output_cost": output_cost,
            "llm_output_tokens": llm_output_tokens
        }, returning="minimal").execute()

    except Exception as e:
        print(f"[USAGE] failed: {e}")