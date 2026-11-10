-- "Can't pass this stage?" reports from the formation cards on critterformations.com.
--
-- Lives in the shared `maptogpx` Supabase project (ref njzrhztlmvhcpjglnuut), next to
-- critter_feedback. Apply directly, not through `supabase db push` (see critter_feedback.sql):
--
--   supabase db query --linked --project-ref njzrhztlmvhcpjglnuut -f supabase/sql/critter_stage_reports.sql
--
-- Only the critter-feedback Edge Function (service role) reads or writes this table:
-- RLS is enabled with no policies, so anon/authenticated roles have no access.
-- Keep the limits below in sync with supabase/functions/critter-feedback/index.ts.
create table if not exists public.critter_stage_reports (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  chapter smallint not null check (chapter between 1 and 80),
  -- Null when a multi-stage card was reported with "not sure".
  stage text check (stage ~ '^[0-9]{1,2}-[0-9]{1,2}$'),
  formation_id text not null check (char_length(formation_id) <= 64),
  page text check (char_length(page) <= 200),
  lang text check (char_length(lang) <= 16)
);

create index if not exists critter_stage_reports_stage_idx on public.critter_stage_reports (chapter, stage);

alter table public.critter_stage_reports enable row level security;

revoke all on table public.critter_stage_reports from anon, authenticated;
