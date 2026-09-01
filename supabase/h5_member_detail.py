#!/usr/bin/env python3
# h5_member_detail.py — 删除 addMember 按钮 + 删除 showPrepForm + 重写 showMemberDetail
import sys
src = open('index.html', encoding='utf-8').read()

# 1) 删除 renderMemberDivision 里的「+」按钮
old_add_btn = """  if(members.length<12){
    html+='<div class="member-cell" style="display:flex;align-items:center;justify-content:center"><button class="member-add" data-action="addMember">+</button></div>';
  }
  html+='</div>';"""
new_add_btn = """  html+='</div>';"""
if src.count(old_add_btn) != 1:
    print(f'!! addMember 按钮 ({src.count(old_add_btn)})')
    sys.exit(1)
src = src.replace(old_add_btn, new_add_btn)

# 2) 删除 showPrepForm 函数（已无引用）
start = src.index('/* 准备物品表单（item 存在则编辑，否则新增） */')
end = src.index('/* ============================================================\n   模块 2：每日记账')
if 'showPrepForm' not in src[start:end]:
    print('!! showPrepForm 区段定位错误')
    sys.exit(1)
src = src[:start] + '/* ============================================================\n   模块 2：每日记账' + src[end:]

# 3) 重写 showMemberDetail
smd_start = src.index('/* ---- 成员分工详情弹窗 ---- */')
smd_end = src.index('/* ---- 待办可视化日历 ---- */')
old_smd = src[smd_start:smd_end]

