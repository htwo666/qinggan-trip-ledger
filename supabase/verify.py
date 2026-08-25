#!/usr/bin/env python3
"""End-to-end verification of Supabase backend via REST API (as the browser would)."""
import json, urllib.request, urllib.error, time, sys

URL  = "https://cxvwynfwoppyzjopzpkz.supabase.co"
ANON = "sb_publishable_tL1-YiaZ0AJcVCpqCt5d8A_p91RFmYJ"

def call(path, method="GET", body=None, token=None, prefer=None):
    req = urllib.request.Request(URL + path, method=method)
    req.add_header("apikey", ANON)
    req.add_header("Authorization", "Bearer " + (token or ANON))
    req.add_header("Content-Type", "application/json")
    if prefer:
        req.add_header("Prefer", prefer)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=25) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw

def signup(email, pw, nickname):
    return call("/auth/v1/signup", "POST",
                {"email": email, "password": pw, "data": {"nickname": nickname}})

def login(email, pw):
    return call("/auth/v1/token?grant_type=password", "POST",
                {"email": email, "password": pw})

results = []
def check(name, cond, extra=""):
    results.append((name, cond))
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"  {extra}" if extra else ""))

stamp = str(int(time.time()))
u1 = f"qg_owner_{stamp}@gmail.com"
u2 = f"qg_mate_{stamp}@gmail.com"
PW = "TripTest2026!"

def user_obj(r):
    """signup 可能直接返回 user，也可能返回 {access_token, user:{...}}"""
    if not isinstance(r, dict):
        return {}
    return r.get("user") if isinstance(r.get("user"), dict) else r

print("=== 1. 注册用户A（模拟你）===")
s, r = signup(u1, PW, "何浩")
uo = user_obj(r)
check("用户A注册成功", s == 200 and bool(uo.get("id")), f"HTTP {s}")
check("邮箱免验证（触发器生效）",
      bool(uo.get("email_confirmed_at") or uo.get("confirmed_at")),
      "confirmed_at=" + str(uo.get("email_confirmed_at")))

print("\n=== 2. 用户A登录（拿 access_token）===")
s, r = login(u1, PW)
tok1 = r.get("access_token") if isinstance(r, dict) else None
uid1 = (r.get("user") or {}).get("id") if isinstance(r, dict) else None
check("用户A密码登录成功", s == 200 and bool(tok1), f"HTTP {s} {str(r)[:100] if not tok1 else ''}")
if not tok1:
    sys.exit("cannot continue without token")

print("\n=== 3. profiles 自动创建 ===")
s, r = call(f"/rest/v1/profiles?id=eq.{uid1}&select=*", token=tok1)
check("profile 已自动生成", s == 200 and isinstance(r, list) and len(r) == 1, f"HTTP {s}")
check("昵称取自注册元数据",
      isinstance(r, list) and r and r[0].get("nickname") == "何浩",
      f"nickname={r[0].get('nickname') if isinstance(r,list) and r else None}")

print("\n=== 4. 创建团队空间 ===")
s, r = call("/rest/v1/rpc/create_workspace", "POST",
            {"p_name": "青甘四人组", "p_kind": "team"}, tok1)
team = r if isinstance(r, dict) else (r[0] if isinstance(r, list) and r else None)
check("团队空间创建成功", s == 200 and team and team.get("id"), f"HTTP {s} {str(r)[:120]}")
code = team.get("invite_code") if team else None
check("自动生成邀请码", bool(code) and len(str(code)) == 6, f"code={code}")
ws_team = team.get("id") if team else None

print("\n=== 5. 创建个人空间 ===")
s, r = call("/rest/v1/rpc/create_workspace", "POST",
            {"p_name": "我的私房账", "p_kind": "personal"}, tok1)
pers = r if isinstance(r, dict) else (r[0] if isinstance(r, list) and r else None)
ws_pers = pers.get("id") if pers else None
check("个人空间创建成功", s == 200 and bool(ws_pers), f"HTTP {s}")
check("个人空间无邀请码", pers is not None and pers.get("invite_code") is None)

print("\n=== 6. 用户A写入数据（团队 + 个人）===")
s, r = call("/rest/v1/rpc/push_records", "POST", {"p_ws": ws_team, "p_records": [
    {"id": "e1", "kind": "expense", "ts": 1000,
     "payload": {"amount": 128, "category": "餐饮", "note": "兰州牛肉面", "payer": "何浩"}},
    {"id": "e2", "kind": "expense", "ts": 1001,
     "payload": {"amount": 300, "category": "加油", "note": "西宁加油"}},
    {"id": "meta", "kind": "meta", "ts": 1002, "payload": {"teamName": "青甘四人组"}},
]}, tok1)
check("团队数据写入成功", s == 200, f"HTTP {s} 影响行数={r}")

s, r = call("/rest/v1/rpc/push_records", "POST", {"p_ws": ws_pers, "p_records": [
    {"id": "p1", "kind": "expense", "ts": 1000,
     "payload": {"amount": 999, "category": "购物", "note": "私人消费-别人不该看到"}},
]}, tok1)
check("个人数据写入成功", s == 200, f"HTTP {s}")

print("\n=== 7. 用户A读回数据 ===")
s, r = call(f"/rest/v1/records?workspace_id=eq.{ws_team}&select=*&order=ts", token=tok1)
check("团队数据读回 3 条", s == 200 and isinstance(r, list) and len(r) == 3,
      f"HTTP {s} count={len(r) if isinstance(r,list) else r}")

