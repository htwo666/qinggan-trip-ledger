#!/usr/bin/env python3
# h12_prep_auto_fix.py — 修复必买清单每次打开自动新增板块的 bug
#
# 根因：prepCats() 用 aliveList() 过滤掉墓碑后判断是否为空，
#   如果用户删了所有板块 → aliveList 返回 [] → 函数自动注入 6 个默认板块 + saveData()
#   → 每次打开页面都冒出新板块
#
# 修复：
#   1. prepCats(): 改成检查 raw 数组长度（包括墓碑），只有从未初始化过（raw 为空）才注入
#   2. 清空函数: 清空后留一个墓碑标记，防止 prepCats() 重新注入默认板块

src = open('index.html', encoding='utf-8').read()

# ---- 1. 修复 prepCats() ----
prep_old = """/* 取存活的分类列表；全新空间自动注入默认分类，保证页面打开就有板块可看 */
function prepCats(){
  var list=aliveList(state.data&&state.data.prepCategories);
  if(!list.length){
    for(var i=0;i<DEFAULT_PREP_CATS.length;i++){
      var c={id:genId(),name:DEFAULT_PREP_CATS[i],_ts:Date.now()};
      state.data.prepCategories.push(c);
      list.push(c);
    }
    saveData();
  }
  return list;
}"""

prep_new = """/* 取存活的分类列表；全新空间（从未初始化过）自动注入默认分类。
   关键：检查 raw 数组长度（包括已删除的墓碑），不是 aliveList。
   否则用户删掉所有板块后，每次打开页面 aliveList 都为空，会自动冒出 6 个默认板块。 */
function prepCats(){
  var raw=state.data&&state.data.prepCategories;
  if(!raw){raw=[];state.data.prepCategories=raw;}
  var list=aliveList(raw);
  /* 只有 raw 完全为空（从未初始化过）才注入默认分类。
     raw 有元素（包括墓碑）说明用户已经操作过，不再自动注入。 */
  if(!raw.length){
    for(var i=0;i<DEFAULT_PREP_CATS.length;i++){
      var c={id:genId(),name:DEFAULT_PREP_CATS[i],_ts:Date.now()};
      raw.push(c);
      list.push(c);
    }
    saveData();
  }
  return list;
}"""

c1 = src.count(prep_old)
print(f'prepCats anchor: {c1}')
if c1 != 1:
    print('!! prepCats anchor not unique'); exit(1)
src = src.replace(prep_old, prep_new)

# ---- 2. 修复清空必买清单函数：留墓碑防止重新注入 ----
clear_prep_old = "fn=function(){state.data.prepItems=[];state.data.prepCategories=[];saveData();renderAll();};"
clear_prep_new = "fn=function(){state.data.prepItems=[];state.data.prepCategories=[{id:genId(),name:'_cleared',_deleted:true,_ts:Date.now()}];saveData();renderAll();};"

c2 = src.count(clear_prep_old)
print(f'clear prep anchor: {c2}')
if c2 != 1:
    print('!! clear prep anchor not unique'); exit(1)
src = src.replace(clear_prep_old, clear_prep_new)

# ---- 3. 修复清空全部数据函数：同样留墓碑 ----
clear_all_old = """fn=function(){
          state.data.prepItems=[];state.data.prepCategories=[];
          state.data.todos=[];state.data.outfits=[];state.data.expenses=[];
          saveData();renderAll();
        };"""
clear_all_new = """fn=function(){
          state.data.prepItems=[];state.data.prepCategories=[{id:genId(),name:'_cleared',_deleted:true,_ts:Date.now()}];
          state.data.todos=[];state.data.outfits=[];state.data.expenses=[];
          saveData();renderAll();
        };"""

c3 = src.count(clear_all_old)
print(f'clear all anchor: {c3}')
if c3 != 1:
    print('!! clear all anchor not unique'); exit(1)
src = src.replace(clear_all_old, clear_all_new)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
