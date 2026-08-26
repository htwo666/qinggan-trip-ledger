# -*- coding: utf-8 -*-
"""计划渲染：区间显示 / 多人徽章 / 创建者色块 / 日历跨天"""
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


# ── 1. 分类逻辑：用结束日判逾期，进行中单独一类 ────────────────
sub('计划分类',
"""  /* 待办分类：逾期 / 今日 / 未来 */
  var overdueTodos=[],todayTodos=[],upcomingTodos=[];
  for(var ti=0;ti<todos.length;ti++){
    if(todos[ti].done){continue;}
    if(todos[ti].date<today){overdueTodos.push(todos[ti]);}
    else if(todos[ti].date===today){todayTodos.push(todos[ti]);}
    else{upcomingTodos.push(todos[ti]);}
  }""",
"""  /* 计划分类：逾期 / 今天要做 / 未来
     逾期看结束日 —— 9.25–9.30 的阶段计划，9.27 那天还在进行中，不该标红。
     今天要做包含「今天正好落在区间里」的阶段计划。 */
  var overdueTodos=[],todayTodos=[],upcomingTodos=[];
  for(var ti=0;ti<todos.length;ti++){
    var _p=todos[ti];
    if(_p.done){continue;}
    if(planEnd(_p)&&planEnd(_p)<today){overdueTodos.push(_p);}
    else if(planCoversDate(_p,today)){todayTodos.push(_p);}
    else{upcomingTodos.push(_p);}
  }""")


# ── 2. 今天要处理区：逾期/今日文案带区间 ──────────────────────
sub('今日区 逾期项',
"""      todayHtml+='<div class="today-item overdue"><span class="label"><strong>【逾期】</strong>'+escapeHtml(overdueTodos[j].text)+'</span><button class="btn btn-sm btn-primary act-btn" data-action="doneTodo" data-id="'+overdueTodos[j].id+'">完成</button></div>';""",
"""      todayHtml+='<div class="today-item overdue"><span class="label"><strong>【逾期】</strong>'+escapeHtml(overdueTodos[j].text)+
        '<span class="plan-range">'+planDateLabel(overdueTodos[j])+'</span>'+planByBadge(overdueTodos[j])+
        '</span><button class="btn btn-sm btn-primary act-btn" data-action="doneTodo" data-id="'+overdueTodos[j].id+'">完成</button></div>';""")

sub('今日区 今日项',
"""      todayHtml+='<div class="today-item"><span class="label"><strong>【今日】</strong>'+escapeHtml(todayTodos[t2].text)+'</span><button class="btn btn-sm btn-primary act-btn" data-action="doneTodo" data-id="'+todayTodos[t2].id+'">完成</button></div>';""",
"""      /* 阶段计划标「进行中」，单日标「今日」，区分开更清楚 */
      var _lbl=planIsRange(todayTodos[t2])?'【进行中】':'【今日】';
      todayHtml+='<div class="today-item"><span class="label"><strong>'+_lbl+'</strong>'+escapeHtml(todayTodos[t2].text)+
        '<span class="plan-range">'+planDateLabel(todayTodos[t2])+'</span>'+planByBadge(todayTodos[t2])+
        '</span><button class="btn btn-sm btn-primary act-btn" data-action="doneTodo" data-id="'+todayTodos[t2].id+'">完成</button></div>';""")


# ── 3. 计划清单卡片 ─────────────────────────────────────────
sub('清单标题',
"""  var todoCard='<div class="card"><div class="card-title">'+svgIcon('today')+'待办清单 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（未完成 '+(overdueTodos.length+todayTodos.length+upcomingTodos.length)+' · 已完成 '+doneTodos.length+'）</span></div>';""",
"""  var todoCard='<div class="card"><div class="card-title">'+svgIcon('today')+'计划清单 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（未完成 '+(overdueTodos.length+todayTodos.length+upcomingTodos.length)+' · 已完成 '+doneTodos.length+'）</span></div>';""")

sub('清单空态',
"""    todoCard+='<div class="empty">'+svgIcon('check')+'<div>暂无待办，点下方「添加待办」</div></div>';""",
"""    todoCard+='<div class="empty">'+svgIcon('check')+'<div>暂无计划，点下方「添加计划」</div></div>';""")

