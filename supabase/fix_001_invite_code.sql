-- ============================================================
-- Fix 001: 邀请码生成改用内置函数
-- 原因：gen_random_bytes 属 pgcrypto 扩展，不在 search_path=public 内，
--       导致 create_workspace(kind='team') 抛 42883 undefined_function
-- 方案：用 md5(random()) 生成，并剔除易混淆字符 0/O/1/I/L
-- ============================================================

create or replace function public.gen_invite_code()
returns text
language plpgsql
volatile
as $$
declare
  alphabet text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';  -- 去掉 0 O 1 I L
  out_code text := '';
  i int;
begin
  for i in 1..6 loop
    out_code := out_code || substr(alphabet, 1 + floor(random() * length(alphabet))::int, 1);
  end loop;
  return out_code;
end;
$$;


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

  if p_kind = 'team' then
    loop
      i := i + 1;
      v_code := public.gen_invite_code();
      exit when not exists (select 1 from public.workspaces where invite_code = v_code);
      if i > 30 then raise exception 'invite code generation failed'; end if;
    end loop;
  else
    v_code := null;
  end if;

  insert into public.workspaces (name, kind, invite_code, owner_id)
  values (
    coalesce(nullif(trim(p_name),''),
             case when p_kind='team' then '我的团队' else '个人空间' end),
    p_kind, v_code, auth.uid()
  )
  returning * into v_ws;

  insert into public.workspace_members (workspace_id, user_id, role)
  values (v_ws.id, auth.uid(), 'owner')
  on conflict do nothing;

  return v_ws;
end;
$$;


-- 为已存在但缺邀请码的团队空间补码
update public.workspaces
   set invite_code = public.gen_invite_code()
 where kind = 'team' and invite_code is null;


grant execute on function public.gen_invite_code()             to authenticated;
grant execute on function public.create_workspace(text,text)   to authenticated;

-- 通知 PostgREST 重载 schema 缓存
notify pgrst, 'reload schema';
