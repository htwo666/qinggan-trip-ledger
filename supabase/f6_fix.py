# -*- coding: utf-8 -*-
"""
修两个 bug + AI 全能记录：

bug1：AI 面板打开后按返回键直接退出应用（没 pushState，也没拦 popstate）
bug2：确认框和 AI 面板 z-index 都是 200，面板在 DOM 里更靠后所以压住了确认框
      —— 这就是"AI 不能记账"的真相：其实解析成功了、确认框也弹了，只是被挡得看不见

AI 全能：@@RECORD 只能记花费，扩展成 @@ADD，支持
  expense  途中花费
  prep     必买物品（要买啥）
  todo     待办（几号订啥票）
  outfit   穿搭
"""
import io, sys

P = 'index.html'
src = io.open(P, encoding='utf-8').read()
before = len(src.encode('utf-8'))
ok = []

def sub(name, old, new, count=1):
    global src
    if old not in src:
        print('  MISS  %s' % name); return False
    n = src.count(old)
    if n != count:
        print('  WARN  %s 出现 %d 次（预期 %d）' % (name, n, count))
    src = src.replace(old, new, count)
    ok.append(name); print('  OK    %s' % name); return True

# ---------------------------------------------------------------- bug2: 层级
# AI 面板 200 / backdrop 199 → 确认框和表单弹层必须更高
sub('confirm z-index',
    '.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;',
    '.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:260;')

sub('form-modal z-index',
    '.form-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;',
    '.form-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:260;')

# ---------------------------------------------------------------- bug1: 返回键
sub('back stack helpers',
    '/* 打开/关闭 AI 面板 */\nfunction openAIPanel(){',
    '''/* ---------- 返回键 / 浏览器后退 统一管理 ----------
   手机上从 AI 面板按返回键，原来会直接退出整个应用（因为压根没往历史里放东西）。
   现在每打开一层浮层就 pushState 一条，返回键先关浮层，关完了才真的退出。 */
var uiStack=[];      /* 每项 {name:'ai', close:fn} */
function pushUILayer(name,closeFn){
  /* 同名的先清掉，避免重复叠加 */
  for(var i=uiStack.length-1;i>=0;i--){
    if(uiStack[i].name===name){uiStack.splice(i,1);}
  }
  uiStack.push({name:name,close:closeFn});
  try{history.pushState({qgLayer:name,depth:uiStack.length},'',location.href);}catch(e){}
}
/* 用户主动点了关闭按钮：把历史里那条也退掉，不然会多出一次空的返回 */
function popUILayer(name){
  var idx=-1,i;
  for(i=uiStack.length-1;i>=0;i--){if(uiStack[i].name===name){idx=i;break;}}
  if(idx<0){return;}
  uiStack.splice(idx,1);
  if(history.state&&history.state.qgLayer){
    uiStack.__skip=(uiStack.__skip||0)+1;   /* 标记：接下来这次 popstate 是我自己触发的 */
    try{history.back();}catch(e){uiStack.__skip=0;}
  }
}
window.addEventListener('popstate',function(){
  /* 自己调 history.back() 引起的，浮层已经关了，别再关一层 */
  if(uiStack.__skip>0){uiStack.__skip--;return;}
  if(uiStack.length){
    var top=uiStack.pop();
    try{top.close&&top.close();}catch(e){}
    /* 还有更下面的浮层 → 补一条历史，保证下次返回键还能接着关 */
    if(uiStack.length){
      try{history.pushState({qgLayer:uiStack[uiStack.length-1].name,depth:uiStack.length},'',location.href);}catch(e){}
    }
  }
});
/* 确认框 / 表单弹层也纳入返回键管理 */
function closeTopModal(){
  var cm=document.getElementById('confirmModal');
  var fm=document.getElementById('formModal');
  if(cm&&cm.classList.contains('show')){cm.classList.remove('show');return true;}
  if(fm&&fm.classList.contains('show')){fm.classList.remove('show');return true;}
  return false;
}
/* 打开/关闭 AI 面板 */
function openAIPanel(){''')

sub('openAIPanel push',
    """  document.getElementById('aiPanel').classList.add('open');
  document.getElementById('aiBackdrop').classList.add('open');""",
    """  document.getElementById('aiPanel').classList.add('open');
  document.getElementById('aiBackdrop').classList.add('open');
  pushUILayer('ai',function(){
    document.getElementById('aiPanel').classList.remove('open');
    document.getElementById('aiBackdrop').classList.remove('open');
  });""")

