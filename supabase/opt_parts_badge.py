#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""花费列表显示"仅N人"标记 + 参与人chip的X5兼容class"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# 花费列表：不是全员参与的账目打标记
sub('expense list parts badge',
"""        var payerBadge=ex.payer?'<span class="payer-tag">付:'+escapeHtml(payerName)+'</span>':'';""",
"""        var payerBadge=ex.payer?'<span class="payer-tag">付:'+escapeHtml(payerName)+'</span>':'';
        /* 不是全员参与的账目，标出参与人数（点击可看是谁） */
        var partBadge='';
        if(isC&&ex.parts&&ex.parts.length){
          var pnames=[];
          for(var pn=0;pn<ex.parts.length;pn++){pnames.push(memberNameById(ex.parts[pn]));}
          partBadge='<span class="payer-tag" style="background:#eef6ff;color:#2b6cb0" title="'+
            escapeHtml(pnames.join('、'))+'">仅'+ex.parts.length+'人分</span>';
        }""")

sub('expense list render parts badge',
"""'</span>'+payerBadge+'</div><div style="font-size:0.72rem;color:var(--text-light);margin-top:2px">'+(ex.note?escapeHtml(ex.note):'无备注')+'</div></div>""",
"""'</span>'+payerBadge+partBadge+'</div><div style="font-size:0.72rem;color:var(--text-light);margin-top:2px">'+(ex.note?escapeHtml(ex.note):'无备注')+'</div></div>""")

# 参与人 chip：给 label 加/去 .on class（微信 X5 不支持 :has）
sub('part chip class toggle',
"""  var partCbs=document.querySelectorAll('.fPart');
  for(var pc=0;pc<partCbs.length;pc++){partCbs[pc].onchange=refreshPartHint;}""",
"""  /* 同步 chip 的选中样式（微信 X5 内核不支持 :has，靠 class 兜底） */
  function syncChips(){
    var cbs=document.querySelectorAll('.fPart');
    for(var i=0;i<cbs.length;i++){
      var lab=cbs[i].parentNode;
      if(!lab){continue;}
      if(cbs[i].checked){
        if(lab.className.indexOf('on')<0){lab.className+=' on';}
      }else{
        lab.className=lab.className.replace(/\\s*\\bon\\b/g,'');
      }
    }
  }
  var partCbs=document.querySelectorAll('.fPart');
  for(var pc=0;pc<partCbs.length;pc++){
    partCbs[pc].onchange=function(){syncChips();refreshPartHint();};
  }
  syncChips();""")

sub('part all sync','''    var cbs=document.querySelectorAll('.fPart');
    for(var i=0;i<cbs.length;i++){cbs[i].checked=true;}
    refreshPartHint();''',
'''    var cbs=document.querySelectorAll('.fPart');
    for(var i=0;i<cbs.length;i++){cbs[i].checked=true;}
    syncChips();refreshPartHint();''')

sub('part none sync','''    var cbs=document.querySelectorAll('.fPart');
    for(var i=0;i<cbs.length;i++){cbs[i].checked=false;}
    refreshPartHint();''',
'''    var cbs=document.querySelectorAll('.fPart');
    for(var i=0;i<cbs.length;i++){cbs[i].checked=false;}
    syncChips();refreshPartHint();''')

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
