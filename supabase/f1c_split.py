#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切分 computeSettlement（纯计算，return 结果）/ renderSettlement（纯渲染）"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# 1) 净额算完后：计算 transfers 然后 return，renderSettlement 从这里重新开始
sub('close compute / open render',
"""  /* 3. 计算每人净额（实付 - 应承担） */
  var net={};
  for(i=0;i<N;i++){
    var mid=members[i].id;
    net[mid]=paid[mid]-owed[mid];
  }
  /* 4. 输出统计概览卡片 */
  var settleHtml='<div class="card"><div class="card-title">'+svgIcon('users')+'AA 结算助手</div>';""",
"""  /* 3. 计算每人净额（实付 - 应承担） */
  var net={};
  for(i=0;i<N;i++){
    var mid2=members[i].id;
    net[mid2]=paid[mid2]-owed[mid2];
  }
  /* 4. 贪心匹配生成结算清单（谁给谁多少，转账次数最少） */
  var receivables=[],payables=[];
  for(i=0;i<N;i++){
    var m2=members[i];
    if(net[m2.id]>0.01){receivables.push({id:m2.id,name:m2.name,amt:net[m2.id]});}
    else if(net[m2.id]<-0.01){payables.push({id:m2.id,name:m2.name,amt:-net[m2.id]});}
  }
  receivables.sort(function(a,b){return b.amt-a.amt;});
  payables.sort(function(a,b){return b.amt-a.amt;});
  var transfers=[],ri=0,pi2=0;
  while(ri<receivables.length&&pi2<payables.length){
    var r=receivables[ri],py=payables[pi2];
    var xfer=Math.min(r.amt,py.amt);
    if(xfer>0.01){transfers.push({from:py.name,to:r.name,amt:xfer});}
    r.amt-=xfer;py.amt-=xfer;
    if(r.amt<0.01){ri++;}
    if(py.amt<0.01){pi2++;}
  }
  return {members:members,N:N,paid:paid,owed:owed,net:net,transfers:transfers,
          hasUnequal:hasUnequal,hasPayerRecords:hasPayerRecords,
          collectiveTotal:collectiveTotal,settled:settled,
          coveredCount:coveredCount,coveredTotal:coveredTotal};
}

function renderSettlement(data){
  var R=computeSettlement(data);
  if(!R){return '';}
  var members=R.members,N=R.N,paid=R.paid,owed=R.owed,net=R.net;
  var transfers=R.transfers,hasUnequal=R.hasUnequal,settled=R.settled;
  var i;
  var settleHtml='<div class="card"><div class="card-title">'+svgIcon('users')+'AA 结算助手</div>';
  /* 已结清横幅 */
  if(settled){
    settleHtml+='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;'+
      'font-size:0.74rem;background:#eafaf1;color:#1e7d52;padding:9px 11px;border-radius:8px;margin-bottom:10px">'+
      '<span>✅ '+escapeHtml(settled.at||'')+' 由 '+escapeHtml(settled.by||'某人')+
      ' 标记已结清（'+(settled.count||0)+' 笔 / '+fmtMoney(settled.total||0)+'）'+
      (transfers.length?'，下面是之后新增的账':'')+'</span>'+
      '<button class="btn btn-outline btn-sm" id="unsettleBtn" style="flex-shrink:0;padding:3px 9px;font-size:0.68rem">撤销</button></div>';
  }""")

# 2) 删掉渲染段里重复的 meId 定义之前的旧注释编号，并删掉后面重复的贪心段
sub('remove duplicate greedy block',
"""  settleHtml+='</tbody></table></div>';
  /* 6. 贪心算法生成结算清单（谁给谁多少） */
  var receivables=[],payables=[];
  for(i=0;i<N;i++){
    var m2=members[i];
    if(net[m2.id]>0.01){receivables.push({id:m2.id,name:m2.name,amt:net[m2.id]});}
    else if(net[m2.id]<-0.01){payables.push({id:m2.id,name:m2.name,amt:-net[m2.id]});}
  }
  /* 排序：金额大的先匹配 */
  receivables.sort(function(a,b){return b.amt-a.amt;});
  payables.sort(function(a,b){return b.amt-a.amt;});
  var transfers=[];
  var ri=0,pi2=0;
  while(ri<receivables.length&&pi2<payables.length){
    var r=receivables[ri],py=payables[pi2];
    var xfer=Math.min(r.amt,py.amt);
    if(xfer>0.01){
      transfers.push({from:py.name,to:r.name,amt:xfer});
    }
    r.amt-=xfer;py.amt-=xfer;
    if(r.amt<0.01){ri++;}
    if(py.amt<0.01){pi2++;}
  }
  /* 7. 输出结算清单 */
  if(transfers.length===0){
    settleHtml+='<div class="empty" style="padding:14px">'+svgIcon('check')+'<div>所有人已平衡，无需结算</div></div>';""",
"""  settleHtml+='</tbody></table></div>';
  /* 输出结算清单 */
  if(transfers.length===0){
    settleHtml+='<div class="empty" style="padding:14px">'+svgIcon('check')+'<div>'+
      (settled?'已结清，之后没有新增待结算的账':'所有人已平衡，无需结算')+'</div></div>';""")

# 3) 结算清单末尾加「标记已结清」按钮
sub('add markSettled button',
"""    settleHtml+='<div style="font-size:0.72rem;color:var(--text-light);margin-top:8px">💡 共 '+transfers.length+' 笔结算，总流转金额 '+fmtMoney(transfers.reduce(function(s,t2){return s+t2.amt;},0))+'</div>';
  }""",
"""    settleHtml+='<div style="font-size:0.72rem;color:var(--text-light);margin-top:8px">💡 共 '+transfers.length+' 笔结算，总流转金额 '+fmtMoney(transfers.reduce(function(s,t2){return s+t2.amt;},0))+'</div>';
    /* 付完了点一下，之后不再重复计算这部分 */
    if(state.spaceMode==='team'){
      settleHtml+='<div style="margin-top:10px"><button class="btn btn-primary btn-sm" id="settleBtn" style="width:100%">'+
        svgIcon('check')+'这些都付完了，标记结清</button></div>';
    }
  }""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
