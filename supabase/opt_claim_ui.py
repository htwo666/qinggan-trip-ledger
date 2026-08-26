#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""成员卡片加"这是我"认领按钮 + 绑定事件 + 上限同步为12"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# 成员卡片加认领按钮
sub('member cell claim btn',
"""    html+='<div class="member-cell" style="position:relative"><button class="member-del" data-action="delMember" data-id="'+m.id+'">✕</button><div class="member-avatar" style="background:'+memberColor(i)+'" data-action="viewMember" data-id="'+m.id+'">'+escapeHtml((m.name||'?').charAt(0))+'</div><input class="member-name-input" data-id="'+m.id+'" value="'+escapeHtml(m.name)+'"><div style="font-size:0.66rem;color:var(--text-light);margin-top:2px">点击头像看分工</div></div>';
  }
  if(members.length<8){""",
"""    /* 认领状态：我认领的 / 别人认领的 / 没人认领 */
    var claimCls='',claimTxt='这是我',claimDis='';
    if(m.uid&&m.uid===uid){claimCls=' mine';claimTxt='✓ 我';}
    else if(m.uid){claimCls=' taken';claimTxt='已认领';claimDis=' disabled';}
    var claimBtn=logged
      ?'<button class="claim-btn'+claimCls+'" data-action="claimMember" data-id="'+m.id+'"'+claimDis+'>'+claimTxt+'</button>'
      :'<div style="font-size:0.66rem;color:var(--text-light);margin-top:2px">点击头像看分工</div>';
    html+='<div class="member-cell" style="position:relative"><button class="member-del" data-action="delMember" data-id="'+m.id+'">✕</button><div class="member-avatar" style="background:'+memberColor(i)+'" data-action="viewMember" data-id="'+m.id+'">'+escapeHtml((m.name||'?').charAt(0))+'</div><input class="member-name-input" data-id="'+m.id+'" value="'+escapeHtml(m.name)+'">'+claimBtn+'</div>';
  }
  if(members.length<12){""")

# 认领所需的上下文变量
sub('member division claim ctx',
"""function renderMemberDivision(prepItems,todos){
  var members=aliveMembers();
  var html='<div class="member-card"><div class="card-title">'+svgIcon('users')+'成员分工 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（当前 '+members.length+' 人 · 点击名字可改名 · 可增删成员，AA 自动按实际人数算）</span></div>';""",
"""function renderMemberDivision(prepItems,todos){
  var members=aliveMembers();
  var uid=myUid();
  var logged=!!(uid&&state.spaceMode==='team');
  var hint=logged
    ?'当前 '+members.length+' 人 · 点名字改名 · 点「这是我」认领，记账就默认你付款'
    :'当前 '+members.length+' 人 · 点击名字可改名 · 可增删成员，AA 按实际人数算';
  var html='<div class="member-card"><div class="card-title">'+svgIcon('users')+'成员分工 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（'+hint+'）</span></div>';""")

# 绑定认领点击
sub('bind claim',
"""  /* 点击头像查看成员分工详情 */
  var viewBtns=p.querySelectorAll('[data-action="viewMember"]');""",
"""  /* 认领成员（这是我） */
  var claimBtns=p.querySelectorAll('[data-action="claimMember"]');
  for(var cb2=0;cb2<claimBtns.length;cb2++){
    claimBtns[cb2].onclick=function(){
      if(this.disabled){return;}
      claimMember(this.getAttribute('data-id'),function(){renderPrep();});
    };
  }
  /* 点击头像查看成员分工详情 */
  var viewBtns=p.querySelectorAll('[data-action="viewMember"]');""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
