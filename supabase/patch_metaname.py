#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复：records._meta 里过期的 teamName 覆盖了 workspaces 表的真实名字。
   空间名的唯一权威来源必须是 workspaces 表。"""
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

# 1. 删掉 pullRemote 里"用 meta 覆盖空间名"的错误逻辑
sub('remove meta name override',
"""      /* 云端的空间名以 workspaces 表为准（团队名多设备同步） */
      if(data._meta&&data._meta.teamName&&data._meta.teamName!==ws.name){
        /* 云端 meta 比本地新，说明别人改了名，采用云端的 */
        ws.name=data._meta.teamName;
        for(var i=0;i<auth.workspaces.length;i++){
          if(auth.workspaces[i].id===ws.id){auth.workspaces[i].name=ws.name;}
        }
        applySpaceModeUI();
      }
""",
"""      /* 注意：空间名的唯一权威来源是 workspaces 表，不是 records 的 meta。
         meta 里的 teamName 只作为历史兼容字段，绝不用它覆盖 ws.name，
         否则过期的 meta 会把别人的改名顶掉（这正是"假同步"的另一种表现）。 */
      if(data._meta){delete data._meta.teamName;}
""")

# 2. remoteWrite 不再往 meta 里写 teamName（避免再产生过期数据）
sub('stop writing teamName to meta',
"""  var ws=auth.currentWs;
  /* 同时把空间名带上，实现团队名多设备同步 */
  data._meta=data._meta||{};
  data._meta.teamName=ws.name;
  data._metaTs=Date.now();
  sbPush(ws.id,data,function(err){""",
"""  var ws=auth.currentWs;
  /* 空间名走 workspaces 表（renameWorkspace），不写进 records.meta，
     避免过期副本覆盖真实名字 */
  if(data._meta&&data._meta.teamName){delete data._meta.teamName;}
  sbPush(ws.id,data,function(err){""")

# 3. 改名时也不再写 meta 双通道（workspaces 表 + Realtime 已经够了）
sub('rename single channel',
"""      applySpaceModeUI();
      /* 同时写进 records 的 meta，双通道保证同步 */
      sbPushMeta(auth.currentWs.id,{teamName:name},function(){
        setSyncStatus('synced');
        showToast('已改名为「'+name+'」，队友会自动看到');
      });""",
"""      applySpaceModeUI();
      setSyncStatus('synced');
      showToast('已改名为「'+name+'」，队友会自动看到');""")

# 4. bootAfterLogin / activateWorkspace 之后一定用 workspaces 表的名字刷新横幅
sub('activate uses authoritative name',
"""  setSyncStatus('connecting');
  loadWsMembers(ws.id,function(){renderAll();});""",
"""  setSyncStatus('connecting');
  loadWsMembers(ws.id,function(){applySpaceModeUI();renderAll();});""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d patches. %d -> %d bytes'%(len(ok),orig,len(src)))
