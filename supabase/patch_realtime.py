#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复：团队名/成员数变化没有实时同步（Realtime 只订阅了 records 表，漏了 workspaces 表）"""
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

# 1. Realtime 同时订阅 workspaces 表（团队名、成员数变化）
sub('realtime subscribe workspaces',
"""          postgres_changes:[{event:'*',schema:'public',table:'records',
                             filter:'workspace_id=eq.'+wsId}]""",
"""          postgres_changes:[
            {event:'*',schema:'public',table:'records',filter:'workspace_id=eq.'+wsId},
            {event:'*',schema:'public',table:'workspaces',filter:'id=eq.'+wsId},
            {event:'*',schema:'public',table:'workspace_members',filter:'workspace_id=eq.'+wsId}
          ]""")

# 2. Realtime 收到消息时，区分是 records 还是 workspaces/members
sub('realtime message handler',
"""      if(m.event==='postgres_changes'&&m.payload&&m.payload.data){
        /* 别人改了数据，300ms 防抖后拉取（合并多条连续变更） */
        if(state.rtPullTimer){clearTimeout(state.rtPullTimer);}
        state.rtPullTimer=setTimeout(function(){
          pullRemote(function(){renderAll();});
        },350);
      }""",
"""      if(m.event==='postgres_changes'&&m.payload&&m.payload.data){
        var tbl=m.payload.data.table||'';
        if(state.rtPullTimer){clearTimeout(state.rtPullTimer);}
        state.rtPullTimer=setTimeout(function(){
          if(tbl==='records'){
            pullRemote(function(){renderAll();});
          }else{
            /* workspaces / workspace_members 变了：刷新空间元信息（名字、成员数） */
            syncWorkspaceMeta(function(){pullRemote(function(){renderAll();});});
          }
        },350);
      }""")

# 3. 新增 syncWorkspaceMeta：重新拉 my_workspaces 并更新横幅
sub('add syncWorkspaceMeta',
"""/* ---------- 登录 UI ---------- */""",
"""/* 刷新当前空间的元信息（名字 / 成员数），用于接收别人的改名 */
function syncWorkspaceMeta(cb){
  if(!auth.session||!auth.currentWs){cb&&cb();return;}
  var curId=auth.currentWs.id;
  loadWorkspaces(function(err){
    if(err){cb&&cb(err);return;}
    var found=null;
    for(var i=0;i<auth.workspaces.length;i++){
      if(auth.workspaces[i].id===curId){found=auth.workspaces[i];break;}
    }
    if(found){
      var renamed=found.name!==auth.currentWs.name;
      auth.currentWs=found;
      if(found.kind==='personal'){auth.personalWs=found;}else{auth.teamWs=found;}
      applySpaceModeUI();
      if(renamed){showToast('空间已更名为「'+found.name+'」');}
    }else{
      /* 当前空间已被移除（比如被踢出团队） */
      showToast('你已不在该空间中');
      var fallback=auth.teamWs||auth.personalWs||auth.workspaces[0];
      if(fallback){activateWorkspace(fallback,function(){});}
    }
    loadWsMembers(curId,function(){cb&&cb();});
  });
}

/* ---------- 登录 UI ---------- */""")

# 4. 兜底：每次 pullRemote 成功后也顺带校验一次空间名（防止 Realtime 被网络掐断）
sub('pullRemote meta check',
"""  var ws=auth.currentWs,modeKey=(ws.kind==='personal')?'personal':'team';
  remoteRead(function(err,data){""",
"""  var ws=auth.currentWs,modeKey=(ws.kind==='personal')?'personal':'team';
  /* 每 5 次拉取校验一次空间名（Realtime 失效时的兜底） */
  state.pullCount_=(state.pullCount_||0)+1;
  if(state.pullCount_%5===0&&!state.metaChecking_){
    state.metaChecking_=true;
    var curName=ws.name;
    rpc('my_workspaces',{},function(e2,list){
      state.metaChecking_=false;
      if(e2||!list){return;}
      auth.workspaces=list;
      for(var i=0;i<list.length;i++){
        if(list[i].id===ws.id){
          if(list[i].name!==curName||list[i].member_count!==ws.member_count){
            auth.currentWs=list[i];
            if(list[i].kind==='personal'){auth.personalWs=list[i];}else{auth.teamWs=list[i];}
            applySpaceModeUI();
          }
          break;
        }
      }
    });
  }
  remoteRead(function(err,data){""")

# 5. 团队名可点击修改（点横幅标题即可改名，并同步到所有设备）
sub('rename by clicking banner',
"""function initAuthModule(){""",
"""/* 点击横幅标题改空间名（同步到所有设备） */
function initRenameHandler(){
  var title=document.getElementById('bannerTitle');
  if(!title){return;}
  title.style.cursor='pointer';
  title.title='点击可修改空间名称';
  title.addEventListener('click',function(){
    if(!auth.session||!auth.currentWs){
      showToast('登录后才能修改空间名');return;
    }
    var cur=auth.currentWs.name;
    var name=prompt('修改空间名称（会同步到所有队友的设备）：',cur);
    if(name===null){return;}
    name=String(name).trim();
    if(!name||name===cur){return;}
    setSyncStatus('syncing');
    renameWorkspace(auth.currentWs.id,name,function(err){
      if(err){setSyncStatus('offline');showToast('改名失败：'+err.message);return;}
      auth.currentWs.name=name;
      for(var i=0;i<auth.workspaces.length;i++){
        if(auth.workspaces[i].id===auth.currentWs.id){auth.workspaces[i].name=name;}
      }
      if(auth.currentWs.kind==='personal'){auth.personalWs=auth.currentWs;}
      else{auth.teamWs=auth.currentWs;}
      applySpaceModeUI();
      /* 同时写进 records 的 meta，双通道保证同步 */
      sbPushMeta(auth.currentWs.id,{teamName:name},function(){
        setSyncStatus('synced');
        showToast('已改名为「'+name+'」，队友会自动看到');
      });
    });
  });
}

function initAuthModule(){
  initRenameHandler();""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d patches. %d -> %d bytes'%(len(ok),orig,len(src)))
