#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""花费列表加编辑按钮 + 绑定"""
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

# 列表项加「改」按钮（放在删除左边）
sub('add edit button to expense item',
"""'</div><div class="amount">'+fmtMoney(ex.amount)+'</div><div class="del"><button data-action="delExp" data-id="'+ex.id+'">'+svgIcon('trash')+'</button></div></div>';""",
"""'</div><div class="amount">'+fmtMoney(ex.amount)+'</div><div class="del">'+
          '<button data-action="editExp" data-id="'+ex.id+'" title="修改这笔" style="color:var(--primary)">'+svgIcon('edit')+'</button>'+
          '<button data-action="delExp" data-id="'+ex.id+'">'+svgIcon('trash')+'</button></div></div>';""")

# 绑定编辑
sub('bind edit button',
"""  var csvBtn=document.getElementById('exportCsvBtn');""",
"""  var edBtns=p.querySelectorAll('[data-action="editExp"]');
  for(var eb=0;eb<edBtns.length;eb++){
    edBtns[eb].onclick=function(){
      var id=this.getAttribute('data-id');
      var arr=state.data.expenses||[];
      for(var q=0;q<arr.length;q++){
        if(arr[q].id===id&&!arr[q]._deleted){showExpenseForm(arr[q]);return;}
      }
      showToast('这笔账找不到了');
    };
  }
  var csvBtn=document.getElementById('exportCsvBtn');""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
