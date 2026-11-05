-- Feedback submitted from the critterformations.com feedback form.
--
-- This table lives in the shared `maptogpx` Supabase project (ref njzrhztlmvhcpjglnuut),
-- whose migration history is owned by the GoogleMapRouteToGPX repo. So this file is applied
-- directly instead of through `supabase db push` (which would add a migration that repo
-- doesn't know about):
--
--   supabase db query --linked --project-ref njzrhztlmvhcpjglnuut -f supabase/sql/critter_feedback.sql
--
-- Only the critter-feedback Edge Function (service role) reads or writes this table:
-- RLS is enabled with no policies, so anon/authenticated roles have no access.
-- Keep the limits below in sync with supabase/functions/critter-feedback/index.ts.
create table if not exists public.critter_feedback (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  rating smallint check (rating between 1 and 5),
  message text check (char_length(message) <= 2000),
  email text check (char_length(email) <= 320),
  page text check (char_length(page) <= 200),
  lang text check (char_length(lang) <= 16),
  constraint critter_feedback_has_content check (rating is not null or message is not null)
);

alter table public.critter_feedback enable row level security;

revoke all on table public.critter_feedback from anon, authenticated;
