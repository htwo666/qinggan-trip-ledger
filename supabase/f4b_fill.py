#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回填日期/金额/备注/分摊方式 + 花费列表加编辑按钮"""
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

# 分摊方式：编辑时选中原值
sub('type selected',
"""     '<div><label>分摊方式</label><select id="fType"><option value="collective">集体AA（参与均摊）</option><option value="personal">个人物品（不均摊）</option></select></div></div>';""",
"""     '<div><label>分摊方式</label><select id="fType">'+
       '<option value="collective"'+(vType==='collective'?' selected':'')+'>集体AA（参与均摊）</option>'+
       '<option value="personal"'+(vType==='personal'?' selected':'')+'>个人物品（不均摊）</option>'+
     '</select></div></div>';""")

# 日期 + 金额（这一段是记账表单专属，带 fAmount 所以唯一）
sub('date & amount value',
"""    '<div class="form-row"><div><label>日期</label><input type="date" id="fDate" value="'+today+'"></div>'+
    '<div><label>金额 ¥</label><input type="number" id="fAmount" step="0.01" placeholder="0.00"></div></div>'+""",
"""    '<div class="form-row"><div><label>日期</label><input type="date" id="fDate" value="'+vDate+'"></div>'+
    '<div><label>金额 ¥</label><input type="number" id="fAmount" step="0.01" placeholder="0.00" value="'+vAmount+'"></div></div>'+""")

# 备注
sub('note value',
"""    '<div class="form-row"><div style="flex:1"><label>备注</label><input type="text" id="fNote" placeholder="如：3人午餐，老王没吃"></div></div>'+""",
"""    '<div class="form-row"><div style="flex:1"><label>备注</label><input type="text" id="fNote" placeholder="如：3人午餐，老王没吃" value="'+escapeHtml(vNote)+'"></div></div>'+""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
