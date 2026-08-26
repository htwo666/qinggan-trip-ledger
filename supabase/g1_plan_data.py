# -*- coding: utf-8 -*-
"""待办 → 计划：数据结构升级 + 兼容层
   1. date 保留为开始日，新增 endDate 表示阶段结束（单日则 endDate===date）
   2. owner 单人保留（老数据），新增 owners 数组表示多人
   3. 新增 by(创建者uid) / byName(创建者昵称快照)
   兼容策略：不改老字段，只加新字段，读的时候统一走 helper。
   这样老设备读新数据不会崩，新设备读老数据也能自动补齐。
"""
import io

P = 'index.html'
src = io.open(P, encoding='utf-8').read()
before = len(src)
ok = []


def sub(name, old, new, count=1):
    global src
    if old not in src:
        print('  MISS  %s' % name)
        return False
    n = src.count(old)
    if n != count:
        print('  WARN  %s 出现 %d 次（预期 %d）' % (name, n, count))
    src = src.replace(old, new, count)
    ok.append(name)
    print('  OK    %s' % name)
    return True


# ── 1. normalizeData 里补齐老数据 ─────────────────────────────
sub('todo 字段迁移',
"""  if(!d.todos){d.todos=[];}""",
"""  if(!d.todos){d.todos=[];}
  /* 计划字段迁移：老待办只有 date + 单个 owner，这里补出区间和多人字段。
     只补不改，老字段原样留着，万一用户还有旧设备在用也不会读崩。 */
  for(var _ti=0;_ti<d.todos.length;_ti++){
    var _t=d.todos[_ti];
    if(!_t){continue;}
    /* 没有结束日 → 单日计划，结束日等于开始日 */
    if(!_t.endDate){_t.endDate=_t.date||'';}
    /* 没有 owners 数组 → 用单个 owner 拼一个；没负责人就空数组 */
    if(!_t.owners){_t.owners=_t.owner?[_t.owner]:[];}
  }""")


# ── 2. 计划字段读取 helper（渲染/统计统一走这里）─────────────
sub('计划 helper',
"""/* 待办负责人下拉选项 */""",
"""/* ---------- 计划（原待办）字段读取 ----------
   老数据只有 date + owner，新数据是 date~endDate + owners[]。
   所有渲染和统计都走这几个函数，避免每处都写一遍兼容判断。 */
/* 开始日 */
function planStart(t){return t.date||'';}
/* 结束日：没有就退回开始日（单日计划） */
function planEnd(t){return t.endDate||t.date||'';}
/* 是否跨天 */
function planIsRange(t){
  var a=planStart(t),b=planEnd(t);
  return !!(a&&b&&b>a);
}
/* 负责人数组：优先 owners，退回单个 owner */
function planOwners(t){
  if(t.owners&&t.owners.length){return t.owners;}
  return t.owner?[t.owner]:[];
}
/* 某成员是否参与这个计划 */
function planHasOwner(t,mid){
  var os=planOwners(t),i;
  for(i=0;i<os.length;i++){if(os[i]===mid){return true;}}
  return false;
}
/* 某天是否落在计划区间内（含首尾） */
function planCoversDate(t,ds){
  var a=planStart(t),b=planEnd(t);
  if(!a){return false;}
  if(!b){return ds===a;}
  return ds>=a&&ds<=b;
}
/* 计划的紧急度基准日：用结束日判断逾期
   （阶段计划只要还没到结束日就不算逾期，9.25-9.30 在 9.27 那天不该标红） */
function planDueDate(t){return planEnd(t);}
/* 日期区间的显示文案 */
function planDateLabel(t){
  var a=planStart(t),b=planEnd(t);
  if(!a){return '未定日期';}
  if(!b||b===a){return fmtDate(a)+'前';}
  return fmtDate(a)+'–'+fmtDate(b);
}
/* 创建者色块：按 uid 稳定散列取色，不同人不同颜色 */
var PLAN_BY_COLORS=['#2d8b8b','#f0a04b','#9b59b6','#3498db','#e85d5d','#16a085','#e67e22','#7f8c8d'];
function planByColor(key){
  if(!key){return '#95a5a6';}
  var h=0,i;
  for(i=0;i<key.length;i++){h=(h*31+key.charCodeAt(i))%99991;}
  return PLAN_BY_COLORS[h%PLAN_BY_COLORS.length];
}
/* 创建者显示名：优先存的快照，其次按 uid 找认领的成员 */
function planByName(t){
  if(t.byName){return t.byName;}
  if(t.by){
    var ms=aliveMembers(),i;
    for(i=0;i<ms.length;i++){if(ms[i].uid===t.by){return ms[i].name;}}
  }
  return '';
}
/* 多人负责徽章 */
function ownersBadges(t){
  var os=planOwners(t),html='',i;
  for(i=0;i<os.length;i++){html+=ownerBadge(os[i]);}
  return html;
}
/* 创建者小标签 */
function planByBadge(t){
  var nm=planByName(t);
  if(!nm){return '';}
  var col=planByColor(t.by||nm);
  return '<span class="plan-by" style="color:'+col+';background:'+col+'1a;border-color:'+col+'55">'+
         escapeHtml(nm)+' 添加</span>';
}
/* 待办负责人下拉选项 */""")


# ── 3. CSS：创建者色块 + 区间条 ──────────────────────────────
sub('计划 CSS',
""".todo-item .del-todo svg{width:14px;height:14px;}""",
""".todo-item .del-todo svg{width:14px;height:14px;}
/* 计划：创建者标签 + 左侧色条（一眼看出谁加的） */
.plan-by{display:inline-block;font-size:0.66rem;padding:1px 6px;border-radius:8px;margin-left:4px;border:1px solid;white-space:nowrap;}
.todo-item.plan{border-left:4px solid var(--border);padding-left:8px;}
.plan-range{display:inline-block;font-size:0.66rem;padding:1px 6px;border-radius:8px;margin-left:4px;background:var(--primary-bg);color:var(--primary-dark);white-space:nowrap;}
/* 日历里跨天计划的连续条 */
.cal-day .day-bar{display:block;height:3px;border-radius:2px;margin-top:1px;}""")


io.open(P, 'w', encoding='utf-8').write(src)
print('\n%d/%d  %d → %d bytes' % (len(ok), 3, before, len(src)))