sub('closeAIPanel pop',
    """function closeAIPanel(){
  document.getElementById('aiPanel').classList.remove('open');
  document.getElementById('aiBackdrop').classList.remove('open');""",
    """function closeAIPanel(){
  document.getElementById('aiPanel').classList.remove('open');
  document.getElementById('aiBackdrop').classList.remove('open');
  popUILayer('ai');""")

# 确认框也纳入返回键（showConfirm 里 add show 的地方）
sub('showConfirm push layer',
    """  confirmCallback=cb;
  document.getElementById('confirmModal').classList.add('show');""",
    """  confirmCallback=cb;
  document.getElementById('confirmModal').classList.add('show');
  pushUILayer('confirm',function(){document.getElementById('confirmModal').classList.remove('show');});""")

# ---------------------------------------------------------------- AI 全能记录
sub('generalize parser',
    """function parseAIRecord(text){
  if(!text||text.indexOf('@@RECORD')<0){return null;}
  var i=text.indexOf('@@RECORD');
  var start=text.indexOf('{',i);""",
    """/* 兼容老的 @@RECORD，同时支持新的 @@ADD */
function parseAIRecord(text){
  if(!text){return null;}
  var tag=null;
  if(text.indexOf('@@ADD')>=0){tag='@@ADD';}
  else if(text.indexOf('@@RECORD')>=0){tag='@@RECORD';}
  if(!tag){return null;}
  var i=text.indexOf(tag);
  var start=text.indexOf('{',i);""")

sub('parser return any kind',
    """  try{
    var o=JSON.parse(text.slice(start,end+1));
    if(!o||!(Number(o.amount)>0)){return null;}
    return {obj:o,raw:text.slice(i,end+1)};
  }catch(e){return null;}
}""",
    """  try{
    var o=JSON.parse(text.slice(start,end+1));
    if(!o){return null;}
    /* 老格式没有 kind，默认当花费 */
    if(!o.kind){o.kind='expense';}
    /* 花费必须有正数金额，其他类型不强求 */
    if(o.kind==='expense'&&!(Number(o.amount)>0)){return null;}
    if(o.kind==='prep'&&!o.name){return null;}
    if(o.kind==='todo'&&!o.text){return null;}
    if(o.kind==='outfit'&&!o.desc){return null;}
    return {obj:o,raw:text.slice(i,end+1)};
  }catch(e){return null;}
}
/* 找一个成员 id：优先按名字匹配，匹配不上就用自己，再不行用第一个 */
function resolveMemberId(name){
  var members=aliveMembers(),i;
  if(name){
    for(i=0;i<members.length;i++){
      if(members[i].name===String(name).trim()){return members[i].id;}
    }
  }
  var mine=myMember();
  if(mine){return mine.id;}
  return members.length?members[0].id:'';
}
/* 日期兜底：AI 给的不合法就用今天 */
function safeDate(s){
  if(s&&/^\\d{4}-\\d{2}-\\d{2}$/.test(String(s).trim())){return String(s).trim();}
  return todayStr();
}
/* @@ADD 总入口：按 kind 分派 */
function applyAIAdd(o){
  var k=o.kind||'expense';
  if(k==='expense'){confirmAIRecord(o);return;}
  if(k==='prep'){confirmAIPrep(o);return;}
  if(k==='todo'){confirmAITodo(o);return;}
  if(k==='outfit'){confirmAIOutfit(o);return;}
  showToast('AI 给了个看不懂的类型：'+k);
}
/* 必买物品 */
function confirmAIPrep(o){
  var cats=['服饰装备','个护美妆','药品保健','证件','食品','其他'];
  var cat=o.category||'其他',okc=false,i;
  for(i=0;i<cats.length;i++){if(cats[i]===cat){okc=true;break;}}
  if(!okc){cat='其他';}
  var price=Number(o.price)||0;
  var owner=resolveMemberId(o.owner);
  var body='物品：'+o.name+'\\n'+
    '分类：'+cat+'\\n'+
    (price>0?('预估价：'+fmtMoney(price)+'\\n'):'')+
    '购买渠道：'+(o.channel||'待定')+'\\n'+
    '负责人：'+(owner?memberNameById(owner):'未指定')+'\\n'+
    '\\n加到必买清单吗？';
  showConfirm('AI 帮你加进必买清单',body,function(){
    state.data.prepItems.push({
      id:genId(),category:cat,name:String(o.name).trim(),
      price:price,channel:o.channel||'待定',owner:owner,
      bought:false,overdue:false,_ts:Date.now()
    });
    saveData();showToast('已加入必买清单');renderAll();
  });
}
/* 待办（订票这种） */
function confirmAITodo(o){
  var date=safeDate(o.date);
  var owner=resolveMemberId(o.owner);
  var body='内容：'+o.text+'\\n'+
    '日期：'+fmtDate(date)+'\\n'+
    '负责人：'+(owner?memberNameById(owner):'未指定')+'\\n'+
    '\\n加到待办里吗？';
  showConfirm('AI 帮你加个待办',body,function(){
    var t={id:genId(),date:date,text:String(o.text).trim(),
           owner:owner,done:false,_ts:Date.now()};
    state.data.todos.push(t);saveData();
    var dp=t.date.split('-');
    if(dp.length===3){state.calYear=parseInt(dp[0],10);state.calMonth=parseInt(dp[1],10)-1;state.calSel=t.date;}
    showToast('已加入待办');renderAll();
  });
}
/* 穿搭 */
function confirmAIOutfit(o){
  var date=safeDate(o.date);
  var person=o.person?String(o.person).trim():(currentNickname()||'未署名');
  var body='日期：'+fmtDate(date)+'\\n'+
    '谁：'+person+'\\n'+
    '搭配：'+o.desc+'\\n'+
    '\\n记到穿搭里吗？';
  showConfirm('AI 帮你记个穿搭',body,function(){
    state.data.outfits.push({
      id:genId(),date:date,person:person,
      desc:String(o.desc).trim(),_ts:Date.now()
    });
    saveData();showToast('已记录穿搭');renderAll();
  });
}""")

