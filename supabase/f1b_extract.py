#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 renderSettlement 的计算部分抽成 computeSettlement()，并支持已结清基线"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

OLD_HEAD = """function renderSettlement(data){
  var members=aliveList(data.members);
  var expenses=data.expenses||[];
  var N=members.length;
  if(N<2){return '';}
  var i,payer,payerName;
  /* 1. 统计每人实付总额 */
  var paid={};
  for(i=0;i<N;i++){paid[members[i].id]=0;}
  var hasPayerRecords=false;
  for(i=0;i<expenses.length;i++){
    var e=expenses[i];
    var amt=Number(e.amount)||0;
    if(e.payer&&paid.hasOwnProperty(e.payer)){
      paid[e.payer]+=amt;
      hasPayerRecords=true;
    }
  }
  /* 2. 统计每人应承担金额（集体AA按参与人分摊 + 个人物品自付） */
  var owed={};
  for(i=0;i<N;i++){owed[members[i].id]=0;}
  var collectiveTotal=0,hasUnequal=false;
  for(i=0;i<expenses.length;i++){
    var e2=expenses[i];
    var amt2=Number(e2.amount)||0;
    if(e2.type==='collective'){
      collectiveTotal+=amt2;
      /* parts 为空 = 全员参与（兼容老数据）；有 parts = 只在这些人之间分 */
      var pl=[],j;
      if(e2.parts&&e2.parts.length){
        for(j=0;j<e2.parts.length;j++){
          if(owed.hasOwnProperty(e2.parts[j])){pl.push(e2.parts[j]);}
        }
        if(pl.length&&pl.length<N){hasUnequal=true;}
      }
      /* 参与人都被删了的话退回全员分摊，避免这笔钱没人承担 */
      if(!pl.length){for(j=0;j<N;j++){pl.push(members[j].id);}}
      var each=amt2/pl.length;
      for(j=0;j<pl.length;j++){owed[pl[j]]+=each;}
    }else{
      /* 个人物品：付款人自付，老数据无 payer 则跳过 */
      if(e2.payer&&owed.hasOwnProperty(e2.payer)){
        owed[e2.payer]+=amt2;
      }
    }
  }
  /* 3. 计算每人净额（实付 - 应承担） */"""

NEW_HEAD = """/* 纯计算：返回 {members,N,paid,owed,net,transfers,hasUnequal,hasPayerRecords,
                 collectiveTotal,settled,coveredCount}
   已标记结清时，会减去快照里的基线，只算快照之后新增的账。 */
function computeSettlement(data){
  var members=aliveList(data.members);
  var expenses=data.expenses||[];
  var N=members.length;
  if(N<2){return null;}
  var i,j;
  var settled=(data._meta&&data._meta.settled)||null;
  /* 1. 统计每人实付总额 */
  var paid={};
  for(i=0;i<N;i++){paid[members[i].id]=0;}
  var hasPayerRecords=false;
  for(i=0;i<expenses.length;i++){
    var e=expenses[i];
    var amt=Number(e.amount)||0;
    if(e.payer&&paid.hasOwnProperty(e.payer)){
      paid[e.payer]+=amt;
      hasPayerRecords=true;
    }
  }
  /* 2. 统计每人应承担金额（集体AA按参与人分摊 + 个人物品自付） */
  var owed={};
  for(i=0;i<N;i++){owed[members[i].id]=0;}
  var collectiveTotal=0,hasUnequal=false;
  for(i=0;i<expenses.length;i++){
    var e2=expenses[i];
    var amt2=Number(e2.amount)||0;
    if(e2.type==='collective'){
      collectiveTotal+=amt2;
      /* parts 为空 = 全员参与（兼容老数据）；有 parts = 只在这些人之间分 */
      var pl=[];
      if(e2.parts&&e2.parts.length){
        for(j=0;j<e2.parts.length;j++){
          if(owed.hasOwnProperty(e2.parts[j])){pl.push(e2.parts[j]);}
        }
        if(pl.length&&pl.length<N){hasUnequal=true;}
      }
      /* 参与人都被删了的话退回全员分摊，避免这笔钱没人承担 */
      if(!pl.length){for(j=0;j<N;j++){pl.push(members[j].id);}}
      var each=amt2/pl.length;
      for(j=0;j<pl.length;j++){owed[pl[j]]+=each;}
    }else{
      /* 个人物品：付款人自付，老数据无 payer 则跳过 */
      if(e2.payer&&owed.hasOwnProperty(e2.payer)){
        owed[e2.payer]+=amt2;
      }
    }
  }
  /* 2.5 已结清基线：减掉快照里那部分，只算之后新增的
     这样"已经付过的钱"不会每次打开又被算一遍 */
  var coveredCount=0,coveredTotal=0;
  if(settled){
    coveredCount=settled.count||0;
    coveredTotal=settled.total||0;
    for(i=0;i<N;i++){
      var mid=members[i].id;
      if(settled.paid&&settled.paid.hasOwnProperty(mid)){paid[mid]-=(Number(settled.paid[mid])||0);}
      if(settled.owed&&settled.owed.hasOwnProperty(mid)){owed[mid]-=(Number(settled.owed[mid])||0);}
    }
  }
  /* 3. 计算每人净额（实付 - 应承担） */"""

sub('extract computeSettlement head', OLD_HEAD, NEW_HEAD)

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
