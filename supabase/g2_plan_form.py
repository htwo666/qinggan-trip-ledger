# -*- coding: utf-8 -*-
"""计划表单：日期区间 + 负责人多选 + 记录创建者"""
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


# ── 多选负责人的勾选组件 ─────────────────────────────────────
sub('多选负责人组件',
"""/* 待办负责人下拉选项 */
function memberSelectOptions(selId){""",
"""/* 计划负责人多选：一排可点的小胶囊，点一下切换选中
   （用 checkbox 而不是 multiple select —— 手机上 multiple select 极难点） */
function ownerCheckboxes(selIds){
  selIds=selIds||[];
  var mlist=aliveMembers(),html='',i;
  if(!mlist.length){return '<div style="font-size:0.75rem;color:var(--text-light)">还没有成员</div>';}
  html='<div class="owner-pick">';
  for(i=0;i<mlist.length;i++){
    var m=mlist[i],on=false,j;
    for(j=0;j<selIds.length;j++){if(selIds[j]===m.id){on=true;break;}}
    var col=memberColor(i);
    html+='<label class="owner-chip'+(on?' on':'')+'" style="'+(on?('border-color:'+col+';background:'+col+'1a;color:'+col):'')+'">'+
      '<input type="checkbox" class="fOwnerChk" value="'+m.id+'"'+(on?' checked':'')+'>'+
      escapeHtml(m.name)+'</label>';
  }
  html+='</div>';
  return html;
}
/* 读取多选负责人的当前值 */
function readOwnerChecks(){
  var els=document.querySelectorAll('.fOwnerChk'),out=[],i;
  for(i=0;i<els.length;i++){if(els[i].checked){out.push(els[i].value);}}
  return out;
}
/* 待办负责人下拉选项 */
function memberSelectOptions(selId){""")


# ── 表单本体 ────────────────────────────────────────────────
sub('计划表单',
"""function showTodoForm(){
  var today=todayStr();
  var sheet=document.getElementById('formModalSheet');
  sheet.innerHTML='<div class="form-modal-title">添加待办<button id="closeForm">✕</button></div>'+
    '<div class="form-row"><div><label>日期</label><input type="date" id="fDate" value="'+today+'"></div>'+
    '<div><label>负责人</label><select id="fOwner">'+memberSelectOptions('')+'</select></div></div>'+
    '<div class="form-row"><div style="flex:1"><label>待办内容</label><input type="text" id="fText" placeholder="如：预订莫高窟门票"></div></div>'+
    '<button class="btn btn-primary btn-block" style="margin-top:12px" id="saveTodoBtn">保存</button>';
  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  document.getElementById('saveTodoBtn').onclick=function(){
    var t={id:genId(),date:document.getElementById('fDate').value,text:document.getElementById('fText').value.trim(),owner:document.getElementById('fOwner').value,done:false,_ts:Date.now()};
    if(!t.date){showToast('请选择日期');return;}
    if(!t.text){showToast('请填写内容');return;}
    state.data.todos.push(t);saveData();
    /* 日历跳到该待办所在月份 */
    var dp=t.date.split('-');if(dp.length===3){state.calYear=parseInt(dp[0],10);state.calMonth=parseInt(dp[1],10)-1;state.calSel=t.date;}
    document.getElementById('formModal').classList.remove('show');
    renderPrep();showToast('已添加');
  };
}""",
"""/* 计划表单（plan 存在则编辑，否则新增） */
function showTodoForm(plan){
  plan=plan||null;
  var today=todayStr();
  var vStart=plan?planStart(plan):today;
  var vEnd=plan?planEnd(plan):today;
  var vOwners=plan?planOwners(plan):[];
  var sheet=document.getElementById('formModalSheet');
  sheet.innerHTML='<div class="form-modal-title">'+(plan?'修改计划':'添加计划')+'<button id="closeForm">✕</button></div>'+
    '<div class="form-row"><div style="flex:1"><label>计划内容</label><input type="text" id="fText" placeholder="如：预订莫高窟门票" value="'+(plan?escapeHtml(plan.text):'')+'"></div></div>'+
    '<div class="form-row"><div><label>开始日期</label><input type="date" id="fDate" value="'+vStart+'"></div>'+
    '<div><label>结束日期</label><input type="date" id="fEndDate" value="'+vEnd+'"></div></div>'+
    '<div style="font-size:0.7rem;color:var(--text-light);margin:-4px 0 8px">单天的计划，两个日期填一样就行；跨几天就选一段（如 9.25–9.30）</div>'+
    '<div class="form-row"><div style="flex:1"><label>负责人（可多选）</label>'+ownerCheckboxes(vOwners)+'</div></div>'+
    '<button class="btn btn-primary btn-block" style="margin-top:12px" id="saveTodoBtn">保存</button>';
  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  /* 胶囊点击时同步高亮（checkbox 本身是隐藏的） */
  var chks=document.querySelectorAll('.fOwnerChk'),ci;
  for(ci=0;ci<chks.length;ci++){
    chks[ci].onchange=function(){
      var lb=this.parentNode;
      if(this.checked){lb.className='owner-chip on';}
      else{lb.className='owner-chip';lb.removeAttribute('style');}
    };
  }
  document.getElementById('saveTodoBtn').onclick=function(){
    var start=document.getElementById('fDate').value;
    var end=document.getElementById('fEndDate').value||start;
    var text=document.getElementById('fText').value.trim();
    if(!start){showToast('请选择开始日期');return;}
    if(!text){showToast('请填写计划内容');return;}
    /* 结束日早于开始日 → 自动兑换，别让用户为了顺序再填一遍 */
    if(end<start){var tmp=start;start=end;end=tmp;}
    var owners=readOwnerChecks();
    if(plan){
      /* 编辑：保留原创建者，不冒领别人的计划 */
      for(var i=0;i<state.data.todos.length;i++){
        if(state.data.todos[i].id===plan.id){
          var o=state.data.todos[i];
          o.date=start;o.endDate=end;o.text=text;
          o.owners=owners;o.owner=owners.length?owners[0]:'';
          o._ts=Date.now();
          break;
        }
      }
    }else{
      var t={id:genId(),date:start,endDate:end,text:text,
             owners:owners,
             /* owner 单字段同步写一份：老版本页面读的是这个 */
             owner:owners.length?owners[0]:'',
             done:false,
             by:myUid(),byName:currentNickname(),
             _ts:Date.now()};
      state.data.todos.push(t);
    }
    saveData();
    /* 日历跳到计划开始的月份 */
    var dp=start.split('-');
    if(dp.length===3){state.calYear=parseInt(dp[0],10);state.calMonth=parseInt(dp[1],10)-1;state.calSel=start;}
    document.getElementById('formModal').classList.remove('show');
    renderPrep();showToast(plan?'已更新':'已添加');
  };
}""")


# ── 胶囊 CSS ────────────────────────────────────────────────
sub('胶囊 CSS',
""".plan-range{display:inline-block;""",
""".owner-pick{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;}
.owner-chip{display:inline-flex;align-items:center;font-size:0.78rem;padding:5px 12px;border-radius:14px;border:1px solid var(--border);background:var(--card);color:var(--text);cursor:pointer;user-select:none;}
.owner-chip input{display:none;}
.owner-chip.on{font-weight:600;}
.plan-range{display:inline-block;""")


io.open(P, 'w', encoding='utf-8').write(src)
print('\n%d/3  %d → %d bytes' % (len(ok), before, len(src)))