sub('清单条目',
"""    var allOpen=overdueTodos.concat(todayTodos).concat(upcomingTodos);
    for(var a=0;a<allOpen.length;a++){
      var od=allOpen[a].date<today;
      todoCard+='<div class="todo-item"><input type="checkbox" data-id="'+allOpen[a].id+'" class="todo-check"><span class="text">'+(od?'<span style="color:var(--danger);font-weight:600">[逾期] </span>':'')+escapeHtml(allOpen[a].text)+' <span style="color:var(--text-light);font-size:0.72rem">· '+fmtDate(allOpen[a].date)+'前</span>'+(allOpen[a].owner?ownerBadge(allOpen[a].owner):'')+'</span><button class="del-todo" data-action="delTodo" data-id="'+allOpen[a].id+'">'+svgIcon('trash')+'</button></div>';
    }""",
"""    var allOpen=overdueTodos.concat(todayTodos).concat(upcomingTodos);
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
    }""")


# ── 4. 日历：跨天计划在每一天都显示 ──────────────────────────
sub('日历跨天',
"""  var byDate={};
  for(var i=0;i<todos.length;i++){
    if(todos[i].done){continue;}
    var d=todos[i].date;
    if(d&&!byDate[d]){byDate[d]=[];}
    if(d){byDate[d].push(todos[i].text);}
  }""",
"""  /* 把每个计划铺到它覆盖的每一天，阶段计划才会在日历上连成一片。
     顺便记下创建者颜色，日历格子里画一条对应颜色的小条。 */
  var byDate={},barColor={};
  for(var i=0;i<todos.length;i++){
    if(todos[i].done){continue;}
    var a=planStart(todos[i]),b=planEnd(todos[i])||a;
    if(!a){continue;}
    var cur=a,guard=0;
    while(cur<=b&&guard<400){
      if(!byDate[cur]){byDate[cur]=[];}
      byDate[cur].push(todos[i]);
      if(!barColor[cur]){barColor[cur]=planByColor(todos[i].by||planByName(todos[i]));}
      cur=addDays(cur,1);
      guard++;
    }
  }""")

sub('日历格子',
"""    var dot=byDate[ds]?('·'+byDate[ds].length):'';
    html+='<div class="'+cls+'" data-date="'+ds+'"><span class="day-num">'+day+'</span><span class="day-dot">'+dot+'</span></div>';""",
"""    var dot=byDate[ds]?('·'+byDate[ds].length):'';
    var bar=byDate[ds]?('<span class="day-bar" style="background:'+barColor[ds]+'"></span>'):'';
    html+='<div class="'+cls+'" data-date="'+ds+'"><span class="day-num">'+day+'</span><span class="day-dot">'+dot+'</span>'+bar+'</div>';""")

sub('日历标题',
"""'待办日历 · '+y+'年'+(mo+1)+'月'""",
"""'计划日历 · '+y+'年'+(mo+1)+'月'""")

sub('日历图例',
"""<span class="dot" style="background:var(--primary-bg);border:1px solid var(--primary-light)"></span>有待办</span>""",
"""<span class="dot" style="background:var(--primary-bg);border:1px solid var(--primary-light)"></span>有计划</span>""")

sub('日历选中明细',
"""    var sels=byDate[sel]||[];
    html+='<div class="cal-selected-list"><div class="cal-sel-title">'+fmtDate(sel)+' 待办（'+(sels.length? sels.length:'0')+'）</div>';
    if(sels.length){
      for(var s2=0;s2<sels.length;s2++){html+='<div style="font-size:0.78rem;color:var(--text);padding:2px 0">· '+escapeHtml(sels[s2])+'</div>';}
    }else{html+='<div style="font-size:0.75rem;color:var(--text-light)">这天没有待办</div>';}""",
"""    var sels=byDate[sel]||[];
    html+='<div class="cal-selected-list"><div class="cal-sel-title">'+fmtDate(sel)+' 计划（'+(sels.length? sels.length:'0')+'）</div>';
    if(sels.length){
      for(var s2=0;s2<sels.length;s2++){
        var _sp=sels[s2];
        html+='<div style="font-size:0.78rem;color:var(--text);padding:3px 0;border-left:3px solid '+
          planByColor(_sp.by||planByName(_sp))+';padding-left:6px;margin-bottom:2px">'+
          escapeHtml(_sp.text)+
          (planIsRange(_sp)?('<span class="plan-range">'+planDateLabel(_sp)+'</span>'):'')+
          ownersBadges(_sp)+planByBadge(_sp)+'</div>';
      }
    }else{html+='<div style="font-size:0.75rem;color:var(--text-light)">这天没有计划</div>';}""")


io.open(P, 'w', encoding='utf-8').write(src)
print('\n%d/11  %d → %d bytes' % (len(ok), before, len(src)))