print("\n=== 8. 注册用户B（模拟老王）并加入团队 ===")
s, _ = signup(u2, PW, "老王")
check("用户B注册成功", s == 200, f"HTTP {s}")
s, r = login(u2, PW)
tok2 = r.get("access_token") if isinstance(r, dict) else None
check("用户B登录成功", s == 200 and bool(tok2), f"HTTP {s}")

s, r = call("/rest/v1/rpc/join_workspace", "POST", {"p_code": code}, tok2)
check("用户B凭邀请码加入团队", s == 200, f"HTTP {s} {str(r)[:120]}")

print("\n=== 9. 【关键】跨账号同步验证 ===")
s, r = call(f"/rest/v1/records?workspace_id=eq.{ws_team}&select=*&order=ts", token=tok2)
n = len(r) if isinstance(r, list) else -1
check("用户B看到用户A写的团队数据", s == 200 and n == 3, f"HTTP {s} count={n}")
if isinstance(r, list) and r:
    notes = [x["payload"].get("note") or x["payload"].get("teamName") for x in r]
    check("数据内容一致", "兰州牛肉面" in notes and "青甘四人组" in notes, str(notes))

print("\n=== 10. 【关键】个人空间隐私隔离 ===")
s, r = call(f"/rest/v1/records?workspace_id=eq.{ws_pers}&select=*", token=tok2)
leaked = len(r) if isinstance(r, list) else -1
check("用户B读不到用户A的个人空间", s == 200 and leaked == 0, f"HTTP {s} 泄露条数={leaked}")

s, r = call("/rest/v1/rpc/push_records", "POST", {"p_ws": ws_pers, "p_records": [
    {"id": "hack", "kind": "expense", "ts": 9999, "payload": {"amount": 1}}]}, tok2)
check("用户B无法写入用户A的个人空间", s >= 400, f"HTTP {s}")

print("\n=== 11. 用户B改团队名（模拟你手机改，电脑要能看到）===")
s, r = call("/rest/v1/rpc/push_records", "POST", {"p_ws": ws_team, "p_records": [
    {"id": "meta", "kind": "meta", "ts": 5000, "payload": {"teamName": "青甘大环线小队"}}]}, tok2)
check("用户B改名写入成功", s == 200, f"HTTP {s}")
s, r = call(f"/rest/v1/records?workspace_id=eq.{ws_team}&id=eq.meta&select=payload,ts", token=tok1)
newname = r[0]["payload"].get("teamName") if isinstance(r, list) and r else None
check("用户A立刻看到新团队名（修复假同步）", newname == "青甘大环线小队", f"teamName={newname}")

print("\n=== 12. 时间戳冲突合并（旧数据不能覆盖新数据）===")
call("/rest/v1/rpc/push_records", "POST", {"p_ws": ws_team, "p_records": [
    {"id": "meta", "kind": "meta", "ts": 100, "payload": {"teamName": "旧名字不该生效"}}]}, tok1)
s, r = call(f"/rest/v1/records?workspace_id=eq.{ws_team}&id=eq.meta&select=payload", token=tok1)
still = r[0]["payload"].get("teamName") if isinstance(r, list) and r else None
check("旧时间戳被正确拒绝", still == "青甘大环线小队", f"teamName={still}")

print("\n=== 13. 空间列表 / 成员列表 ===")
s, r = call("/rest/v1/rpc/my_workspaces", "POST", {}, tok1)
check("用户A看到自己的 2 个空间", s == 200 and isinstance(r, list) and len(r) == 2,
      f"HTTP {s} count={len(r) if isinstance(r,list) else r}")
s, r = call("/rest/v1/rpc/my_workspaces", "POST", {}, tok2)
check("用户B只看到 1 个（团队）空间", s == 200 and isinstance(r, list) and len(r) == 1,
      f"count={len(r) if isinstance(r,list) else r}")
s, r = call("/rest/v1/rpc/ws_members", "POST", {"p_ws": ws_team}, tok1)
names = sorted(x.get("nickname") for x in r) if isinstance(r, list) else r
check("团队成员列表含两人昵称", isinstance(r, list) and len(r) == 2, str(names))

print("\n=== 14. 未登录用户完全无权访问 ===")
s, r = call(f"/rest/v1/records?workspace_id=eq.{ws_team}&select=*")
check("匿名用户读不到任何数据", isinstance(r, list) and len(r) == 0 or s >= 400,
      f"HTTP {s} count={len(r) if isinstance(r,list) else r}")

print("\n=== 15. 清理测试数据 ===")
for w in (ws_team, ws_pers):
    call(f"/rest/v1/workspaces?id=eq.{w}", "DELETE", token=tok1)
s, r = call(f"/rest/v1/workspaces?id=eq.{ws_team}&select=id", token=tok1)
check("测试空间已删除", isinstance(r, list) and len(r) == 0)

p = sum(1 for _, c in results if c)
t = len(results)
print(f"\n{'='*52}\n结果：{p}/{t} 通过")
if p == t:
    print("✅ 后端完全就绪：真实鉴权 + 团队同步 + 个人隐私隔离 全部验证通过")
else:
    print("❌ 失败项：")
    for n_, c in results:
        if not c:
            print("   -", n_)
sys.exit(0 if p == t else 1)
