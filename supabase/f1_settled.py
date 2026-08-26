#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能 1：结算标记「已付清」
思路：点"标记已结清"时，把当前每人的净额存成一个 settlement 快照（存在 _meta.settled）。
之后结算只算"快照之后新增的账"，已结清的部分不再重复出现。
可以撤销（删掉快照）。快照随云端同步，四个人看到的都一样。
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

# ---------- 结算快照读写 ----------
sub('settle snapshot helpers',
"""/* 渲染专用视图：剔除所有 _deleted 墓碑条目。""",
"""/* ---------- 结算快照（已付清）----------
   存在 _meta.settled = {ts:结算时间, by:操作人昵称, paid:{成员id:当时实付}, owed:{成员id:当时应承担}}
   结算时只统计 _ts > settled.ts 的账目，已结清的不再重复算。
   快照随云端同步，所有人看到的结算状态一致。 */
function getSettled(){
  var m=(state.data&&state.data._meta)||{};
  return m.settled||null;
}
function setSettled(snap){
  if(!state.data._meta){state.data._meta={};}
  if(snap){state.data._meta.settled=snap;}
  else{delete state.data._meta.settled;}
  state.data._metaTs=Date.now();
  saveData();
}
/* 标记已结清：把当前算出来的净额存快照 */
function markSettled(){
  var r=computeSettlement(viewData());
  if(!r||!r.transfers.length){showToast('当前没有待结算的金额');return;}
  var when=new Date();
  showConfirm('标记已结清',
    '确认这 '+r.transfers.length+' 笔转账都已经付完了吗？\\n\\n'+
    '标记后这些账不再出现在结算清单里，之后新记的账会重新开始算。\\n'+
    '（随时可以撤销）',
    function(){
      setSettled({
        ts:Date.now(),
        by:displayName()||'某人',
        at:fmtDate(todayStr()),
        paid:r.paid,
        owed:r.owed,
        count:r.transfers.length,
        total:r.transfers.reduce(function(s,t){return s+t.amt;},0)
      });
      showToast('已标记结清');
      renderAll();
    });
}
/* 撤销结清 */
function unmarkSettled(){
  var s=getSettled();
  if(!s){return;}
  showConfirm('撤销结清','撤销后之前那笔结算会重新回到清单里，确定吗？',function(){
    setSettled(null);
    showToast('已撤销');
    renderAll();
  });
}
/* 渲染专用视图：剔除所有 _deleted 墓碑条目。""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
