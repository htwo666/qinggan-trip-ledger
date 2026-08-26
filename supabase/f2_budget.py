#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能 2/3 + 顺手优化：
  - 结算按钮绑定
  - 预算超支提醒（可自定义预算，超支/接近超支提示）
  - 导出图片（Canvas 渲染结算卡，微信可直接发/存相册）
  - 花费可编辑（原来只能删了重记）
"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# ============ 1. 结算 + 导出图片按钮绑定 ============
sub('bind settle & image btns',
"""  document.getElementById('exportJsonBtn').onclick=exportAllJson;""",
"""  var sb=document.getElementById('settleBtn');
  if(sb){sb.onclick=markSettled;}
  var usb=document.getElementById('unsettleBtn');
  if(usb){usb.onclick=unmarkSettled;}
  var imgb=document.getElementById('exportImgBtn');
  if(imgb){imgb.onclick=exportSettleImage;}
  document.getElementById('exportJsonBtn').onclick=exportAllJson;""")

# ============ 2. 汇总页工具栏加「导出图片」 ============
sub('add export image button',
"""  var toolbar='<div class="toolbar"><button class="btn btn-outline btn-sm" id="exportJsonBtn">'+svgIcon('download')+'导出JSON</button>""",
"""  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="exportImgBtn">'+svgIcon('download')+'导出图片发群</button><button class="btn btn-outline btn-sm" id="exportJsonBtn">'+svgIcon('download')+'导出JSON</button>""")

# ============ 3. 预算：可自定义 + 超支提醒 ============
sub('budget helpers',
"""/* ---------- 结算快照（已付清）----------""",
"""/* ---------- 预算 ----------
   默认每天 1000，可以自己改（存 _meta.dailyBudget，随云端同步）。 */
function getDailyBudget(){
  var m=(state.data&&state.data._meta)||{};
  var v=Number(m.dailyBudget);
  return (v&&v>0)?v:DAILY_BUDGET;
}
function setDailyBudget(v){
  if(!state.data._meta){state.data._meta={};}
  state.data._meta.dailyBudget=Number(v)||DAILY_BUDGET;
  state.data._metaTs=Date.now();
  saveData();
}
function editBudget(){
  var cur=getDailyBudget();
  showPrompt('修改每日预算','每人每天大概花多少（元）',String(cur),function(v){
    var n=Number(v);
    if(!n||n<=0){showToast('请输入大于 0 的数字');return;}
    setDailyBudget(n);
    showToast('每日预算已改为 '+fmtMoney(n));
    renderAll();
  });
}
/* 今日花了多少（只算途中花费） */
function todaySpent(){
  var d=viewData(),t=todayStr(),s=0;
  for(var i=0;i<d.expenses.length;i++){
    if(d.expenses[i].date===t){s+=Number(d.expenses[i].amount)||0;}
  }
  return s;
}
/* 预算预警：返回 {level:'ok'|'near'|'over', ...} */
function budgetAlert(){
  var budget=getDailyBudget();
  var members=Math.max(1,aliveMembers().length);
  var dayBudget=budget*(state.spaceMode==='team'?members:1);
  var spent=todaySpent();
  var pct=dayBudget>0?Math.round(spent/dayBudget*100):0;
  var level='ok';
  if(pct>100){level='over';}
  else if(pct>=80){level='near';}
  return {level:level,pct:pct,spent:spent,dayBudget:dayBudget,
          budget:budget,members:members,over:spent-dayBudget};
}
/* 今日预算提示条 */
function renderBudgetAlert(){
  var a=budgetAlert();
  if(a.level==='ok'&&a.spent===0){return '';}
  var bg,fg,icon,txt;
  if(a.level==='over'){
    bg='#fdecec';fg='#c0392b';icon='🚨';
    txt='今天超支 '+fmtMoney(a.over)+'（已花 '+fmtMoney(a.spent)+' / 预算 '+fmtMoney(a.dayBudget)+'）';
  }else if(a.level==='near'){
    bg='#fff6e5';fg='#b8730a';icon='⚠️';
    txt='今天快到预算了，已用 '+a.pct+'%（'+fmtMoney(a.spent)+' / '+fmtMoney(a.dayBudget)+'）';
  }else{
    bg='#eafaf1';fg='#1e7d52';icon='✅';
    txt='今天花了 '+fmtMoney(a.spent)+'，还剩 '+fmtMoney(a.dayBudget-a.spent)+' 额度';
  }
  return '<div style="display:flex;align-items:center;gap:8px;font-size:0.76rem;background:'+bg+
    ';color:'+fg+';padding:10px 12px;border-radius:10px;margin-bottom:12px;font-weight:500">'+
    '<span style="font-size:1rem;flex-shrink:0">'+icon+'</span><span style="flex:1">'+txt+'</span>'+
    '<a href="javascript:void(0)" id="editBudgetLink" style="color:'+fg+
    ';font-size:0.68rem;text-decoration:underline;flex-shrink:0;opacity:.75">改预算</a></div>';
}

/* ---------- 结算快照（已付清）----------""")

# ============ 4. 记账页顶部插预算提示 ============
sub('inject budget alert into expense page',
"""  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="addExpenseBtn">'+svgIcon('plus')+'记一笔</button>""",
"""  var alertHtml=renderBudgetAlert();
  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="addExpenseBtn">'+svgIcon('plus')+'记一笔</button>""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
