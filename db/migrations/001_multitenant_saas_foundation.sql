-- 001 multi-tenant SaaS foundation (Neon / PostgreSQL). Idempotent: safe to re-run.
-- App contract: per request run  SET LOCAL app.tenant_id = '<uuid>';  SET LOCAL app.role = '<ROLE>';
create extension if not exists pgcrypto;

create table if not exists organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references organizations(id) on delete cascade,
  email text not null,
  role text not null check (role in ('SUPER_ADMIN','SUBSCRIBER','COMMUNITY_FREE')),
  created_at timestamptz not null default now()
);
create unique index if not exists users_email_uq on users (lower(email));

create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references organizations(id) on delete cascade,
  plan text not null,
  status text not null default 'inactive',
  current_period_end timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists tool_runs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references organizations(id) on delete cascade,
  user_id uuid references users(id) on delete set null,
  tool text not null,
  status text not null default 'queued',
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists tool_runs_tenant_idx on tool_runs (tenant_id, created_at desc);

-- Public website intake (not tenant-owned).
create table if not exists website_inquiries (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text not null,
  company text,
  interest text,
  message text,
  source text,
  domain text,
  created_at timestamptz not null default now()
);

-- Shared with the outreach tooling. If it already exists, this is a no-op.
create table if not exists suppression_list (
  id bigserial primary key,
  scope text not null,
  value text not null,
  reason text,
  created_at timestamptz not null default now()
);
create unique index if not exists suppression_scope_value_uq on suppression_list (scope, value);

-- Row-Level Security: tenant isolation + SUPER_ADMIN override.
do $$
declare t text;
begin
  foreach t in array array['users','subscriptions','tool_runs'] loop
    execute format('alter table %I enable row level security', t);
    execute format('alter table %I force row level security', t);
    execute format('drop policy if exists tenant_isolation on %I', t);
    execute format($p$create policy tenant_isolation on %I
      using (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
             or current_setting('app.role', true) = 'SUPER_ADMIN')
      with check (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
             or current_setting('app.role', true) = 'SUPER_ADMIN')$p$, t);
  end loop;
end $$;

alter table organizations enable row level security;
alter table organizations force row level security;
drop policy if exists tenant_isolation on organizations;
create policy tenant_isolation on organizations
  using (id = nullif(current_setting('app.tenant_id', true), '')::uuid or current_setting('app.role', true) = 'SUPER_ADMIN')
  with check (current_setting('app.role', true) = 'SUPER_ADMIN');

-- Inquiries: anyone (the worker) may insert; only SUPER_ADMIN may read.
alter table website_inquiries enable row level security;
alter table website_inquiries force row level security;
drop policy if exists inquiry_insert on website_inquiries;
create policy inquiry_insert on website_inquiries for insert with check (true);
drop policy if exists inquiry_admin_read on website_inquiries;
create policy inquiry_admin_read on website_inquiries for select using (current_setting('app.role', true) = 'SUPER_ADMIN');
