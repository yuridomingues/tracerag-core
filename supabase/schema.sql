-- TraceRAG alpha schema.
-- Apply to a dedicated Supabase project. Every table in public has RLS enabled.

create extension if not exists pgcrypto;

create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 2 and 80),
  slug text not null,
  created_at timestamptz not null default now(),
  unique (owner_id, slug)
);

create table if not exists public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'viewer' check (role in ('owner', 'editor', 'viewer')),
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  name text not null check (char_length(name) between 2 and 80),
  slug text not null,
  created_at timestamptz not null default now(),
  unique (workspace_id, slug)
);

create table if not exists public.rag_endpoints (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 100),
  url text not null check (url like 'https://%'),
  question_path text not null default 'question',
  response_text_path text not null default 'answer',
  response_sources_path text,
  auth_header_name text,
  auth_secret_ciphertext text,
  created_at timestamptz not null default now()
);

create table if not exists public.datasets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  name text not null check (char_length(name) between 2 and 100),
  created_at timestamptz not null default now()
);

create table if not exists public.eval_cases (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references public.datasets(id) on delete cascade,
  question text not null check (char_length(question) between 3 and 2000),
  must_include text[] not null default '{}',
  must_not_include text[] not null default '{}',
  expected_sources text[] not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists public.eval_runs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  dataset_id uuid not null references public.datasets(id) on delete restrict,
  endpoint_id uuid not null references public.rag_endpoints(id) on delete restrict,
  baseline_run_id uuid references public.eval_runs(id) on delete set null,
  triggered_by uuid references auth.users(id) on delete set null,
  status text not null default 'queued' check (status in ('queued', 'running', 'completed', 'failed')),
  git_sha text,
  branch text,
  total_cases integer not null default 0 check (total_cases >= 0),
  success_rate numeric,
  keyword_pass_rate numeric,
  source_recall numeric,
  p95_latency_ms numeric,
  gate_passed boolean,
  gate_reasons text[] not null default '{}',
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.projects
  add column if not exists baseline_run_id uuid
  references public.eval_runs(id) on delete set null;

create table if not exists public.eval_results (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.eval_runs(id) on delete cascade,
  case_id uuid not null references public.eval_cases(id) on delete restrict,
  success boolean not null default false,
  http_status integer,
  latency_ms integer,
  response_text text not null default '',
  sources text[] not null default '{}',
  keyword_pass boolean,
  source_recall numeric,
  error text,
  created_at timestamptz not null default now(),
  unique (run_id, case_id)
);

create table if not exists public.project_gate_settings (
  project_id uuid primary key references public.projects(id) on delete cascade,
  min_success_rate numeric not null default 0.95 check (min_success_rate between 0 and 1),
  min_keyword_pass_rate numeric not null default 0.95 check (min_keyword_pass_rate between 0 and 1),
  min_source_recall numeric not null default 0.80 check (min_source_recall between 0 and 1),
  max_success_rate_drop numeric not null default 0.05 check (max_success_rate_drop between 0 and 1),
  max_keyword_pass_rate_drop numeric not null default 0.05 check (max_keyword_pass_rate_drop between 0 and 1),
  max_source_recall_drop numeric not null default 0.10 check (max_source_recall_drop between 0 and 1),
  max_p95_latency_regression_pct numeric not null default 0.50 check (max_p95_latency_regression_pct >= 0),
  updated_at timestamptz not null default now()
);

create table if not exists public.api_keys (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 80),
  key_prefix text not null,
  key_hash text not null unique,
  last_used_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists projects_workspace_idx on public.projects(workspace_id);
create index if not exists endpoints_project_idx on public.rag_endpoints(project_id);
create index if not exists datasets_project_idx on public.datasets(project_id);
create index if not exists eval_cases_dataset_idx on public.eval_cases(dataset_id);
create index if not exists eval_runs_project_created_idx on public.eval_runs(project_id, created_at desc);
create index if not exists eval_results_run_idx on public.eval_results(run_id);
create index if not exists api_keys_project_idx on public.api_keys(project_id);

create schema if not exists private;
revoke all on schema private from public;
revoke all on schema private from anon;
grant usage on schema private to authenticated;

create or replace function private.can_access_workspace(target_workspace uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select (select auth.uid()) is not null and exists (
    select 1 from public.workspaces w
    left join public.workspace_members m
      on m.workspace_id = w.id and m.user_id = (select auth.uid())
    where w.id = target_workspace
      and (w.owner_id = (select auth.uid()) or m.user_id is not null)
  );
$$;

create or replace function private.can_edit_workspace(target_workspace uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select (select auth.uid()) is not null and exists (
    select 1 from public.workspaces w
    left join public.workspace_members m
      on m.workspace_id = w.id and m.user_id = (select auth.uid())
    where w.id = target_workspace
      and (w.owner_id = (select auth.uid()) or m.role in ('owner', 'editor'))
  );
$$;

create or replace function private.is_workspace_owner(target_workspace uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select (select auth.uid()) is not null and exists (
    select 1 from public.workspaces w
    where w.id = target_workspace and w.owner_id = (select auth.uid())
  );
$$;

create or replace function private.can_access_project(target_project uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.projects p
    where p.id = target_project and private.can_access_workspace(p.workspace_id)
  );
$$;

create or replace function private.can_edit_project(target_project uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.projects p
    where p.id = target_project and private.can_edit_workspace(p.workspace_id)
  );
$$;

create or replace function private.can_access_dataset(target_dataset uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.datasets d
    where d.id = target_dataset and private.can_access_project(d.project_id)
  );
$$;

create or replace function private.can_edit_dataset(target_dataset uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.datasets d
    where d.id = target_dataset and private.can_edit_project(d.project_id)
  );
$$;

create or replace function private.can_access_run(target_run uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.eval_runs r
    where r.id = target_run and private.can_access_project(r.project_id)
  );
$$;

create or replace function private.can_edit_run(target_run uuid)
returns boolean language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.eval_runs r
    where r.id = target_run and private.can_edit_project(r.project_id)
  );
$$;

revoke all on function private.can_access_workspace(uuid) from public, anon;
revoke all on function private.can_edit_workspace(uuid) from public, anon;
revoke all on function private.is_workspace_owner(uuid) from public, anon;
revoke all on function private.can_access_project(uuid) from public, anon;
revoke all on function private.can_edit_project(uuid) from public, anon;
revoke all on function private.can_access_dataset(uuid) from public, anon;
revoke all on function private.can_edit_dataset(uuid) from public, anon;
revoke all on function private.can_access_run(uuid) from public, anon;
revoke all on function private.can_edit_run(uuid) from public, anon;

grant execute on function private.can_access_workspace(uuid) to authenticated;
grant execute on function private.can_edit_workspace(uuid) to authenticated;
grant execute on function private.is_workspace_owner(uuid) to authenticated;
grant execute on function private.can_access_project(uuid) to authenticated;
grant execute on function private.can_edit_project(uuid) to authenticated;
grant execute on function private.can_access_dataset(uuid) to authenticated;
grant execute on function private.can_edit_dataset(uuid) to authenticated;
grant execute on function private.can_access_run(uuid) to authenticated;
grant execute on function private.can_edit_run(uuid) to authenticated;

create or replace function private.add_workspace_owner()
returns trigger language plpgsql security definer
set search_path = ''
as $$
begin
  insert into public.workspace_members(workspace_id, user_id, role)
  values (new.id, new.owner_id, 'owner')
  on conflict (workspace_id, user_id) do update set role = 'owner';
  return new;
end;
$$;

revoke all on function private.add_workspace_owner() from public, anon, authenticated;

drop trigger if exists workspace_owner_membership on public.workspaces;
create trigger workspace_owner_membership
after insert on public.workspaces
for each row execute function private.add_workspace_owner();

alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.projects enable row level security;
alter table public.rag_endpoints enable row level security;
alter table public.datasets enable row level security;
alter table public.eval_cases enable row level security;
alter table public.eval_runs enable row level security;
alter table public.eval_results enable row level security;
alter table public.project_gate_settings enable row level security;
alter table public.api_keys enable row level security;

drop policy if exists workspaces_select on public.workspaces;
create policy workspaces_select on public.workspaces for select to authenticated
using (private.can_access_workspace(id));
drop policy if exists workspaces_insert on public.workspaces;
create policy workspaces_insert on public.workspaces for insert to authenticated
with check (owner_id = (select auth.uid()));
drop policy if exists workspaces_update on public.workspaces;
create policy workspaces_update on public.workspaces for update to authenticated
using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));
drop policy if exists workspaces_delete on public.workspaces;
create policy workspaces_delete on public.workspaces for delete to authenticated
using (owner_id = (select auth.uid()));

drop policy if exists members_select on public.workspace_members;
create policy members_select on public.workspace_members for select to authenticated
using (private.can_access_workspace(workspace_id));
drop policy if exists members_insert on public.workspace_members;
create policy members_insert on public.workspace_members for insert to authenticated
with check (private.is_workspace_owner(workspace_id));
drop policy if exists members_update on public.workspace_members;
create policy members_update on public.workspace_members for update to authenticated
using (private.is_workspace_owner(workspace_id)) with check (private.is_workspace_owner(workspace_id));
drop policy if exists members_delete on public.workspace_members;
create policy members_delete on public.workspace_members for delete to authenticated
using (private.is_workspace_owner(workspace_id) and user_id <> (select auth.uid()));

drop policy if exists projects_select on public.projects;
create policy projects_select on public.projects for select to authenticated
using (private.can_access_project(id));
drop policy if exists projects_insert on public.projects;
create policy projects_insert on public.projects for insert to authenticated
with check (private.can_edit_workspace(workspace_id));
drop policy if exists projects_update on public.projects;
create policy projects_update on public.projects for update to authenticated
using (private.can_edit_project(id)) with check (private.can_edit_workspace(workspace_id));
drop policy if exists projects_delete on public.projects;
create policy projects_delete on public.projects for delete to authenticated
using (private.can_edit_project(id));

drop policy if exists endpoints_all on public.rag_endpoints;
create policy endpoints_all on public.rag_endpoints for all to authenticated
using (private.can_access_project(project_id)) with check (private.can_edit_project(project_id));
drop policy if exists datasets_all on public.datasets;
create policy datasets_all on public.datasets for all to authenticated
using (private.can_access_project(project_id)) with check (private.can_edit_project(project_id));
drop policy if exists eval_cases_all on public.eval_cases;
create policy eval_cases_all on public.eval_cases for all to authenticated
using (private.can_access_dataset(dataset_id)) with check (private.can_edit_dataset(dataset_id));
drop policy if exists eval_runs_all on public.eval_runs;
create policy eval_runs_all on public.eval_runs for all to authenticated
using (private.can_access_project(project_id)) with check (private.can_edit_project(project_id));
drop policy if exists eval_results_all on public.eval_results;
create policy eval_results_all on public.eval_results for all to authenticated
using (private.can_access_run(run_id)) with check (private.can_edit_run(run_id));
drop policy if exists gate_settings_all on public.project_gate_settings;
create policy gate_settings_all on public.project_gate_settings for all to authenticated
using (private.can_access_project(project_id)) with check (private.can_edit_project(project_id));
drop policy if exists api_keys_all on public.api_keys;
create policy api_keys_all on public.api_keys for all to authenticated
using (private.can_access_project(project_id)) with check (private.can_edit_project(project_id));

revoke all on all tables in schema public from anon;
grant select, insert, update, delete on
  public.workspaces, public.workspace_members, public.projects,
  public.rag_endpoints, public.datasets, public.eval_cases,
  public.eval_runs, public.eval_results, public.project_gate_settings,
  public.api_keys
to authenticated;
