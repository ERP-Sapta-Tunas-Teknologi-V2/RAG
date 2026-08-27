import csv
import io
from utils.supabase_client import supabase

def export_query_logs():
    result = (
        supabase.table("query_logs")
        .select("id,query,timestamp")
        .order("timestamp", desc=True)
        .execute()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "query", "timestamp"])

    for row in result.data or []:
        writer.writerow([
            row["id"],
            row["query"],
            row["timestamp"]
        ])

    return output.getvalue()