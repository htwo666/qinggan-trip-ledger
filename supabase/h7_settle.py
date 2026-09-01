#!/usr/bin/env python3
# h7_settle.py — computeSettlement 用 coveredIds 跳过已结清的账
import sys
src = open('index.html', encoding='utf-8').read()

# 替换 computeSettlement 里统计 paid/owed 的两个循环，加上 coveredIds 跳过逻辑
old = r"""  var hasPayerRecords=false;
  for(i=0;i<expenses.length;i++){
    var e=expenses[i];
    var amt=Number(e.amount)||0;
    if(e.payer&&paid.hasOwnProperty(e.payer)){
      paid[e.payer]+=amt;
      hasPayerRecords=true;
    }
  }"""

new = r"""  var hasPayerRecords=false;
  /* coveredIds 存在 → 只算结算后新加的账，老账按 id 跳过；
     没有 coveredIds（老快照）→ 退回原来的 paid/owed 总额减法，兼容老数据。 */
  var cov=(settled&&settled.coveredIds)||null;
  for(i=0;i<expenses.length;i++){
    var e=expenses[i];
    if(cov&&cov.hasOwnProperty(e.id)){continue;}
    var amt=Number(e.amount)||0;
    if(e.payer&&paid.hasOwnProperty(e.payer)){
      paid[e.payer]+=amt;
      hasPayerRecords=true;
    }
  }"""

if src.count(old) != 1:
    print(f'!! paid loop ({src.count(old)})')
    sys.exit(1)
src = src.replace(old, new)

# owed 循环也加 coveredIds 跳过
old2 = r"""  var collectiveTotal=0,hasUnequal=false;
  for(i=0;i<expenses.length;i++){
    var e2=expenses[i];"""
new2 = r"""  var collectiveTotal=0,hasUnequal=false;
  for(i=0;i<expenses.length;i++){
    var e2=expenses[i];
    if(cov&&cov.hasOwnProperty(e2.id)){continue;}"""

if src.count(old2) != 1:
    print(f'!! owed loop ({src.count(old2)})')
    sys.exit(1)
src = src.replace(old2, new2)

# 旧的 settled.paid/owed 减法块只在没有 coveredIds 时跑，加个 if 守卫
old3 = r"""  if(settled){
    coveredCount=settled.count||0;
    coveredTotal=settled.total||0;
    for(i=0;i<N;i++){
      var mid=members[i].id;
      if(settled.paid&&settled.paid.hasOwnProperty(mid)){paid[mid]-=(Number(settled.paid[mid])||0);}
      if(settled.owed&&settled.owed.hasOwnProperty(mid)){owed[mid]-=(Number(settled.owed[mid])||0);}
    }
  }"""
new3 = r"""  if(settled){
    coveredCount=settled.count||0;
    coveredTotal=settled.total||0;
    /* 新快照有 coveredIds：上面已经按 id 跳过了，这里不用再减总额。
       老快照没有 coveredIds：只能按当时的 paid/owed 总额减，不精确但兼容老数据。 */
    if(!settled.coveredIds){
      for(i=0;i<N;i++){
        var mid=members[i].id;
        if(settled.paid&&settled.paid.hasOwnProperty(mid)){paid[mid]-=(Number(settled.paid[mid])||0);}
        if(settled.owed&&settled.owed.hasOwnProperty(mid)){owed[mid]-=(Number(settled.owed[mid])||0);}
      }
    }
  }"""
if src.count(old3) != 1:
    print(f'!! settled block ({src.count(old3)})')
    sys.exit(1)
src = src.replace(old3, new3)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
