#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 优化（全部围绕体验）：
 1. 把真实账本数据喂给 AI（原来只有行程，AI 根本不知道你花了多少，问"超支了吗"只能瞎猜）
 2. 自然语言记账："午饭花了120，老王没吃" → 自动解析成账目，确认后入账
 3. 一键花费体检：AI 看真实数据给省钱建议
 4. 硬编码的"4人11天"改成动态
"""
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

# ============ 1. 账本快照喂给 AI ============
sub('ledger context for AI',
"""function buildAISystemPrompt(){""",
"""/* 把真实账本浓缩成文字喂给 AI。
   原来 AI 只知道行程不知道账，用户问"超支了吗""还能花多少"只能瞎编。
   控制在几百字，不然每次请求都烧 token。 */
function buildLedgerContext(){
  var d=viewData();
  var members=aliveList(d.members);
  var budget=getDailyBudget();
  var i,s='';

  var preSum=0;
  for(i=0;i<d.prepaid.length;i++){preSum+=Number(d.prepaid[i].amount)||0;}
  var enC=0,enP=0,byCat={},byDate={};
  for(i=0;i<d.expenses.length;i++){
    var e=d.expenses[i],a=Number(e.amount)||0;
    if(e.type==='collective'){enC+=a;}else{enP+=a;}
    byCat[e.category]=(byCat[e.category]||0)+a;
    if(e.date){byDate[e.date]=(byDate[e.date]||0)+a;}
  }

  s+='\\n【当前账本实况】（这是真实数据，回答花钱相关问题请基于它）\\n';
  s+='- 成员（'+members.length+' 人）：';
  var mn=[];
  for(i=0;i<members.length;i++){mn.push(members[i].name);}
  s+=mn.join('、')+'\\n';
  s+='- 预付款已花：'+fmtMoney(preSum)+'（机票/租车/住宿这类出发前付的）\\n';
  s+='- 途中集体AA：'+fmtMoney(enC)+'；途中个人花费：'+fmtMoney(enP)+'\\n';
  s+='- 总计已花：'+fmtMoney(preSum+enC+enP)+'\\n';
  s+='- 每日预算设定：每人每天 '+fmtMoney(budget)+'\\n';

  /* 分类排行 */
  var cats=[];
  for(var k in byCat){if(byCat.hasOwnProperty(k)){cats.push([k,byCat[k]]);}}
  cats.sort(function(a,b){return b[1]-a[1];});
  if(cats.length){
    var cs=[];
    for(i=0;i<Math.min(5,cats.length);i++){cs.push(cats[i][0]+' '+fmtMoney(cats[i][1]));}
    s+='- 花得最多的类别：'+cs.join('，')+'\\n';
  }

  /* 今日 */
  var a2=budgetAlert();
  s+='- 今天（'+todayStr()+'）已花 '+fmtMoney(a2.spent)+'，今日额度 '+fmtMoney(a2.dayBudget)+
     '，用了 '+a2.pct+'%'+(a2.level==='over'?'（已超支 '+fmtMoney(a2.over)+'）':'')+'\\n';

  /* 结算状态 */
  var R=computeSettlement(d);
  if(R){
    if(R.settled){
      s+='- 结算：'+(R.settled.at||'')+' 已标记结清（'+(R.settled.count||0)+' 笔 / '+
         fmtMoney(R.settled.total||0)+'）';
      s+=R.transfers.length?('，之后新增 '+R.transfers.length+' 笔待结\\n'):'，之后没有新账\\n';
    }
    if(R.transfers.length){
      var ts=[];
      for(i=0;i<R.transfers.length;i++){
        ts.push(R.transfers[i].from+'给'+R.transfers[i].to+' '+fmtMoney(R.transfers[i].amt));
      }
      s+='- 待结算：'+ts.join('；')+'\\n';
    }else if(!R.settled){
      s+='- 待结算：大家已平衡，不用互相转账\\n';
    }
  }

  /* 最近 5 笔，让 AI 有具体的话可说 */
  if(d.expenses.length){
    var recent=d.expenses.slice(-5).reverse(),rs=[];
    for(i=0;i<recent.length;i++){
      var r2=recent[i];
      rs.push(r2.date+' '+r2.category+' '+fmtMoney(r2.amount)+
              (r2.parts&&r2.parts.length?'(仅'+r2.parts.length+'人分)':''));
    }
    s+='- 最近几笔：'+rs.join('；')+'\\n';
  }
  return s;
}

function buildAISystemPrompt(){""")

# ============ 2. 把账本上下文插进 prompt，并去掉硬编码人数天数 ============
sub('inject ledger + dynamic counts',
"""  prompt+='\\n【能力】\\n'+""",
"""  /* 真实账本数据 */
  prompt+=buildLedgerContext();
  prompt+='\\n【能力】\\n'+""")

sub('dynamic member count in prompt',
"""  var prompt='你是"青甘旅伴"，一个为4人11天青甘大环线自驾游设计的AI助手。\\n\\n'+
    '【行程信息】\\n'+
    '- 时间：2026-09-25 至 2026-10-05，4 人自驾（小美、阿杰、丸子、老王）\\n'+""",
"""  var mList=aliveMembers(),mNames=[];
  for(var mi=0;mi<mList.length;mi++){mNames.push(mList[mi].name);}
  var nPeople=Math.max(1,mList.length);
  var nDays=Math.abs(daysBetween(TRIP_START,TRIP_END))+1;
  var prompt='你是"青甘旅伴"，一个为'+nPeople+'人'+nDays+'天青甘大环线自驾游设计的AI助手。\\n\\n'+
    '【行程信息】\\n'+
    '- 时间：'+TRIP_START+' 至 '+TRIP_END+'，'+nPeople+' 人自驾'+
    (mNames.length?'（'+mNames.join('、')+'）':'')+'\\n'+""")

# ============ 3. 能力清单升级 + 记账指令说明 ============
sub('ai capabilities upgrade',
"""    '4. 记账与预算贴士、AA 结算建议\\n'+""",
"""    '4. 记账与预算贴士、AA 结算建议（你能看到真实账本，请基于实际数字回答，别编数字）\\n'+
    '5. 帮用户记账：用户说"午饭花了120""加油300老王没去"这类话时，'+
      '你要回一个记账指令，格式严格如下（单独一行，前后不要加代码块标记）：\\n'+
      '@@RECORD{"amount":120,"category":"餐饮","type":"collective","note":"午饭","exclude":["老王"]}\\n'+
      '  - amount 必填数字；category 从 '+EXPENSE_CATEGORIES.join('/')+' 里挑最接近的\\n'+
      '  - type：大家一起花的用 collective，某人自己买的用 personal\\n'+
      '  - exclude 可选，填没参与的人的名字（用户说"某人没去/没吃"时）\\n'+
      '  - 指令那一行之外，再用一句话跟用户确认，比如"记好了，午饭120，老王没参与"\\n'+
      '  - 用户只是闲聊或问问题时，不要输出这个指令\\n'+""")

sub('renumber ai capabilities',
"""    '5. 闲聊逗闷子、讲笑话、缓解旅途疲惫\\n'+
    '6. 高原反应、安全提示\\n\\n'+""",
"""    '6. 闲聊逗闷子、讲笑话、缓解旅途疲惫\\n'+
    '7. 高原反应、安全提示\\n\\n'+""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
