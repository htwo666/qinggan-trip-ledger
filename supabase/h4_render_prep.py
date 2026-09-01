#!/usr/bin/env python3
# h4_render_prep.py — 重写 renderPrep 为板块形式
import sys
src = open('index.html', encoding='utf-8').read()

start = src.index('function renderPrep(){')
end = src.index('function memberNameById(')
old = src[start:end]

NEW = r"""function renderPrep(){
  var p=document.getElementById('panel-prep');
  var data=viewData();
  var prepItems=data.prepItems||[];
  var todos=data.todos||[];
  var members=aliveMembers();
  var today=todayStr();
  /* 计划分类：逾期 / 今天要做 / 未来
     逾期看结束日 —— 9.25–9.30 的阶段计划，9.27 那天还在进行中，不该标红。
     今天要做包含「今天正好落在区间里」的阶段计划。 */
  var overdueTodos=[],todayTodos=[],upcomingTodos=[];
  for(var ti=0;ti<todos.length;ti++){
    var _p=todos[ti];
    if(_p.done){continue;}
    if(planEnd(_p)&&planEnd(_p)<today){overdueTodos.push(_p);}
    else if(planCoversDate(_p,today)){todayTodos.push(_p);}
    else{upcomingTodos.push(_p);}
  }
  /* 今天要处理：只列计划，物品不再单列（板块里就能直接看谁备了谁没备） */
  var todayHtml='<div class="today-section"><div class="today-title">'+svgIcon('today')+'今天要处理</div>';
  if(overdueTodos.length===0&&todayTodos.length===0){
    todayHtml+='<div class="today-empty">今天没有要处理的计划，下方可以添加</div>';
  }else{
    for(var j=0;j<overdueTodos.length;j++){
      todayHtml+='<div class="today-item overdue"><span class="label"><strong>【逾期】</strong>'+escapeHtml(overdueTodos[j].text)+
        '<span class="plan-range">'+planDateLabel(overdueTodos[j])+'</span>'+planByBadge(overdueTodos[j])+
        '</span><button class="btn btn-sm btn-primary act-btn" data-action="doneTodo" data-id="'+overdueTodos[j].id+'">完成</button></div>';
    }
    for(var t2=0;t2<todayTodos.length;t2++){
      /* 阶段计划标「进行中」，单日标「今日」，区分开更清楚 */
      var _lbl=planIsRange(todayTodos[t2])?'【进行中】':'【今日】';
      todayHtml+='<div class="today-item"><span class="label"><strong>'+_lbl+'</strong>'+escapeHtml(todayTodos[t2].text)+
        '<span class="plan-range">'+planDateLabel(todayTodos[t2])+'</span>'+planByBadge(todayTodos[t2])+
        '</span><button class="btn btn-sm btn-primary act-btn" data-action="doneTodo" data-id="'+todayTodos[t2].id+'">完成</button></div>';
    }
  }
  todayHtml+='</div>';
  /* 待办可视化日历 */
  var calHtml=renderPrepCalendar(todos,today);
  /* 待办清单卡片（全部未完成 + 已完成折叠） */
  var doneTodos=[];
  for(var dt=0;dt<todos.length;dt++){
    if(todos[dt].done){doneTodos.push(todos[dt]);}
  }
  var todoCard='<div class="card"><div class="card-title">'+svgIcon('today')+'计划清单 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（未完成 '+(overdueTodos.length+todayTodos.length+upcomingTodos.length)+' · 已完成 '+doneTodos.length+'）</span></div>';
  if(overdueTodos.length+todayTodos.length+upcomingTodos.length===0&&doneTodos.length===0){
    todoCard+='<div class="empty">'+svgIcon('check')+'<div>暂无计划，点下方「添加计划」</div></div>';
  }else{
    var allOpen=overdueTodos.concat(todayTodos).concat(upcomingTodos);
    for(var a=0;a<allOpen.length;a++){
      var _pl=allOpen[a];
      var od=planEnd(_pl)&&planEnd(_pl)<today;
      /* 左侧色条用创建者的颜色 —— 团队里一眼能分出谁加的 */
      var _bcol=planByColor(_pl.by||planByName(_pl));
      todoCard+='<div class="todo-item plan" style="border-left-color:'+_bcol+'">'+
        '<input type="checkbox" data-id="'+_pl.id+'" class="todo-check">'+
        '<span class="text">'+(od?'<span style="color:var(--danger);font-weight:600">[逾期] </span>':'')+
        escapeHtml(_pl.text)+
        '<span class="plan-range">'+planDateLabel(_pl)+'</span>'+
        ownersBadges(_pl)+planByBadge(_pl)+
        '</span>'+
        '<button class="del-todo" data-action="editTodo" data-id="'+_pl.id+'" title="修改">'+svgIcon('edit')+'</button>'+
        '<button class="del-todo" data-action="delTodo" data-id="'+_pl.id+'">'+svgIcon('trash')+'</button></div>';
    }
    if(doneTodos.length>0){
      todoCard+='<div style="font-size:0.75rem;color:var(--text-light);margin:8px 0 4px">已完成：</div>';
      for(var d2=0;d2<Math.min(doneTodos.length,5);d2++){
        todoCard+='<div class="todo-item done"><input type="checkbox" checked data-id="'+doneTodos[d2].id+'" class="todo-check"><span class="text">'+escapeHtml(doneTodos[d2].text)+'</span><button class="del-todo" data-action="delTodo" data-id="'+doneTodos[d2].id+'">'+svgIcon('trash')+'</button></div>';
      }
    }
  }
  todoCard+='</div>';
  /* 必买清单：按分类板块展示。
     每个板块一排排物品，物品后面是一排成员头像按钮，
     点亮代表「我备好了」，所有人点亮 = 全员备齐。 */
  var cats=prepCats();
  var byCat={};
  for(var bc=0;bc<cats.length;bc++){byCat[cats[bc].id]=[];}
  for(var pi=0;pi<prepItems.length;pi++){
    var _it=prepItems[pi];
    var _cid=_it.cat||'';
    /* 老数据没 cat（还没迁移）兜底到第一个分类，避免物品凭空消失 */
    if(!_cid&&cats.length){_cid=cats[0].id;}
    if(!byCat[_cid]){byCat[_cid]=[];}
    byCat[_cid].push(_it);
  }
  /* 备齐进度 */
  var fullyReady=0;
  for(var fr=0;fr<prepItems.length;fr++){
    if(prepAllReady(prepItems[fr])){fullyReady++;}
  }
  var boardHtml='<div class="card"><div class="card-title">'+svgIcon('prep')+'必买清单 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（'+fullyReady+'/'+prepItems.length+' 全员备齐）</span></div>';
  if(prepItems.length===0){
    boardHtml+='<div class="empty">'+svgIcon('prep')+'<div>清单是空的，点下方「添加板块」或在板块里输入物品名开始添加</div></div>';
  }
  boardHtml+='<div class="prep-board-grid">';
  for(var bi=0;bi<cats.length;bi++){
    var cat=cats[bi];
    var items=byCat[cat.id]||[];
    boardHtml+='<div class="prep-board" data-cat="'+cat.id+'">'+
      '<div class="prep-board-head">'+
        '<input class="prep-board-name" value="'+escapeHtml(cat.name)+'" data-cat="'+cat.id+'">'+
        '<button class="prep-board-del" data-action="delBoard" data-id="'+cat.id+'" title="删除板块">'+svgIcon('trash')+'</button>'+
      '</div>'+
      '<div class="prep-board-items">';
    if(items.length===0){
      boardHtml+='<div class="prep-empty-board">还没有物品，下面输入添加</div>';
    }else{
      for(var ii=0;ii<items.length;ii++){
        var item=items[ii];
        var allR=prepAllReady(item);
        boardHtml+='<div class="prep-item'+(allR?' all-ready':'')+'" data-id="'+item.id+'">'+
          '<div class="prep-item-top">'+
            '<input class="prep-item-name" value="'+escapeHtml(item.name)+'" data-id="'+item.id+'">'+
            '<button class="prep-item-del" data-action="delPrepItem" data-id="'+item.id+'" title="删除物品">'+svgIcon('trash')+'</button>'+
          '</div>'+
          '<div class="prep-ready-row">';
        for(var ri=0;ri<members.length;ri++){
          var mb=members[ri];
          var on=!!(item.readyBy&&item.readyBy[mb.id]);
          var col=memberColor(ri);
          boardHtml+='<button class="prep-ready'+(on?' on':'')+'" style="'+(on?('background:'+col+';border-color:'+col):'')+'" data-action="toggleReady" data-id="'+item.id+'" data-mid="'+mb.id+'" title="'+escapeHtml(mb.name)+'">'+escapeHtml((mb.name||'?').charAt(0))+'</button>';
        }
        boardHtml+='</div></div>';
      }
    }
    boardHtml+='</div>';
    /* 板块底部添加物品输入框，回车直接添加 */
    boardHtml+='<div class="prep-add-row"><input class="prep-add-input" placeholder="+ 添加物品，回车确认" data-cat="'+cat.id+'"></div>';
    boardHtml+='</div>';
  }
  boardHtml+='</div>';
  /* 加板块按钮 */
  boardHtml+='<div style="margin-top:10px"><button class="btn btn-outline btn-sm" id="addBoardBtn">'+svgIcon('plus')+'添加板块</button></div>';
  boardHtml+='</div>';
  /* 工具栏 */
  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="addTodoBtn">'+svgIcon('plus')+'添加计划</button><button class="btn btn-outline btn-sm" id="clearPrepSampleBtn">清空数据</button></div>';
  /* 成员分工 */
  var memberHtml=renderMemberDivision(prepItems,todos);
  p.innerHTML=todayHtml+calHtml+todoCard+memberHtml+boardHtml+toolbar;
  /* 事件 */
  var addTodoBtn=document.getElementById('addTodoBtn');
  if(addTodoBtn){addTodoBtn.onclick=function(){showTodoForm();};}
  var addBoardBtn=document.getElementById('addBoardBtn');
  if(addBoardBtn){addBoardBtn.onclick=function(){showAddBoardForm();};}
  var clearBtn=document.getElementById('clearPrepSampleBtn');
  if(clearBtn){clearBtn.onclick=function(){
    showConfirm('清空准备数据','将删除全部计划与物品记录，此操作不可撤销。确定继续吗？',function(){
      state.data.prepItems=[];state.data.prepCategories=[];state.data.todos=[];saveData();renderPrep();showToast('已清空');
    });
  };}
  /* 待办完成/删除 */
  var todoChecks=p.querySelectorAll('.todo-check');
  for(var tc=0;tc<todoChecks.length;tc++){
    todoChecks[tc].onchange=function(){
      var id=this.getAttribute('data-id');
      for(var i=0;i<state.data.todos.length;i++){
        if(state.data.todos[i].id===id){state.data.todos[i].done=this.checked;state.data.todos[i]._ts=Date.now();break;}
      }
      saveData();renderPrep();
    };
  }
  var todoDoneBtns=p.querySelectorAll('[data-action="doneTodo"]');
  for(var td2=0;td2<todoDoneBtns.length;td2++){
    todoDoneBtns[td2].onclick=function(){
      var id=this.getAttribute('data-id');
      for(var i=0;i<state.data.todos.length;i++){
        if(state.data.todos[i].id===id){state.data.todos[i].done=true;state.data.todos[i]._ts=Date.now();break;}
      }
      saveData();renderPrep();showToast('已完成');
    };
  }
  var todoDelBtns=p.querySelectorAll('[data-action="delTodo"]');
  for(var tl=0;tl<todoDelBtns.length;tl++){
    todoDelBtns[tl].onclick=function(){
      var id=this.getAttribute('data-id');
      for(var i=0;i<state.data.todos.length;i++){
        if(state.data.todos[i].id===id){state.data.todos[i]._deleted=true;state.data.todos[i]._ts=Date.now();break;}
      }
      saveData();renderPrep();showToast('已删除');
    };
  }
  /* 编辑计划 */
  var editTodoBtns=p.querySelectorAll('[data-action="editTodo"]');
  for(var eti=0;eti<editTodoBtns.length;eti++){
    editTodoBtns[eti].onclick=function(){
      var id=this.getAttribute('data-id');
      for(var i=0;i<state.data.todos.length;i++){
        if(state.data.todos[i].id===id){showTodoForm(state.data.todos[i]);break;}
      }
    };
  }
  /* 日历事件：上月/下月/今天 */
  var calNavBtns=p.querySelectorAll('.cal-nav-btn');
  for(var cn=0;cn<calNavBtns.length;cn++){
    calNavBtns[cn].onclick=function(){
      if(this.getAttribute('data-dir')==='today'){
        var nw=new Date();
        state.calYear=nw.getFullYear();state.calMonth=nw.getMonth();state.calSel=null;
      }
      else{
        var dir=parseInt(this.getAttribute('data-dir')||'0',10);
        var y=state.calYear,mo=state.calMonth;
        var dt=new Date(y,mo+dir,1);
        state.calYear=dt.getFullYear();state.calMonth=dt.getMonth();
      }
      renderPrep();
    };
  }
  /* 日历：点击日期选中 */
  var calDays=p.querySelectorAll('.cal-day');
  for(var cd=0;cd<calDays.length;cd++){
    calDays[cd].onclick=function(){
      var d=this.getAttribute('data-date');
      state.calSel=(state.calSel===d)?null:d;
      renderPrep();
    };
  }
  /* 成员名称编辑 */
  var memberInputs=p.querySelectorAll('.member-name-input');
  for(var mi2=0;mi2<memberInputs.length;mi2++){
    memberInputs[mi2].onchange=function(){
      var id=this.getAttribute('data-id');
      var val=this.value.trim();
      if(!val){showToast('名字不能为空');renderPrep();return;}
      for(var mi3=0;mi3<state.data.members.length;mi3++){
        if(state.data.members[mi3].id===id){state.data.members[mi3].name=val;state.data.members[mi3]._ts=Date.now();break;}
      }
      saveData();renderPrep();renderCurrentPanel();
    };
  }
  /* 删除成员 */
  var delMemberBtns=p.querySelectorAll('[data-action="delMember"]');
  for(var dm=0;dm<delMemberBtns.length;dm++){
    delMemberBtns[dm].onclick=function(){
      var id=this.getAttribute('data-id');
      if(aliveMembers().length<=1){showToast('至少保留 1 位成员');return;}
      var name=memberNameById(id);
      showConfirm('删除成员','确定删除成员「'+name+'」吗？\n\n该成员负责的物品不会删除，已记的账目仍保留（结算时会显示为"已退出"）。',function(){
        /* 用墓碑标记而不是直接删除，否则云端的旧记录会在下次同步时"复活"
           （这就是"删了成员又变回预设那几个"的根源） */
        for(var mz=0;mz<state.data.members.length;mz++){
          if(state.data.members[mz].id===id){
            state.data.members[mz]._deleted=true;
            state.data.members[mz]._ts=Date.now();
            break;
          }
        }
        saveData();renderPrep();renderCurrentPanel();
      });
    };
  }
  /* 认领成员（这是我） */
  var claimBtns=p.querySelectorAll('[data-action="claimMember"]');
  for(var cb2=0;cb2<claimBtns.length;cb2++){
    claimBtns[cb2].onclick=function(){
      if(this.disabled){return;}
      claimMember(this.getAttribute('data-id'),function(){renderPrep();});
    };
  }
  /* 点击头像查看成员分工详情 */
  var viewBtns=p.querySelectorAll('[data-action="viewMember"]');
  for(var vbi=0;vbi<viewBtns.length;vbi++){
    viewBtns[vbi].onclick=function(){
      var id=this.getAttribute('data-id');
      showMemberDetail(id);
    };
  }
  /* === 必买清单板块事件 === */
  /* 板块重命名（失焦保存） */
  var boardNames=p.querySelectorAll('.prep-board-name');
  for(var bn=0;bn<boardNames.length;bn++){
    boardNames[bn].onchange=function(){
      var cid=this.getAttribute('data-cat');
      var val=this.value.trim();
      if(!val){showToast('板块名不能为空');renderPrep();return;}
      for(var bi2=0;bi2<state.data.prepCategories.length;bi2++){
        if(state.data.prepCategories[bi2].id===cid){
          state.data.prepCategories[bi2].name=val;
          state.data.prepCategories[bi2]._ts=Date.now();
          break;
        }
      }
      saveData();renderPrep();
    };
  }
  /* 删除板块（连带删除其中的物品） */
  var delBoardBtns=p.querySelectorAll('[data-action="delBoard"]');
  for(var db=0;db<delBoardBtns.length;db++){
    delBoardBtns[db].onclick=function(){
      var cid=this.getAttribute('data-id');
      var cname=prepCatName(cid);
      var cnt=0,ci;
      for(ci=0;ci<state.data.prepItems.length;ci++){
        if(!state.data.prepItems[ci]._deleted&&state.data.prepItems[ci].cat===cid){cnt++;}
      }
      var msg='删除板块「'+cname+'」';
      if(cnt>0){msg+='会同时删除其中的 '+cnt+' 件物品';}
      msg+='，确定吗？';
      showConfirm('删除板块',msg,function(){
        for(var bi3=0;bi3<state.data.prepCategories.length;bi3++){
          if(state.data.prepCategories[bi3].id===cid){
            state.data.prepCategories[bi3]._deleted=true;
            state.data.prepCategories[bi3]._ts=Date.now();
            break;
          }
        }
        for(var pi2=0;pi2<state.data.prepItems.length;pi2++){
          if(!state.data.prepItems[pi2]._deleted&&state.data.prepItems[pi2].cat===cid){
            state.data.prepItems[pi2]._deleted=true;
            state.data.prepItems[pi2]._ts=Date.now();
          }
        }
        saveData();renderPrep();showToast('已删除板块');
      });
    };
  }
  /* 物品名编辑（失焦保存） */
  var itemNameInputs=p.querySelectorAll('.prep-item-name');
  for(var inm=0;inm<itemNameInputs.length;inm++){
    itemNameInputs[inm].onchange=function(){
      var id=this.getAttribute('data-id');
      var val=this.value.trim();
      if(!val){showToast('物品名不能为空');renderPrep();return;}
      for(var pi3=0;pi3<state.data.prepItems.length;pi3++){
        if(state.data.prepItems[pi3].id===id){
          state.data.prepItems[pi3].name=val;
          state.data.prepItems[pi3]._ts=Date.now();
          break;
        }
      }
      saveData();renderPrep();
    };
  }
  /* 删除物品 */
  var delItemBtns=p.querySelectorAll('[data-action="delPrepItem"]');
  for(var dpi=0;dpi<delItemBtns.length;dpi++){
    delItemBtns[dpi].onclick=function(){
      var id=this.getAttribute('data-id');
      for(var pi4=0;pi4<state.data.prepItems.length;pi4++){
        if(state.data.prepItems[pi4].id===id){
          state.data.prepItems[pi4]._deleted=true;
          state.data.prepItems[pi4]._ts=Date.now();
          break;
        }
      }
      saveData();renderPrep();showToast('已删除');
    };
  }
  /* 成员确认按钮：点亮/取消「我备好了」 */
  var readyBtns=p.querySelectorAll('[data-action="toggleReady"]');
  for(var rb=0;rb<readyBtns.length;rb++){
    readyBtns[rb].onclick=function(){
      var id=this.getAttribute('data-id');
      var mid=this.getAttribute('data-mid');
      for(var pi5=0;pi5<state.data.prepItems.length;pi5++){
        if(state.data.prepItems[pi5].id===id){
          if(!state.data.prepItems[pi5].readyBy){state.data.prepItems[pi5].readyBy={};}
          if(state.data.prepItems[pi5].readyBy[mid]){
            delete state.data.prepItems[pi5].readyBy[mid];
          }else{
            state.data.prepItems[pi5].readyBy[mid]=true;
          }
          state.data.prepItems[pi5]._ts=Date.now();
          break;
        }
      }
      saveData();renderPrep();
    };
  }
  /* 板块底部添加物品（回车确认） */
  var addInputs=p.querySelectorAll('.prep-add-input');
  for(var ai=0;ai<addInputs.length;ai++){
    addInputs[ai].onkeydown=function(ev){
      if(ev.keyCode!==13){return;}
      var cid=this.getAttribute('data-cat');
      var val=this.value.trim();
      if(!val){return;}
      state.data.prepItems.push({
        id:genId(),cat:cid,name:val,readyBy:{},_ts:Date.now()
      });
      saveData();renderPrep();
    };
  }
}
/* 添加板块的表单 */
function showAddBoardForm(){
  var sheet=document.getElementById('formModalSheet');
  sheet.innerHTML='<div class="form-modal-title">添加板块<button id="closeForm">✕</button></div>'+
    '<div class="form-row"><div style="flex:1"><label>板块名称</label><input type="text" id="fBoardName" placeholder="如：户外装备"></div></div>'+
    '<button class="btn btn-primary btn-block" style="margin-top:12px" id="saveBoardBtn">保存</button>';
  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  var inp=document.getElementById('fBoardName');
  if(inp){inp.focus();}
  document.getElementById('saveBoardBtn').onclick=function(){
    var name=document.getElementById('fBoardName').value.trim();
    if(!name){showToast('请填写板块名称');return;}
    /* 同名板块已存在就不重复加 */
    var existing=aliveList(state.data.prepCategories);
    for(var i=0;i<existing.length;i++){
      if(existing[i].name===name){showToast('已有这个板块了');return;}
    }
    state.data.prepCategories.push({id:genId(),name:name,_ts:Date.now()});
    saveData();
    document.getElementById('formModal').classList.remove('show');
    renderPrep();showToast('已添加板块');
  };
}
"""

src = src[:start] + NEW + src[end:]
open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