sub('dispatch via applyAIAdd',
    "        setTimeout(function(){confirmAIRecord(rec.obj);},400);",
    "        setTimeout(function(){applyAIAdd(rec.obj);},400);")

sub('clean msg wording',
    "        updateLastAIMessage(clean||'我帮你记一笔（见下方确认框）');",
    "        updateLastAIMessage(clean||'好，我帮你加上（见下方确认框）');")

# ---------------------------------------------------------------- prompt 升级
old_prompt = """      '5. 帮用户记账：用户说"午饭花了120""加油300老王没去"这类话时，'+
        '你要回一个记账指令，格式严格如下（单独一行，前后不要加代码块标记）：\\n'+
      '@@RECORD{"amount":120,"category":"餐饮","type":"collective","note":"午饭","exclude":["老王"]}\\n'+"""

new_prompt = """      '5. 帮用户记东西：用户说"午饭花了120""帮我加个登山杖""9月20号订莫高窟门票"这类话时，'+
        '你要回一个指令，单独占一行，前后不要加代码块标记。四种类型：\\n'+
      '   记花费：@@ADD{"kind":"expense","amount":120,"category":"餐饮","type":"collective","note":"午饭","exclude":["老王"]}\\n'+
      '   加必买物品：@@ADD{"kind":"prep","name":"登山杖","category":"服饰装备","price":80,"channel":"淘宝","owner":"小美"}\\n'+
      '   加待办：@@ADD{"kind":"todo","date":"2026-09-20","text":"订莫高窟门票","owner":"阿杰"}\\n'+
      '   记穿搭：@@ADD{"kind":"outfit","date":"2026-09-26","person":"小美","desc":"冲锋衣+速干裤"}\\n'+
      '  必买物品的 category 从 服饰装备/个护美妆/药品保健/证件/食品/其他 里挑\\n'+
      '  待办的 date 必须是 YYYY-MM-DD；用户说"下周三"这种相对时间，你按今天的日期算成具体日期\\n'+
      '  owner/person 填成员名字，没说就别填这个字段\\n'+
      '  一次只输出一条指令。用户一句话里说了好几件事，先办最主要的那件，其余的问一句再说\\n'+"""

sub('prompt multi-kind', old_prompt, new_prompt)

# ---------------------------------------------------------------- 写回
if not ok:
    print('!! 一条都没打上，中止'); sys.exit(1)

io.open(P, 'w', encoding='utf-8').write(src)
after = len(src.encode('utf-8'))
print('\n共 %d 处，%d -> %d bytes' % (len(ok), before, after))
