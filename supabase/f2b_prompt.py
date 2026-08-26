#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""showPrompt 输入弹窗 + 预算提示条挂载 + 改预算链接绑定"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# 1. showPrompt：复用 confirm 弹窗，塞一个输入框进去
sub('showPrompt',
"""function showConfirm(title,body,cb){""",
"""/* 输入型弹窗：复用 confirm 弹窗的结构，往 body 里塞个 input */
function showPrompt(title,label,defVal,cb){
  var body=document.getElementById('confirmBody');
  document.getElementById('confirmTitle').textContent=title;
  body.innerHTML='<div style="font-size:0.8rem;color:var(--text-light);margin-bottom:8px">'+
    escapeHtml(label)+'</div>'+
    '<input type="number" id="promptInput" value="'+escapeHtml(String(defVal||''))+'" '+
    'style="width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;font-size:1rem;box-sizing:border-box">';
  confirmCallback=function(){
    var el=document.getElementById('promptInput');
    var v=el?el.value:'';
    /* 用完把 body 还原成纯文本容器，不然下次 showConfirm 会残留输入框 */
    body.innerHTML='';
    cb&&cb(v);
  };
  document.getElementById('confirmModal').classList.add('show');
  setTimeout(function(){
    var el=document.getElementById('promptInput');
    if(el){el.focus();el.select();}
  },100);
}
function showConfirm(title,body,cb){
  document.getElementById('confirmBody').innerHTML='';""")

# 2. 预算提示条挂到记账页最上面
sub('mount budget alert',
"""  p.innerHTML=todayHtml+stats+toolbar+preHtml+enHtml;""",
"""  p.innerHTML=alertHtml+todayHtml+stats+toolbar+preHtml+enHtml;
  var ebl=document.getElementById('editBudgetLink');
  if(ebl){ebl.onclick=editBudget;}""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
