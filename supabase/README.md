# Supabase 后端说明

本目录是青甘大环线记账台的云端后端（账号鉴权 + 团队共享 + 私密个人空间 + 实时同步）。

## 为什么要重做同步

老版本用 `textdb.online` 无鉴权 JSON 存储，`workspaceId` 是**每台设备本地随机生成**的：

```js
// 老代码（已删除）
var existingId = getLSWorkspaceId();
if (existingId) { state.workspaceId = existingId; }
else { state.workspaceId = genWorkspaceId(); }  // ← 手机和电脑各生成一个，永远同步不到一起
```

结果就是电脑改了团队名，手机压根在读另一份文档 —— 这就是"假同步"的根源。

现在改成：**登录 → `my_workspaces()` 返回同一个 workspace UUID → 所有设备读写同一份数据**。

## 文件说明

| 文件 | 作用 |
|---|---|
| `schema.sql` | 完整表结构 + RLS 策略 + RPC 函数 + Realtime（63 条语句） |
| `fix_001_invite_code.sql` | 修复邀请码生成（`gen_random_bytes` 在 `search_path=public` 下不可见） |
| `run_sql.py` | 用 pg8000 执行 SQL 文件（密码从环境变量读，不入库） |
| `verify.py` | 27 项端到端测试（注册/登录/邀请/隔离/冲突/改名） |
| `client_module.js` | 前端 Supabase 客户端源码（已内联进 `index.html`） |
| `patch_*.py` | 把 `index.html` 从 textdb 迁移到 Supabase 的补丁脚本（记录改动过程） |

## 数据模型

```
auth.users              Supabase 内置用户表
  └─ profiles           昵称等资料（触发器自动创建）
workspaces              空间（team 共享 / personal 私密）
  ├─ invite_code        团队邀请码，6 位，去掉了易混淆的 0O1IL
  └─ workspace_members  谁在哪个空间
records                 所有业务数据，(workspace_id, id) 主键
  ├─ kind               expense|prepaid|prepItem|outfit|todo|prepTodo|member|meta
  ├─ payload jsonb      原始对象
  └─ ts bigint          毫秒时间戳，用于冲突解决（新者胜）
```

## 关键设计

**1. 邮箱免验证 —— 双保险**

后台已关掉 `Confirm email`，同时数据库里还有个触发器兜底：

```sql
create trigger trg_auto_confirm_email before insert on auth.users
  for each row execute function public.auto_confirm_email();
```

即使有人误开了后台开关，注册也不会被卡住。免费版每小时只能发 2 封邮件，4 个人注册必死锁。

**2. RLS 防递归**

`workspace_members` 的策略如果直接查 `workspace_members` 会无限递归，用 `SECURITY DEFINER` 函数打断：

```sql
create function public.is_ws_member(ws uuid) returns boolean
  language sql security definer set search_path = public stable as $$
  select exists(select 1 from public.workspace_members
                where workspace_id = ws and user_id = auth.uid());
$$;
```

**3. 个人空间的隐私**

个人空间也存在同一张 `records` 表里，靠 RLS 保证只有本人能读写。已实测：队友读返回 0 条，写返回 HTTP 400。

**4. 空间名的唯一权威来源是 `workspaces.name`**

早期版本还往 `records` 的 `meta` 里冗余写了一份 `teamName`，结果过期副本会把别人的改名顶掉 —— 又制造了一次"假同步"。现已移除，改名只走 `workspaces` 表 + Realtime 推送。

**5. Realtime 订阅三张表**

只订阅 `records` 会漏掉改名和成员变化：

```js
postgres_changes:[
  {event:'*',schema:'public',table:'records',          filter:'workspace_id=eq.'+wsId},
  {event:'*',schema:'public',table:'workspaces',       filter:'id=eq.'+wsId},
  {event:'*',schema:'public',table:'workspace_members',filter:'workspace_id=eq.'+wsId}
]
```

另有 5 次轮询校验一次空间名作为兜底（WebSocket 可能被网络环境掐断）。

## 运维命令

连接信息（新项目 `db.<ref>.supabase.co` 没有 IPv4 A 记录，必须走 pooler）：

```
host = aws-0-ap-south-1.pooler.supabase.com
port = 5432
user = postgres.cxvwynfwoppyzjopzpkz
db   = postgres
```

执行 SQL：

```bash
SUPA_DB_PW='你的数据库密码' python3 supabase/run_sql.py supabase/schema.sql
```

跑端到端测试：

```bash
python3 supabase/verify.py
```

依赖：`pip3 install pg8000`（纯 Python，不需要 libpq/psql）

## 安全

- `SUPABASE_ANON_KEY`（publishable key）内嵌在前端是**设计如此**，安全性由 RLS 保证，可以提交
- **数据库密码绝不入库**，只通过 `SUPA_DB_PW` 环境变量传入
- 建议在开发完成后到 Supabase 后台 Settings → Database 重置一次数据库密码
