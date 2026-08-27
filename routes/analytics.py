from flask import Blueprint, Response
from sync.export_logs import export_query_logs

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/logs/export", methods=["GET"])
def export_logs():
    csv_data = export_query_logs()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=query_logs.csv"}
    )