#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纵深防御：即使缓存 key 逻辑再出 bug，也不能把 A 团队的数据写进 B 团队。
做法：缓存数据里盖上 _wsId 印章，读取时空间 ID 不匹配就直接丢弃。
"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

sub('cache ws stamp',
"""function getLSCache(mode){
  try{return JSON.parse(localStorage.getItem(cacheKey(mode))||'null');}catch(e){return null;}
}
function setLSCache(d,mode){
  try{localStorage.setItem(cacheKey(mode),JSON.stringify(d));}catch(e){}
}""",
"""function getLSCache(mode){
  try{
    var d=JSON.parse(localStorage.getItem(cacheKey(mode))||'null');
    if(!d){return null;}
    /* 纵深防御：缓存里盖了空间印章，对不上就丢弃。
       宁可白屏一下从云端重拉，也不能把别的团队的数据渲染出来。 */
    var cur=(auth&&auth.currentWs&&auth.currentWs.id)?auth.currentWs.id:null;
    if(cur&&d._wsId&&d._wsId!==cur){return null;}
    return d;
  }catch(e){return null;}
}
function setLSCache(d,mode){
  try{
    var cur=(auth&&auth.currentWs&&auth.currentWs.id)?auth.currentWs.id:null;
    if(cur&&d){d._wsId=cur;}
    localStorage.setItem(cacheKey(mode),JSON.stringify(d));
  }catch(e){}
}""")

# 推送前再校验一次：要推的数据必须属于当前空间
sub('push guard',
"""function dataToRecords(data){
  var out=[];""",
"""function dataToRecords(data){
  var out=[];
  /* 纵深防御：数据印章和当前空间不符时拒绝推送，避免污染云端 */
  var curWs=(auth&&auth.currentWs&&auth.currentWs.id)?auth.currentWs.id:null;
  if(curWs&&data&&data._wsId&&data._wsId!==curWs){
    try{console.warn('[同步] 数据归属'+data._wsId+'，当前空间'+curWs+'，已拒绝推送');}catch(e){}
    return out;
  }""")

# _wsId 不要作为业务字段被推到云端
sub('exclude _wsId from merge types passthrough',
"""  var merged={};
  for(var t in local){if(local.hasOwnProperty(t)&&types.indexOf(t)===-1){merged[t]=local[t];}}""",
"""  var merged={};
  for(var t in local){
    if(local.hasOwnProperty(t)&&types.indexOf(t)===-1&&t!=='_wsId'){merged[t]=local[t];}
  }
  /* _wsId 始终跟随当前空间，不参与合并 */
  if(auth&&auth.currentWs&&auth.currentWs.id){merged._wsId=auth.currentWs.id;}""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处修改. %d -> %d bytes'%(len(ok),orig,len(src)))
