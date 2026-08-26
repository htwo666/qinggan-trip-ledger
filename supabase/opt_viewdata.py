#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渲染层统一过滤墓碑：各 render 函数入口的 var data=state.data
改成 var data=viewData()，返回一份已剔除 _deleted 的浅视图。
写操作仍然直接改 state.data（按 id 查找，不受影响）。
"""
import io,re
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    n=src.count(old)
    if n!=count: print('  WARN  %s 出现 %d 次（预期 %d）'%(name,n,count))
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# viewData：只给渲染用的、剔除墓碑的视图
sub('viewData helper',
"""/* 取当前存活的成员列表 —— 全站统一用这个，不要直接用 state.data.members */""",
"""/* 渲染专用视图：剔除所有 _deleted 墓碑条目。
   写操作请继续用 state.data（按 id 查找修改），只有"读来渲染"才用这个。 */
function viewData(){
  var s=state.data||{};
  var v={},types=['prepItems','prepaid','expenses','outfits','todos','members','prepTodos'],i;
  for(var k in s){if(s.hasOwnProperty(k)&&types.indexOf(k)===-1){v[k]=s[k];}}
  for(i=0;i<types.length;i++){v[types[i]]=aliveList(s[types[i]]);}
  return v;
}
/* 取当前存活的成员列表 —— 全站统一用这个，不要直接用 state.data.members */""")

# 6 处 var data=state.data 全换（第 3112 行那个 outfits 兜底要特殊处理）
n=src.count('  var data=state.data;')
src=src.replace('  var data=state.data;','  var data=viewData();')
print('  OK    %d 处 var data=state.data -> viewData()'%n);ok.append('viewData swap')

# outfits 兜底那行原来是 data=state.data，改成重新取视图
sub('outfits fallback',
"""  if(!data.outfits){state.data.outfits=[];data=state.data;}""",
"""  if(!data.outfits){state.data.outfits=[];data=viewData();}""")

# showMemberDetail 里遍历 prepItems/todos 也要过滤墓碑
sub('memberDetail filter',
"""  for(var i=0;i<state.data.prepItems.length;i++){
    if(state.data.prepItems[i].owner===memberId){myItems.push(state.data.prepItems[i]);}""",
"""  var _pi=aliveList(state.data.prepItems);
  for(var i=0;i<_pi.length;i++){
    if(_pi[i].owner===memberId){myItems.push(_pi[i]);}""")

sub('memberDetail todos filter',
"""  for(var t=0;t<state.data.todos.length;t++){
    if(state.data.todos[t].owner===memberId){myTodos.push(state.data.todos[t]);}""",
"""  var _td=aliveList(state.data.todos);
  for(var t=0;t<_td.length;t++){
    if(_td[t].owner===memberId){myTodos.push(_td[t]);}""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 组修改. %d -> %d bytes'%(len(ok),orig,len(src)))
