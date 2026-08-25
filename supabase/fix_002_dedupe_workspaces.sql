-- ============================================================
-- fix_002: 修复空间重复创建（并发 ensureWorkspaces 竞态）
-- 症状：同一用户出现两个「我的个人空间」和两个「青甘四人组」
-- 原因：两个设备/标签页同时首次登录，各自都发现"没有空间"就各建一个
-- ============================================================

-- 1. 合并重复的个人空间：把记录搬到最早那个，删掉多余的
do $$
declare
  r record;
  keep_id uuid;
begin
  for r in
    select owner_id, kind, min(created_at) as first_at, count(*) as n
    from public.workspaces
    where kind = 'personal'
    group by owner_id, kind
    having count(*) > 1
  loop
    -- 保留记录数最多的那个（数据最全），并列时保留最早创建的
    select id into keep_id
    from public.workspaces w
    where w.owner_id = r.owner_id and w.kind = 'personal'
    order by (select count(*) from public.records rc where rc.workspace_id = w.id) desc,
             w.created_at asc
    limit 1;

    -- 把其他个人空间的记录搬过来（冲突时保留 ts 更新的）
    insert into public.records (workspace_id, id, kind, payload, ts, deleted, updated_by, updated_at)
    select keep_id, rc.id, rc.kind, rc.payload, rc.ts, rc.deleted, rc.updated_by, rc.updated_at
    from public.records rc
    join public.workspaces w2 on w2.id = rc.workspace_id
    where w2.owner_id = r.owner_id and w2.kind = 'personal' and w2.id <> keep_id
    on conflict (workspace_id, id) do update
      set payload = excluded.payload, ts = excluded.ts, deleted = excluded.deleted
      where excluded.ts > public.records.ts;

    -- 删掉多余的个人空间
    delete from public.workspaces
    where owner_id = r.owner_id and kind = 'personal' and id <> keep_id;

    raise notice '合并个人空间: owner=% 保留=%', r.owner_id, keep_id;
  end loop;
end $$;

-- 2. 合并同名且都是自己创建的空团队（记录数为 0 的重复团队直接删）
do $$
declare r record;
begin
  for r in
    select w.id, w.owner_id, w.name
    from public.workspaces w
    where w.kind = 'team'
      and (select count(*) from public.records rc where rc.workspace_id = w.id) = 0
      and (select count(*) from public.workspace_members m where m.workspace_id = w.id) <= 1
      and exists (
        select 1 from public.workspaces w2
        where w2.owner_id = w.owner_id and w2.kind = 'team'
          and w2.name = w.name and w2.id <> w.id
          and (select count(*) from public.records rc2 where rc2.workspace_id = w2.id) > 0
      )
  loop
    delete from public.workspaces where id = r.id;
    raise notice '删除空的重复团队: % (%)', r.name, r.id;
  end loop;
end $$;

-- 3. 加唯一约束：一个用户只能有一个个人空间（从数据库层面根治竞态）
create unique index if not exists uniq_personal_ws_per_owner
  on public.workspaces (owner_id)
  where kind = 'personal';

-- 4. create_workspace 改为幂等：个人空间已存在时直接返回已有的，不再新建
create or replace function public.create_workspace(p_name text, p_kind text)
returns public.workspaces
language plpgsql security definer set search_path = public as $$
declare
  v_ws public.workspaces;
  v_code text;
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'not authenticated';
  end if;
  if p_kind not in ('team','personal') then
    raise exception 'invalid kind: %', p_kind;
  end if;

  -- 个人空间幂等：已有就直接返回，避免并发重复创建
  if p_kind = 'personal' then
    select * into v_ws from public.workspaces
    where owner_id = v_uid and kind = 'personal'
    order by created_at asc limit 1;
    if found then
      return v_ws;
    end if;
  end if;

  if p_kind = 'team' then
    -- 生成不重复的邀请码，最多试 20 次
    for i in 1..20 loop
      v_code := public.gen_invite_code();
      exit when not exists (select 1 from public.workspaces where invite_code = v_code);
      v_code := null;
    end loop;
    if v_code is null then
      raise exception 'failed to generate unique invite code';
    end if;
  else
    v_code := null;
  end if;

  insert into public.workspaces (name, kind, invite_code, owner_id)
  values (coalesce(nullif(trim(p_name),''), case when p_kind='team' then '我的团队' else '我的个人空间' end),
          p_kind, v_code, v_uid)
  returning * into v_ws;

  insert into public.workspace_members (workspace_id, user_id, role)
  values (v_ws.id, v_uid, 'owner')
  on conflict (workspace_id, user_id) do nothing;

  return v_ws;
exception
  -- 并发情况下唯一索引冲突：返回已存在的那个
  when unique_violation then
    select * into v_ws from public.workspaces
    where owner_id = v_uid and kind = p_kind
    order by created_at asc limit 1;
    if found then return v_ws; end if;
    raise;
end;
$$;

grant execute on function public.create_workspace(text, text) to authenticated;

notify pgrst, 'reload schema';
