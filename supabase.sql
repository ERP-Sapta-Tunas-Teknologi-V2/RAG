-- TABLE: documents

create extension if not exists vector;

drop table if exists public.documents;

create table public.documents (
    id bigserial primary key,
    content text,
    metadata jsonb,
    document_id text not null,
    chunk_index int not null,
    fingerprint text not null,
    embedding vector(1024)
);

create unique index documents_document_chunk_unique
on public.documents(document_id, chunk_index);

alter table public.documents
add column fts tsvector
generated always as (
    to_tsvector('simple', coalesce(content, ''))
) stored;

create index documents_fts_idx
on public.documents
using gin (fts);

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

grant usage, select
on sequence public.documents_id_seq
to anon;

grant select, insert, update, delete
on public.documents
to anon;

alter table public.documents
enable row level security;

create policy "Allow insert documents"
on public.documents
for insert
to anon
with check (true);

create policy "Allow select documents"
on public.documents
for select
to anon
using (true);

create policy "Allow update documents"
on public.documents
for update
to anon
using (true)
with check (true);

create policy "Allow delete documents"
on public.documents
for delete
to anon
using (true);

-- TABLE: query_logs

drop table if exists public.query_logs;

create table public.query_logs (
    id bigint generated always as identity primary key,
    query text not null,
    timestamp timestamptz not null default now(),
    anon_id uuid not null
);