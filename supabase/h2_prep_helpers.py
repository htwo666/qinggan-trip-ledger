#!/usr/bin/env python3
# h2_prep_helpers.py — 加必买清单分类板块的辅助函数
import re, sys
src = open('index.html', encoding='utf-8').read()

HELPERS = r"""/* ---------- 必买清单分类板块 ---------- */
var DEFAULT_PREP_CATS=['服饰装备','个护美妆','药品保健','证件','食品','其他'];
/* 取存活的分类列表；全新空间自动注入默认分类，保证页面打开就有板块可看 */
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
}
/* 按分类 id 查名字 */
function prepCatName(catId){
  var list=aliveList(state.data&&state.data.prepCategories);
  for(var i=0;i<list.length;i++){
    if(list[i].id===catId){return list[i].name;}
  }
  return '其他';
}
/* 按名字找分类 id，找不到就新建一个并返回 */
function prepCatId(name){
  var list=prepCats();
  for(var i=0;i<list.length;i++){
    if(list[i].name===name){return list[i].id;}
  }
  var nc={id:genId(),name:name,_ts:Date.now()};
  state.data.prepCategories.push(nc);
  return nc.id;
}
/* 一件物品有几个人已确认备齐 */
function prepReadyCount(item){
  if(!item||!item.readyBy){return 0;}
  var n=0,k;
  for(k in item.readyBy){if(item.readyBy.hasOwnProperty(k)&&item.readyBy[k]){n++;}}
  return n;
}
/* 物品是否全员备齐 */
function prepAllReady(item){
  var members=aliveMembers();
  if(!members.length){return false;}
  if(!item.readyBy){return false;}
  for(var i=0;i<members.length;i++){
    if(!item.readyBy[members[i].id]){return false;}
  }
  return true;
}
"""

# 在 ownerCheckboxes 函数定义前插入
ANCHOR = "function ownerCheckboxes(selIds){"
if src.count(ANCHOR) != 1:
    print(f'!! 找锚点失败: ownerCheckboxes ({src.count(ANCHOR)})')
    sys.exit(1)
src = src.replace(ANCHOR, HELPERS + ANCHOR)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
