-- ============================================================
-- 青甘旅行记账台 · Supabase Schema v1
-- 目标：真实账号鉴权 + 团队共享空间 + 私密个人空间 + 实时同步
-- ============================================================

-- ---------- 0. 关闭邮箱验证（数据库层实现，无需后台操作） ----------
-- 新注册用户自动标记邮箱已确认，注册后可立即用密码登录
create or replace function public.auto_confirm_email()
returns trigger
language plpgsql
security definer
as $$
begin
  if new.email_confirmed_at is null then
    new.email_confirmed_at := now();
  end if;
  return new;
end;
$$;

drop trigger if exists trg_auto_confirm_email on auth.users;
create trigger trg_auto_confirm_email
  before insert on auth.users
  for each row execute function public.auto_confirm_email();


-- ---------- 1. 用户资料 ----------
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  nickname    text not null default '旅行者',
  color_idx   int  not null default 0,
  created_at  timestamptz not null default now()
);

-- 注册时自动创建资料，昵称优先取 user_metadata.nickname，否则取邮箱前缀
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.profiles (id, nickname)
  values (
    new.id,
    coalesce(
      nullif(new.raw_user_meta_data->>'nickname', ''),
      split_part(new.email, '@', 1)
    )
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists trg_handle_new_user on auth.users;
create trigger trg_handle_new_user
  after insert on auth.users
  for each row execute function public.handle_new_user();


-- ---------- 2. 空间（团队 / 个人） ----------
create table if not exists public.workspaces (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  kind        text not null check (kind in ('team','personal')),
  invite_code text unique,
  owner_id    uuid not null references auth.users(id) on delete cascade,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists idx_workspaces_owner on public.workspaces(owner_id);


-- ---------- 3. 成员关系 ----------
create table if not exists public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id      uuid not null references auth.users(id) on delete cascade,
  role         text not null default 'member' check (role in ('owner','member')),
  joined_at    timestamptz not null default now(),
  primary key (workspace_id, user_id)
);
create index if not exists idx_wm_user on public.workspace_members(user_id);


-- ---------- 4. 数据记录（统一存储，kind 区分类型） ----------
-- kind: expense | prepItem | prepaid | outfit | todo | prepTodo | member | meta
create table if not exists public.records (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  id           text not null,
  kind         text not null,
  payload      jsonb not null default '{}'::jsonb,
  ts           bigint not null default (extract(epoch from now())*1000)::bigint,
  deleted      boolean not null default false,
  updated_by   uuid references auth.users(id) on delete set null,
  updated_at   timestamptz not null default now(),
  primary key (workspace_id, id)
);
create index if not exists idx_records_ws_kind on public.records(workspace_id, kind);
create index if not exists idx_records_ws_ts   on public.records(workspace_id, ts desc);


-- ---------- 5. 权限判定辅助函数（SECURITY DEFINER 避免 RLS 递归） ----------
create or replace function public.is_ws_member(ws uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists(
    select 1 from public.workspace_members
    where workspace_id = ws and user_id = auth.uid()
  );
$$;


-- ---------- 6. 开启 RLS ----------
alter table public.profiles          enable row level security;
alter table public.workspaces        enable row level security;
alter table public.workspace_members enable row level security;
alter table public.records           enable row level security;


-- ---------- 7. RLS 策略：profiles ----------
drop policy if exists p_profiles_select on public.profiles;
create policy p_profiles_select on public.profiles
  for select using (
    id = auth.uid()
    or exists (
      select 1
      from public.workspace_members m1
      join public.workspace_members m2 on m1.workspace_id = m2.workspace_id
      where m1.user_id = auth.uid() and m2.user_id = public.profiles.id
    )
  );

drop policy if exists p_profiles_update on public.profiles;
create policy p_profiles_update on public.profiles
  for update using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists p_profiles_insert on public.profiles;
create policy p_profiles_insert on public.profiles
  for insert with check (id = auth.uid());


-- ---------- 8. RLS 策略：workspaces ----------
drop policy if exists p_ws_select on public.workspaces;
create policy p_ws_select on public.workspaces
  for select using (owner_id = auth.uid() or public.is_ws_member(id));

drop policy if exists p_ws_insert on public.workspaces;
create policy p_ws_insert on public.workspaces
  for insert with check (owner_id = auth.uid());

drop policy if exists p_ws_update on public.workspaces;
create policy p_ws_update on public.workspaces
  for update using (owner_id = auth.uid() or public.is_ws_member(id))
  with check  (owner_id = auth.uid() or public.is_ws_member(id));

drop policy if exists p_ws_delete on public.workspaces;
create policy p_ws_delete on public.workspaces
  for delete using (owner_id = auth.uid());


-- ---------- 9. RLS 策略：workspace_members ----------
drop policy if exists p_wm_select on public.workspace_members;
create policy p_wm_select on public.workspace_members
  for select using (user_id = auth.uid() or public.is_ws_member(workspace_id));

drop policy if exists p_wm_insert on public.workspace_members;
create policy p_wm_insert on public.workspace_members
  for insert with check (
    user_id = auth.uid()
    or exists (select 1 from public.workspaces w
               where w.id = workspace_id and w.owner_id = auth.uid())
  );

drop policy if exists p_wm_delete on public.workspace_members;
create policy p_wm_delete on public.workspace_members
  for delete using (
    user_id = auth.uid()
    or exists (select 1 from public.workspaces w
               where w.id = workspace_id and w.owner_id = auth.uid())
  );


-- ---------- 10. RLS 策略：records（核心数据隔离） ----------
drop policy if exists p_rec_select on public.records;
create policy p_rec_select on public.records
  for select using (public.is_ws_member(workspace_id));

drop policy if exists p_rec_insert on public.records;
create policy p_rec_insert on public.records
  for insert with check (public.is_ws_member(workspace_id));

drop policy if exists p_rec_update on public.records;
create policy p_rec_update on public.records
  for update using (public.is_ws_member(workspace_id))
  with check  (public.is_ws_member(workspace_id));

drop policy if exists p_rec_delete on public.records;
create policy p_rec_delete on public.records
  for delete using (public.is_ws_member(workspace_id));


-- ---------- 11. 创建空间（自动生成邀请码 + 自动加入成员） ----------
create or replace function public.create_workspace(p_name text, p_kind text)
returns public.workspaces
language plpgsql
security definer
set search_path = public
as $$
declare
  v_ws   public.workspaces;
  v_code text;
  i int := 0;
begin
  if auth.uid() is null then
    raise exception 'not authenticated';
  end if;
  if p_kind not in ('team','personal') then
    raise exception 'invalid kind';
  end if;

  -- 个人空间不需要邀请码；团队空间生成 6 位易读邀请码
  if p_kind = 'team' then
    loop
      i := i + 1;
      v_code := upper(
        substr(translate(encode(gen_random_bytes(8),'base64'),'+/=OIl01','ABCDEFG'), 1, 6)
      );
      exit when not exists (select 1 from public.workspaces where invite_code = v_code);
      if i > 20 then raise exception 'code generation failed'; end if;
    end loop;
  else
    v_code := null;
  end if;

  insert into public.workspaces (name, kind, invite_code, owner_id)
  values (coalesce(nullif(trim(p_name),''), case when p_kind='team' then '我的团队' else '个人空间' end),
          p_kind, v_code, auth.uid())
  returning * into v_ws;

  insert into public.workspace_members (workspace_id, user_id, role)
  values (v_ws.id, auth.uid(), 'owner')
  on conflict do nothing;

  return v_ws;
end;
$$;


-- ---------- 12. 凭邀请码加入团队 ----------
create or replace function public.join_workspace(p_code text)
returns public.workspaces
language plpgsql
security definer
set search_path = public
as $$
declare
  v_ws public.workspaces;
begin
  if auth.uid() is null then
    raise exception 'not authenticated';
  end if;

  select * into v_ws from public.workspaces
  where invite_code = upper(trim(p_code)) and kind = 'team';

  if v_ws.id is null then
    raise exception '邀请码无效';
  end if;

  insert into public.workspace_members (workspace_id, user_id, role)
  values (v_ws.id, auth.uid(), 'member')
  on conflict (workspace_id, user_id) do nothing;

  return v_ws;
end;
$$;


-- ---------- 13. 我的空间列表（带成员数） ----------
create or replace function public.my_workspaces()
returns table (
  id uuid, name text, kind text, invite_code text,
  owner_id uuid, is_owner boolean, member_count bigint, created_at timestamptz
)
language sql
security definer
set search_path = public
stable
as $$
  select w.id, w.name, w.kind, w.invite_code, w.owner_id,
         (w.owner_id = auth.uid()) as is_owner,
         (select count(*) from public.workspace_members m where m.workspace_id = w.id) as member_count,
         w.created_at
  from public.workspaces w
  join public.workspace_members me on me.workspace_id = w.id and me.user_id = auth.uid()
  order by w.kind desc, w.created_at asc;
$$;


-- ---------- 14. 空间成员列表（含昵称） ----------
create or replace function public.ws_members(p_ws uuid)
returns table (user_id uuid, nickname text, role text, joined_at timestamptz)
language sql
security definer
set search_path = public
stable
as $$
  select m.user_id, coalesce(p.nickname,'旅行者'), m.role, m.joined_at
  from public.workspace_members m
  left join public.profiles p on p.id = m.user_id
  where m.workspace_id = p_ws
    and exists (select 1 from public.workspace_members x
                where x.workspace_id = p_ws and x.user_id = auth.uid())
  order by m.joined_at asc;
$$;


-- ---------- 15. 批量写入记录（幂等 upsert，_ts 新的胜出） ----------
create or replace function public.push_records(p_ws uuid, p_records jsonb)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  n int := 0;
begin
  if not public.is_ws_member(p_ws) then
    raise exception 'no access to workspace';
  end if;

  insert into public.records (workspace_id, id, kind, payload, ts, deleted, updated_by, updated_at)
  select p_ws,
         r->>'id',
         r->>'kind',
         coalesce(r->'payload','{}'::jsonb),
         coalesce((r->>'ts')::bigint, (extract(epoch from now())*1000)::bigint),
         coalesce((r->>'deleted')::boolean, false),
         auth.uid(),
         now()
  from jsonb_array_elements(p_records) r
  where r->>'id' is not null and r->>'kind' is not null
  on conflict (workspace_id, id) do update
    set payload    = excluded.payload,
        kind       = excluded.kind,
        ts         = excluded.ts,
        deleted    = excluded.deleted,
        updated_by = excluded.updated_by,
        updated_at = now()
    where excluded.ts >= public.records.ts;

  get diagnostics n = row_count;

  update public.workspaces set updated_at = now() where id = p_ws;
  return n;
end;
$$;


-- ---------- 16. 开启 Realtime 实时推送 ----------
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname='supabase_realtime' and schemaname='public' and tablename='records'
  ) then
    alter publication supabase_realtime add table public.records;
  end if;
  if not exists (
    select 1 from pg_publication_tables
    where pubname='supabase_realtime' and schemaname='public' and tablename='workspaces'
  ) then
    alter publication supabase_realtime add table public.workspaces;
  end if;
exception when others then
  raise notice 'realtime setup skipped: %', sqlerrm;
end $$;

alter table public.records    replica identity full;
alter table public.workspaces replica identity full;


-- ---------- 17. 授权给 API 角色 ----------
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on public.profiles, public.workspaces,
      public.workspace_members, public.records to authenticated;
grant execute on function public.create_workspace(text,text) to authenticated;
grant execute on function public.join_workspace(text)        to authenticated;
grant execute on function public.my_workspaces()             to authenticated;
grant execute on function public.ws_members(uuid)            to authenticated;
grant execute on function public.push_records(uuid,jsonb)    to authenticated;
grant execute on function public.is_ws_member(uuid)          to authenticated;
