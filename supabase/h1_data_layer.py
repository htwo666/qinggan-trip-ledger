#!/usr/bin/env python3
# h1_data_layer.py — 数据层：加 prepCategories 数据类型 + 迁移 + 结算快照 coveredIds
import re, sys, io
src = open('index.html', encoding='utf-8').read()

def rep(s, old, new, label):
    n = s.count(old)
    if n == 0:
        print(f'!! 未找到: {label}')
        sys.exit(1)
    if n > 1:
        print(f'!! 多处匹配 ({n}): {label}')
        sys.exit(1)
    return s.replace(old, new)

# 1) state.data 初始 shape 加 prepCategories
src = rep(src,
    "data:{prepItems:[],prepaid:[],expenses:[],outfits:[],todos:[],members:[],prepTodos:[]},",
    "data:{prepItems:[],prepCategories:[],prepaid:[],expenses:[],outfits:[],todos:[],members:[],prepTodos:[]},",
    'state.data shape')

# 2) KIND_MAP 加 prepCategories
src = rep(src,
    "var KIND_MAP={prepItems:'prepItem',prepaid:'prepaid',expenses:'expense',\n              outfits:'outfit',todos:'todo',prepTodos:'prepTodo',members:'member'};",
    "var KIND_MAP={prepItems:'prepItem',prepCategories:'prepCategory',prepaid:'prepaid',expenses:'expense',\n              outfits:'outfit',todos:'todo',prepTodos:'prepTodo',members:'member'};",
    'KIND_MAP')

# 3) DATA_TYPES 加 prepCategories
src = rep(src,
    "var DATA_TYPES=['prepItems','prepaid','expenses','outfits','todos','members','prepTodos'];",
    "var DATA_TYPES=['prepItems','prepCategories','prepaid','expenses','outfits','todos','members','prepTodos'];",
    'DATA_TYPES')

# 4) recordsToData 初始 d 加 prepCategories
src = rep(src,
    "var d={prepItems:[],prepaid:[],expenses:[],outfits:[],todos:[],members:[],prepTodos:[]};\n  var hasAny=false;",
    "var d={prepItems:[],prepCategories:[],prepaid:[],expenses:[],outfits:[],todos:[],members:[],prepTodos:[]};\n  var hasAny=false;",
    'recordsToData d')

# 5) buildDefaultData 初始 d 加 prepCategories
src = rep(src,
    "var d={prepItems:[],prepaid:[],expenses:[],outfits:[],todos:[],members:[],prepTodos:[]};\n  /* 个人空间",
    "var d={prepItems:[],prepCategories:[],prepaid:[],expenses:[],outfits:[],todos:[],members:[],prepTodos:[]};\n  /* 个人空间",
    'buildDefaultData d')

# 6) normalizeData 加 prepCategories 初始化 + 迁移
# 在 `if(!d.prepItems){d.prepItems=[];}` 后加迁移
src = rep(src,
    "  if(!d.prepItems){d.prepItems=[];}\n",
    "  if(!d.prepItems){d.prepItems=[];}\n"
    "  if(!d.prepCategories){d.prepCategories=[];}\n"
    "  /* 老必买清单只有 category 字符串字段，这里升级成分类板块：\n"
    "     每个旧 category 找出（或新建）一个 prepCategories 条目，\n"
    "     把物品的 cat 指向分类 id。price/channel/owner/bought/overdue 在新模型里\n"
    "     不再使用，但旧字段原样留着，老设备读旧数据不会崩。readyBy 用空对象初始化。 */\n"
    "  if(d.prepItems&&d.prepItems.length){\n"
    "    var _pc=d.prepCategories,_pcByName={},_pci;\n"
    "    for(_pci=0;_pci<_pc.length;_pci++){\n"
    "      if(_pc[_pci]&&!_pc[_pci]._deleted&&_pc[_pci].name){_pcByName[_pc[_pci].name]=_pc[_pci].id;}\n"
    "    }\n"
    "    for(var _pii=0;_pii<d.prepItems.length;_pii++){\n"
    "      var _pi=d.prepItems[_pii];\n"
    "      if(!_pi||_pi.cat){continue;}\n"
    "      var _cname=_pi.category||'其他';\n"
    "      if(!_pcByName[_cname]){\n"
    "        var _ncid=genId();\n"
    "        _pc.push({id:_ncid,name:_cname,_ts:Date.now()});\n"
    "        _pcByName[_cname]=_ncid;\n"
    "      }\n"
    "      _pi.cat=_pcByName[_cname];\n"
    "      if(!_pi.readyBy){_pi.readyBy={};}\n"
    "    }\n"
    "  }\n",
    'normalizeData prep migration')

# 7) viewData types 加 prepCategories
src = rep(src,
    "var v={},types=['prepItems','prepaid','expenses','outfits','todos','members','prepTodos'],i;",
    "var v={},types=['prepItems','prepCategories','prepaid','expenses','outfits','todos','members','prepTodos'],i;",
    'viewData types')

# 8) mergeData types 加 prepCategories
src = rep(src,
    "var types=['prepItems','prepaid','expenses','outfits','todos','members','prepTodos'];",
    "var types=['prepItems','prepCategories','prepaid','expenses','outfits','todos','members','prepTodos'];",
    'mergeData types')

# 9) 结算快照：markSettled 存 coveredIds
src = rep(src,
    "      setSettled({\n"
    "        ts:Date.now(),\n"
    "        by:currentNickname()||'某人',\n"
    "        at:fmtDate(todayStr()),\n"
    "        paid:r.paid,\n"
    "        owed:r.owed,\n"
    "        count:r.transfers.length,\n"
    "        total:r.transfers.reduce(function(s,t){return s+t.amt;},0)\n"
    "      });",
    "      /* 把当时所有存活的账 id 都记下来，以后改旧账也不会污染基线 */\n"
    "      var _cov={},_ci;\n"
    "      for(_ci=0;_ci<aliveList(state.data.expenses).length;_ci++){\n"
    "        _cov[aliveList(state.data.expenses)[_ci].id]=true;\n"
    "      }\n"
    "      setSettled({\n"
    "        ts:Date.now(),\n"
    "        by:currentNickname()||'某人',\n"
    "        at:fmtDate(todayStr()),\n"
    "        paid:r.paid,\n"
    "        owed:r.owed,\n"
    "        coveredIds:_cov,\n"
    "        count:r.transfers.length,\n"
    "        total:r.transfers.reduce(function(s,t){return s+t.amt;},0)\n"
    "      });",
    'markSettled coveredIds')

# 10) 结算快照注释更新
src = rep(src,
    "/* ---------- 结算快照（已付清）----------\n"
    "   存在 _meta.settled = {ts:结算时间, by:操作人昵称, paid:{成员id:当时实付}, owed:{成员id:当时应承担}}\n"
    "   结算时只统计 _ts > settled.ts 的账目，已结清的不再重复算。\n"
    "   快照随云端同步，所有人看到的结算状态一致。 */",
    "/* ---------- 结算快照（已付清）----------\n"
    "   _meta.settled = {ts, by, at, paid, owed, coveredIds, count, total}\n"
    "   coveredIds 记下结算时哪些账被算过，之后改/删这些旧账都不会污染基线。\n"
    "   老快照没有 coveredIds，回退到原来的 paid/owed 总额减法（兼容老数据）。 */",
    'settled comment')

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
