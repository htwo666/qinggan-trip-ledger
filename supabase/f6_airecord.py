#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 自然语言记账：解析 @@RECORD 指令，弹确认后入账"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    n=src.count(old)
    if n!=count: print('  WARN  %s 出现 %d 次（预期 %d）'%(name,n,count))
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# 1. 解析器
sub('parse AI record',
"""function sendAIMessage(text){""",
"""/* ---------- AI 自然语言记账 ----------
   AI 回复里带 @@RECORD{...} 时，解析成账目，弹确认框让用户过一眼再入账。
   不自动入账，因为 AI 偶尔会把金额听错，让用户确认一下更安全。 */
function parseAIRecord(text){
  if(!text||text.indexOf('@@RECORD')<0){return null;}
  var i=text.indexOf('@@RECORD');
  var start=text.indexOf('{',i);
  if(start<0){return null;}
  /* 手动找配对的右括号（JSON 里可能有嵌套） */
  var depth=0,end=-1;
  for(var j=start;j<text.length;j++){
    if(text[j]==='{'){depth++;}
    else if(text[j]==='}'){depth--;if(depth===0){end=j;break;}}
  }
  if(end<0){return null;}
  try{
    var o=JSON.parse(text.slice(start,end+1));
    if(!o||!(Number(o.amount)>0)){return null;}
    return {obj:o,raw:text.slice(i,end+1)};
  }catch(e){return null;}
}
/* 把 AI 解析出的对象转成真正的账目并确认入账 */
function confirmAIRecord(o){
  var members=aliveMembers();
  var isPersonal=state.spaceMode==='personal';
  var amount=Number(o.amount)||0;
  var cat=o.category||'其他';
  /* 类别兜底到合法值 */
  var okCat=false,ci;
  for(ci=0;ci<EXPENSE_CATEGORIES.length;ci++){
    if(EXPENSE_CATEGORIES[ci]===cat){okCat=true;break;}
  }
  if(!okCat){cat='其他';}
  var type=(o.type==='personal'||isPersonal)?'personal':'collective';
  var mine=myMember();
  var payer=isPersonal?(members.length?members[0].id:''):(mine?mine.id:(members.length?members[0].id:''));

  /* exclude 里的名字 → parts（排除这些人） */
  var parts=null,excluded=[];
  if(type==='collective'&&o.exclude&&o.exclude.length&&members.length>1){
    parts=[];
    for(var mi=0;mi<members.length;mi++){
      var skip=false;
      for(var xi=0;xi<o.exclude.length;xi++){
        if(members[mi].name===String(o.exclude[xi]).trim()){skip=true;excluded.push(members[mi].name);break;}
      }
      if(!skip){parts.push(members[mi].id);}
    }
    if(!parts.length||parts.length===members.length){parts=null;excluded=[];}
  }

  var payerName=payer?memberNameById(payer):'未指定';
  var body='金额：'+fmtMoney(amount)+'\\n'+
    '类别：'+cat+'\\n'+
    '方式：'+(type==='collective'?'集体AA':'个人物品')+'\\n'+
    '付款人：'+payerName+'\\n'+
    (parts?('参与分摊：'+parts.length+' 人（'+excluded.join('、')+' 不参与）\\n'):'')+
    (o.note?('备注：'+o.note+'\\n'):'')+
    '\\n确认记这一笔吗？';

  showConfirm('AI 帮你记一笔',body,function(){
    var exp={
      id:genId(),
      date:todayStr(),
      amount:amount,
      category:cat,
      type:type,
      payer:payer,
      note:o.note||'AI 记账',
      _ts:Date.now()
    };
    if(parts){exp.parts=parts;}
    state.data.expenses.push(exp);
    saveData();
    showToast('已记入账本');
    renderAll();
  });
}

function sendAIMessage(text){""")

# 2. 流式完成时触发解析；显示时把指令那行藏掉（用户不需要看 JSON）
sub('hook record on done',
"""    function(fullText){
      /* 完成 */
      hideAITyping();
      aiState.isStreaming=false;
      aiState.abortController=null;
      setAIStatus('在线 · DeepSeek',false);
      document.getElementById('aiSendBtn').disabled=false;
      saveAIHistory();
    },""",
"""    function(fullText){
      /* 完成 */
      hideAITyping();
      aiState.isStreaming=false;
      aiState.abortController=null;
      setAIStatus('在线 · DeepSeek',false);
      document.getElementById('aiSendBtn').disabled=false;
      /* AI 想帮记账：把指令从显示里抹掉，然后弹确认 */
      var rec=parseAIRecord(fullText);
      if(rec){
        var clean=fullText.replace(rec.raw,'').replace(/\\n{3,}/g,'\\n\\n').trim();
        updateLastAIMessage(clean||'我帮你记一笔（见下方确认框）');
        setTimeout(function(){confirmAIRecord(rec.obj);},400);
      }
      saveAIHistory();
    },""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
