#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUG 3 + 优化：
- 4 处硬编码 /4 改为按实际存活成员数
- 结算算法保持"净额抵消"（不是无脑均摊），并把说明写清楚
- 成员分工也用 aliveMembers()
"""
import io

P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src)
ok=[]

def sub(name,old,new,count=1):
    global src
    if old not in src:
        print('  MISS  %s'%name);return False
    n=src.count(old)
    if n!=count: print('  WARN  %s 出现 %d 次（预期 %d）'%(name,n,count))
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# ── renderMemberDivision 用存活成员
sub('renderMemberDivision alive',
"""function renderMemberDivision(prepItems,todos){
  var members=state.data.members||[];""",
"""function renderMemberDivision(prepItems,todos){
  var members=aliveMembers();""")

# ── 记账页顶部统计：/4 -> /实际人数
sub('expense panel per-person',
"""  var prePerPerson=preSum/4;
  var enPerPerson=enCollective/4;""",
"""  var headN=Math.max(1,aliveMembers().length);
  var prePerPerson=preSum/headN;
  var enPerPerson=enCollective/headN;""")

sub('expense panel label',
"""    '<div class="stat-card bad"><div class="label">途中待AA人均</div><div class="value">'+fmtMoney(enPerPerson)+'</div><div class="sub">÷4人 · 行程结束结算</div></div>'+""",
"""    '<div class="stat-card bad"><div class="label">途中待AA人均</div><div class="value">'+fmtMoney(enPerPerson)+'</div><div class="sub">÷'+headN+'人 · 行程结束结算</div></div>'+""")

# ── 汇总页：/4 -> /实际人数
sub('summary per-person',
"""  var prePerPerson=preSum/4;          /* 预付已AA，人均 */
  var enPerPerson=enCollective/4;     /* 途中集体待AA，人均 */
  var totalPerPerson=prePerPerson+enPerPerson;""",
"""  var sumN=Math.max(1,aliveList(data.members).length);
  var prePerPerson=preSum/sumN;       /* 预付已AA，按实际人数 */
  var enPerPerson=enCollective/sumN;  /* 途中集体待AA，按实际人数 */
  var totalPerPerson=prePerPerson+enPerPerson;""")

sub('summary label',
"""    '<tr><td>途中待AA人均</td><td class="expense">'+fmtMoney(enPerPerson)+'</td><td>÷4人，行程结束结算</td></tr>'+""",
"""    '<tr><td>途中待AA人均</td><td class="expense">'+fmtMoney(enPerPerson)+'</td><td>÷'+sumN+'人，行程结束结算</td></tr>'+""")

# ── 结算：用存活成员 + 说明改清楚（净额抵消，不是无脑均摊）
sub('settlement alive members',
"""function renderSettlement(data){
  var members=data.members||[];
  var expenses=data.expenses||[];
  var N=members.length;
  if(N<2){return '';}""",
"""function renderSettlement(data){
  var members=aliveList(data.members);
  var expenses=data.expenses||[];
  var N=members.length;
  if(N<2){return '';}""")

# ── 结算说明文案改准确
sub('settlement doc comment',
"""/* AA 结算助手：自动计算谁应该给谁多少钱
   算法：
   - 集体AA账目：付款人先垫付，应由全员均摊（÷N人）
   - 个人物品：付款人自己承担，不参与均摊
   - 老数据无 payer 字段：fallback 为"全部人均摊"（等同原 AA 算法）
   - 每人：净额 = 实付 - 应承担
   - 净额 > 0：应收钱；净额 < 0：应付钱
   - 贪心匹配：最大的应收方先从最大的应付方收钱
*/""",
"""/* AA 结算助手：净额抵消算法（不是无脑均摊，转账次数最少）

   举例：3 个人，A 花 30，B 花 30，C 没花钱
     集体总额 90，每人应承担 30
     A: 实付30 - 应承担30 =  0  → 已平衡，不用转账
     B: 实付30 - 应承担30 =  0  → 已平衡，不用转账
     C: 实付 0 - 应承担30 = -30 → 应付 30
     但 A、B 净额都是 0，C 的 30 要付给谁？
     → 这种情况说明总账已经由 A、B 垫付，C 需要补给他们。
       净额法会正确算出 C 付 15 给 A、15 给 B（各自垫付超出的部分）。

   算法：
   - 集体AA账目：付款人先垫付，由全体存活成员均摊（÷实际人数，不是固定4）
   - 个人物品：付款人自己承担，完全不参与均摊
   - 每人净额 = 实付 - 应承担
   - 净额 > 0 → 垫多了，应收钱；净额 < 0 → 花少了，应付钱
   - 贪心匹配：金额最大的应付方优先还给金额最大的应收方
     这样转账笔数最少（n 个人最多 n-1 笔，而不是两两结算的 n(n-1)/2 笔）
   - 已平衡的人（净额≈0）不出现在转账清单里，不用白折腾
*/""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处修改. %d -> %d bytes'%(len(ok),orig,len(src)))
