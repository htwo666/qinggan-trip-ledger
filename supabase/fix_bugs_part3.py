#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收尾：修正注释示例 + initWorkspace 的 normalizeData 要传 isExisting"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# 修正注释里算错的例子（用用户原话的场景）
sub('fix comment example',
"""   举例：3 个人，A 花 30，B 花 30，C 没花钱
     集体总额 90，每人应承担 30
     A: 实付30 - 应承担30 =  0  → 已平衡，不用转账
     B: 实付30 - 应承担30 =  0  → 已平衡，不用转账
     C: 实付 0 - 应承担30 = -30 → 应付 30
     但 A、B 净额都是 0，C 的 30 要付给谁？
     → 这种情况说明总账已经由 A、B 垫付，C 需要补给他们。
       净额法会正确算出 C 付 15 给 A、15 给 B（各自垫付超出的部分）。
""",
"""   举例：3 个人，A 花 30，B 花 30，C 没花钱
     集体总额 = 30+30+0 = 60，每人应承担 60/3 = 20
     A: 实付30 - 应承担20 = +10 → 应收 10
     B: 实付30 - 应承担20 = +10 → 应收 10
     C: 实付 0 - 应承担20 = -20 → 应付 20
     结算清单：C 付给 A 10 元，C 付给 B 10 元
     A 和 B 之间不用转账（净额法自动抵消，不会让所有人两两互转）
""")

# initWorkspace：有缓存就是已存在数据，不能回填预设
sub('initWorkspace normalizeData isExisting',
"""  state.teamData=normalizeData(state.teamData,false);
  state.personalData=normalizeData(state.personalData,true);""",
"""  state.teamData=normalizeData(state.teamData,false,!!teamCached);
  state.personalData=normalizeData(state.personalData,true,!!personalCached);""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处修改. %d -> %d bytes'%(len(ok),orig,len(src)))
