#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫尾：清掉最后两处"4人"硬编码文案 + 成员分工标题显示实际人数"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

sub('banner not-logged text',
"""      sub.textContent=isPersonal?'私人记账 · 本地模式':'4人 11天自驾 · 2026-09-25 至 10-05';""",
"""      var bn=Math.max(1,aliveMembers().length);
      sub.textContent=isPersonal?'私人记账 · 本地模式':(bn+'人 11天自驾 · 2026-09-25 至 10-05');""")

sub('AI prompt member count',
"""    prompt+='\\n【空间模式】用户当前在"团队空间"（4 人共享记账），多人协作同步。可适当提醒AA结算、分工等团队场景。\\n';""",
"""    prompt+='\\n【空间模式】用户当前在"团队空间"（'+Math.max(1,aliveMembers().length)+' 人共享记账），多人协作同步。可适当提醒AA结算、分工等团队场景。\\n';""")

sub('member division title count',
"""  var html='<div class="member-card"><div class="card-title">'+svgIcon('users')+'成员分工 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（点击名字可直接改名，添加物品/待办时可指定负责人）</span></div>';""",
"""  var html='<div class="member-card"><div class="card-title">'+svgIcon('users')+'成员分工 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（当前 '+members.length+' 人 · 点击名字可改名 · 可增删成员，AA 自动按实际人数算）</span></div>';""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处修改. %d -> %d bytes'%(len(ok),orig,len(src)))