NEW_SMD = r"""/* ---- 成员分工详情弹窗 ---- */
function showMemberDetail(memberId){
  var mmm=aliveMembers(),idx=-1;
  for(var k=0;k<mmm.length;k++){if(mmm[k].id===memberId){idx=k;break;}}
  if(idx<0){showToast('成员不存在');return;}
  var mem=mmm[idx];
  var col=memberColor(idx);
  /* 新模型：物品没有「负责人」概念，每件物品由每个成员各自确认。
     这里列所有物品，给当前成员勾选「我备好了」。 */
  var allItems=aliveList(state.data.prepItems);
  var myReady=0,ci;
  for(ci=0;ci<allItems.length;ci++){
    if(allItems[ci].readyBy&&allItems[ci].readyBy[memberId]){myReady++;}
  }
  /* 收集该成员负责的待办 */
  var myTodos=[];
  var _td=aliveList(state.data.todos);
  for(var t=0;t<_td.length;t++){
    /* 用 planHasOwner 而不是 ===：多人计划要在每个负责人名下都算一份 */
    if(planHasOwner(_td[t],memberId)){myTodos.push(_td[t]);}
  }
  var totalItems=allItems.length,totalTodos=myTodos.length;
  var doneTodos=0;
  for(var dt=0;dt<myTodos.length;dt++){if(myTodos[dt].done)doneTodos++;}
  /* 进度 = 已备物品 + 已完成计划，按总件数算 */
  var doneAll=myReady+doneTodos;
  var totalAll=totalItems+totalTodos;
  var pct=totalAll?Math.round(doneAll/totalAll*100):0;
  /* 进度环：内联SVG */
  var ringR=34,circ=2*Math.PI*ringR,dash=Math.round(pct/100*circ);
  var ring='<svg viewBox="0 0 84 84" style="width:84px;height:84px">'+
    '<circle cx="42" cy="42" r="'+ringR+'" fill="none" stroke="#e8f5f3" stroke-width="8"/>'+
    '<circle cx="42" cy="42" r="'+ringR+'" fill="none" stroke="'+col+'" stroke-width="8" stroke-linecap="round" stroke-dasharray="'+dash+' '+(circ-dash)+'" transform="rotate(-90 42 42)"/>'+
    '<text x="42" y="40" text-anchor="middle" font-size="14" font-weight="700" fill="'+col+'">'+pct+'%</text>'+
    '<text x="42" y="56" text-anchor="middle" font-size="8" fill="#7f8c8d">完成度</text></svg>';
  /* 进度详情 */
  var detailStats='<div style="display:flex;gap:8px;margin:12px 0;flex-wrap:wrap">'+
    '<div style="flex:1;min-width:70px;background:var(--primary-bg);border-radius:10px;padding:10px;text-align:center"><div style="font-size:1.3rem;font-weight:700;color:var(--primary-dark)">'+myReady+'/'+totalItems+'</div><div style="font-size:0.7rem;color:var(--text-light)">已备物品</div></div>'+
    '<div style="flex:1;min-width:70px;background:var(--primary-bg);border-radius:10px;padding:10px;text-align:center"><div style="font-size:1.3rem;font-weight:700;color:var(--primary-dark)">'+totalTodos+'</div><div style="font-size:0.7rem;color:var(--text-light)">负责计划</div><div style="font-size:0.7rem;color:var(--primary)">完成 '+doneTodos+'</div></div>'+
    '</div>';
  /* 物品列表：全部物品，勾选代表「我备好了」 */
  var itemHtml='<div style="font-size:0.85rem;font-weight:600;color:var(--primary-dark);margin:8px 0 4px">物品准备（勾选代表我已备好）</div>';
  if(totalItems===0){itemHtml+='<div style="font-size:0.78rem;color:var(--text-light);padding:4px 0">暂无物品</div>';}
  else{
    itemHtml+='<div style="max-height:180px;overflow-y:auto">';
    for(var mi=0;mi<allItems.length;mi++){
      var it=allItems[mi];
      var isReady=!!(it.readyBy&&it.readyBy[memberId]);
      itemHtml+='<div class="todo-item'+(isReady?' done':'')+'"><input type="checkbox"'+(isReady?' checked':'')+' data-kind="item" data-id="'+it.id+'" class="mdl-check"><span class="text">'+escapeHtml(it.name)+' <span style="color:var(--text-light);font-size:0.72rem">'+escapeHtml(prepCatName(it.cat))+'</span></span></div>';
    }
    itemHtml+='</div>';
  }
  /* 待办列表 */
  var todoHtml='<div style="font-size:0.85rem;font-weight:600;color:var(--primary-dark);margin:8px 0 4px">负责的计划</div>';
  if(myTodos.length===0){todoHtml+='<div style="font-size:0.78rem;color:var(--text-light);padding:4px 0">暂无</div>';}
  else{
    todoHtml+='<div style="max-height:180px;overflow-y:auto">';
    for(var tj=0;tj<myTodos.length;tj++){
      var td=myTodos[tj];
      todoHtml+='<div class="todo-item'+(td.done?' done':'')+'"><input type="checkbox"'+(td.done?' checked':'')+' data-kind="todo" data-id="'+td.id+'" class="mdl-check"><span class="text">'+escapeHtml(td.text)+' <span style="color:var(--text-light);font-size:0.72rem">'+planDateLabel(td)+'</span>'+planByBadge(td)+'</span></div>';
    }
    todoHtml+='</div>';
  }
  /* 弹窗 */
  var sheet=document.getElementById('formModalSheet');
  sheet.innerHTML='<div class="form-modal-title"><span style="display:flex;align-items:center;gap:8px"><span style="width:26px;height:26px;border-radius:50%;background:'+col+';color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700">'+escapeHtml((mem.name||'?').charAt(0))+'</span>'+escapeHtml(mem.name)+'的分工 · '+pct+'% 完成</span><button id="closeForm">✕</button></div>'+
    '<div style="display:flex;align-items:center;gap:16px;margin:6px 0">'+ring+detailStats+'</div>'+
    itemHtml+todoHtml+
    '<div style="font-size:0.7rem;color:var(--text-light);margin-top:10px">勾选可快速标记完成，进度会实时更新</div>'+
    '<button class="btn btn-primary btn-block" style="margin-top:12px" id="closeDetail">关闭</button>';
  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  document.getElementById('closeDetail').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  /* 勾选快速完成 */
  var checks=sheet.querySelectorAll('.mdl-check');
  for(var ck=0;ck<checks.length;ck++){
    checks[ck].onchange=function(){
      var kind=this.getAttribute('data-kind');
      var id=this.getAttribute('data-id');
      var checked=this.checked;
      if(kind==='item'){
        for(var q=0;q<state.data.prepItems.length;q++){
          if(state.data.prepItems[q].id===id){
            if(!state.data.prepItems[q].readyBy){state.data.prepItems[q].readyBy={};}
            if(checked){state.data.prepItems[q].readyBy[memberId]=true;}
            else{delete state.data.prepItems[q].readyBy[memberId];}
            state.data.prepItems[q]._ts=Date.now();
            break;
          }
        }
      }else{
        for(var r=0;r<state.data.todos.length;r++){
          if(state.data.todos[r].id===id){state.data.todos[r].done=checked;state.data.todos[r]._ts=Date.now();break;}
        }
      }
      saveData();
      /* 刷新弹窗内容 */
      showMemberDetail(memberId);
    };
  }
}
"""

src = src[:smd_start] + NEW_SMD + src[smd_end:]
open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
