-- ============================================================
-- Supabase PostgreSQL + pgvector setup
-- ============================================================

-- Enable pgvector
create extension if not exists vector;


-- ============================================================
-- TABLE: documents
-- ============================================================

drop table if exists public.documents;

create table public.documents (
    id bigserial primary key,
    content text,
    metadata jsonb,
    embedding vector(1024)
);


-- ============================================================
-- FULL-TEXT SEARCH
-- ============================================================

alter table public.documents
add column fts tsvector
generated always as (
    to_tsvector('simple', coalesce(content, ''))
) stored;

create index documents_fts_idx
on public.documents
using gin (fts);


-- ============================================================
-- VECTOR SEARCH
-- ============================================================

create or replace function public.match_documents(
    query_embedding vector(1024),
    match_count int default 5
)
returns table (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
language sql
as $$
    select
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) as similarity
    from public.documents
    where documents.embedding is not null
    order by documents.embedding <=> query_embedding
    limit match_count;
$$;


-- ============================================================
-- HYBRID SEARCH
-- Combines:
--   1. Full-text search
--   2. Semantic/vector search
--   3. Reciprocal Rank Fusion (RRF)
-- ============================================================

create or replace function public.hybrid_search(
    query_text text,
    query_embedding vector(1024),
    match_count int default 10,
    full_text_weight float default 1,
    semantic_weight float default 1,
    rrf_k int default 50
)
returns table (
    id bigint,
    content text,
    metadata jsonb,
    embedding vector(1024),
    hybrid_score float
)
language sql
as $$
    with full_text as (
        select
            d.id,
            row_number() over (
                order by ts_rank_cd(
                    d.fts,
                    websearch_to_tsquery('simple', query_text)
                ) desc
            ) as rank_ix
        from public.documents d
        where d.fts @@ websearch_to_tsquery(
            'simple',
            query_text
        )
        order by rank_ix
        limit least(match_count, 30) * 2
    ),

    semantic as (
        select
            d.id,
            row_number() over (
                order by d.embedding <=> query_embedding
            ) as rank_ix
        from public.documents d
        where d.embedding is not null
        order by d.embedding <=> query_embedding
        limit least(match_count, 30) * 2
    ),

    fused as (
        select
            coalesce(ft.id, sem.id) as id,

            coalesce(
                1.0 / (rrf_k + ft.rank_ix),
                0.0
            ) * full_text_weight

            +

            coalesce(
                1.0 / (rrf_k + sem.rank_ix),
                0.0
            ) * semantic_weight

            as hybrid_score

        from full_text ft

        full outer join semantic sem
            on ft.id = sem.id
    )

    select
        d.id,
        d.content,
        d.metadata,
        d.embedding,
        fused.hybrid_score
    from fused
    join public.documents d
        on d.id = fused.id
    order by fused.hybrid_score desc
    limit match_count;
$$;


-- ============================================================
-- SEQUENCE PERMISSION
-- Required for INSERT using BIGSERIAL
-- ============================================================

grant usage, select
on sequence public.documents_id_seq
to anon;


-- ============================================================
-- TABLE PERMISSIONS
-- ============================================================

grant select, insert, update
on public.documents
to anon;


-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

alter table public.documents
enable row level security;


-- INSERT
create policy "Allow insert documents"
on public.documents
for insert
to anon
with check (true);


-- SELECT
create policy "Allow select documents"
on public.documents
for select
to anon
using (true);


-- UPDATE
create policy "Allow update documents"
on public.documents
for update
to anon
using (true)
with check (true);