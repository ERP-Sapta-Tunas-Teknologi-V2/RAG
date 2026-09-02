import csv
import io
from sync.export_logs import export_query_logs

def mock_result(rows):
    class Result:
        data = rows

    return Result()

class MockQuery:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *args):
        return self

    def order(self, *args, **kwargs):
        return self

    def gte(self, *args):
        return self

    def lt(self, *args):
        return self

    def execute(self):
        return mock_result(self.rows)

class MockSupabase:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        assert name == "query_logs"
        return MockQuery(self.rows)

def test_csv_format(monkeypatch):
    rows = [
        {
            "id": 1,
            "query": "Apa layanan perusahaan?",
            "timestamp": "2026-08-27T10:00:00+07:00"
        },
        {
            "id": 2,
            "query": "Apa visi, misi, dan nilai perusahaan?",
            "timestamp": "2026-08-27T11:00:00+07:00"
        }
    ]

    monkeypatch.setattr("sync.export_logs.supabase", MockSupabase(rows))

    csv_data = export_query_logs()
    reader = csv.reader(io.StringIO(csv_data.lstrip("\ufeff")))
    rows = list(reader)

    assert rows[0] == ["id", "query", "timestamp"]
    assert len(rows) == 3
    assert rows[1][1] == "Apa layanan perusahaan?"
    assert rows[2][1] == "Apa visi, misi, dan nilai perusahaan?"

def test_csv_utf8(monkeypatch):
    rows = [
        {
            "id": 1,
            "query": "Bagaimana kebijakan perusahaan di Indonesia?",
            "timestamp": "2026-08-27T10:00:00+07:00"
        },
        {
            "id": 2,
            "query": "Apa hubungan budaya kerja dengan kinerja?",
            "timestamp": "2026-08-27T11:00:00+07:00"
        }
    ]

    monkeypatch.setattr("sync.export_logs.supabase", MockSupabase(rows))

    csv_data = export_query_logs()
    csv_data.encode("utf-8")

    assert "Indonesia" in csv_data
    assert "budaya kerja" in csv_data

def test_csv_special_characters(monkeypatch):
    rows = [
        {
            "id": 1,
            "query": 'Apa "visi, misi" perusahaan?',
            "timestamp": "2026-08-27T10:00:00+07:00"
        },
        {
            "id": 2,
            "query": "Apa kebijakan perusahaan?\nJelaskan secara singkat.",
            "timestamp": "2026-08-27T11:00:00+07:00"
        }
    ]

    monkeypatch.setattr("sync.export_logs.supabase", MockSupabase(rows))

    csv_data = export_query_logs()
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)

    assert len(rows) == 3
    assert rows[1][1] == 'Apa "visi, misi" perusahaan?'
    assert rows[2][1] == "Apa kebijakan perusahaan?\nJelaskan secara singkat."

def test_date_filter(monkeypatch):
    rows = [
        {
            "id": 1,
            "query": "Query test",
            "timestamp": "2026-08-27T10:00:00+07:00"
        }
    ]

    query = MockQuery(rows)
    monkeypatch.setattr("sync.export_logs.supabase", MockSupabase(rows))
    export_query_logs("2026-08-01T00:00:00+07:00", "2026-08-28T00:00:00+07:00")

    assert query is not None

def test_empty_export(monkeypatch):
    monkeypatch.setattr("sync.export_logs.supabase", MockSupabase([]))

    csv_data = export_query_logs()
    reader = list(csv.reader(io.StringIO(csv_data.lstrip("\ufeff"))))

    assert reader == [["id", "query", "timestamp"]]

def test_large_export(monkeypatch):
    rows = [
        {
            "id": i,
            "query": f"Query test {i}",
            "timestamp": "2026-08-27T10:00:00+07:00"
        }
        for i in range(10_000)
    ]

    monkeypatch.setattr("sync.export_logs.supabase", MockSupabase(rows))

    csv_data = export_query_logs()
    rows = list(csv.reader(io.StringIO(csv_data.lstrip("\ufeff"))))

    assert len(rows) == 10_001