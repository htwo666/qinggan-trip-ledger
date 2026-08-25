#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理旧同步码相关的死代码与失效 DOM 绑定"""
import io

P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src)
ok=[]

def sub(name,old,new,count=1):
    global src
    if old not in src:
        print('  MISS  %s'%name); return False
    src=src.replace(old,new,count); ok.append(name); print('  OK    %s'%name); return True

# 1. 删掉指向已删除元素的事件绑定
sub('dead bindings',
"""document.getElementById('bindSyncBtn').onclick=function(){
  var code=document.getElementById('syncCodeInput').value.trim();
  bindSyncCode(code);
  document.getElementById('syncCodeInput').value='';
};
/* 同步弹窗 tab 切换 */
var syncTabs=document.querySelectorAll('.sync-tab');
for(var sti=0;sti<syncTabs.length;sti++){
  syncTabs[sti].onclick=function(){switchSyncTab(this.getAttribute('data-synctab'));};
}
/* 复制分享链接 */
document.getElementById('copyLinkBtn').onclick=function(){
  var input=document.getElementById('syncShareLink');
  input.select();input.setSelectionRange(0,99999);
  try{
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(input.value).then(function(){showToast('链接已复制');});
    }else{
      document.execCommand('copy');
      showToast('链接已复制');
    }
  }catch(e){showToast('复制失败，请手动选择');}
};""",
"""/* 旧的同步码绑定 / tab 切换 / 复制链接已由 initAuthModule() 内的空间管理弹窗接管 */""")

# 2. 把旧 showSyncModal 的死壳彻底删掉，换成干净的转发
i=src.find("function showSyncModal(){")
if i<0:
    print('  MISS  showSyncModal locate')
else:
    j=src.find("/* 切换同步弹窗的 tab */",i)
    if j<0:
        print('  MISS  showSyncModal end')
    else:
        src=src[:i]+"""function showSyncModal(){showWorkspaceModal();}
"""+src[j:]
        ok.append('showSyncModal cleaned'); print('  OK    showSyncModal cleaned')

# 3. 删掉 switchSyncTab / bindSyncCode / handleSyncUrlParam 三个死函数
i=src.find("/* 切换同步弹窗的 tab */")
if i<0:
    print('  MISS  dead funcs start')
else:
    j=src.find("/* 构建分享链接 */",i)
    if j<0:
        print('  MISS  dead funcs end')
    else:
        src=src[:i]+src[j:]
        ok.append('dead funcs removed'); print('  OK    dead funcs removed (switchSyncTab/bindSyncCode/handleSyncUrlParam)')

# 4. syncCodeBtn 文案：applySpaceModeUI 里若还写"同步码"，改成"团队"
src=src.replace("syncCodeBtn.textContent='同步码'","syncCodeBtn.textContent='空间'")
src=src.replace(">同步码<",">空间<")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d cleanups. %d -> %d bytes'%(len(ok),orig,len(src)))
