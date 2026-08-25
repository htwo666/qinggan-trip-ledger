#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 index.html 的同步层从 textdb.online 换成 Supabase"""
import io, sys, re

P = 'index.html'
src = io.open(P, encoding='utf-8').read()
orig_len = len(src)
applied = []

def sub(name, old, new, count=1):
    global src
    if old not in src:
        print('  MISS  %s' % name)
        return False
    n = src.count(old)
    if n != count:
        print('  WARN  %s occurs %d times (expected %d)' % (name, n, count))
    src = src.replace(old, new, count)
    applied.append(name)
    print('  OK    %s' % name)
    return True

# ---------------------------------------------------------------- 1. state 增加字段
sub('state fields',
"""  pendingWrites:false,lastRemoteData:null,lastSyncTime:0
};""",
"""  pendingWrites:false,lastRemoteData:null,lastSyncTime:0,
  rtPullTimer:null,pendingJoinCode:null,dirtyTypes:{},bootDone:false
};""")

# ---------------------------------------------------------------- 2. remoteRead / remoteWrite
sub('remoteRead+remoteWrite',
"""/* 远程读取 */
function remoteRead(cb){
  httpGet(API_BASE+'/'+state.workspaceId,function(err,text){
    if(err){cb(err,null);return;}
    if(!text||text.trim()===''){cb(null,null);return;}
    try{var d=JSON.parse(text);cb(null,d);}
    catch(e){cb(new Error('parse error: '+e.message),null);}
  });
}
/* 远程写入 */
function remoteWrite(data,cb){
  var str=JSON.stringify(data);
  httpPost(API_BASE+'/update',{key:state.workspaceId,value:str},function(err,text){
    if(err){cb(err);return;}
    try{
      var r=JSON.parse(text);
      if(r.status===1){cb(null);setLSCache(data);state.lastSyncTime=Date.now();}
      else{cb(new Error('write failed: '+(r.msg||'unknown')));}
    }catch(e){cb(new Error('parse error: '+e.message));}
  });
}""",
"""/* 远程读取（Supabase records 表） */
function remoteRead(cb){
  if(!auth.session||!auth.currentWs){cb(new Error('未登录'),null);return;}
  var isPersonal=auth.currentWs.kind==='personal';
  sbPull(auth.currentWs.id,function(err,rows){
    if(err){cb(err,null);return;}
    if(!rows||!rows.length){cb(null,null);return;}
    var d=recordsToData(rows,isPersonal);
    if(d.__empty&&!d._meta){cb(null,null);return;}
    delete d.__empty;
    cb(null,d);
  });
}
/* 远程写入（Supabase push_records RPC） */
function remoteWrite(data,cb){
  if(!auth.session||!auth.currentWs){cb(new Error('未登录'));return;}
  var ws=auth.currentWs;
  /* 同时把空间名带上，实现团队名多设备同步 */
  data._meta=data._meta||{};
  data._meta.teamName=ws.name;
  data._metaTs=Date.now();
  sbPush(ws.id,data,function(err){
    if(err){cb(err);return;}
    setLSCache(data,ws.kind==='personal'?'personal':'team');
    state.lastSyncTime=Date.now();
    cb(null);
  });
}""")

# ---------------------------------------------------------------- 3. initWorkspace
sub('initWorkspace',
"""  /* 2. 团队空间：初始化 workspaceId */
  var existingId=getLSWorkspaceId();
  if(existingId){state.workspaceId=existingId;}
  else{
    state.workspaceId=genWorkspaceId();
    setLSWorkspaceId(state.workspaceId);
  }""",
"""  /* 2. workspaceId 由登录后的 Supabase 空间决定，这里不再随机生成
        （老版本随机生成 ID 正是"假同步"的根源：手机和电脑各自生成不同 ID） */
  state.workspaceId=null;""")

# ---------------------------------------------------------------- 4. switchSpace
sub('switchSpace',
"""function switchSpace(mode){
  if(mode!==state.spaceMode){
    /* 保存当前数据引用回对应空间 */
    if(state.spaceMode==='personal'){state.personalData=state.data;}
    else{state.teamData=state.data;}
    /* 切换模式 */
    state.spaceMode=mode;
    setLSSpaceMode(mode);
    /* 切换数据指针 */
    state.data=(mode==='personal')?state.personalData:state.teamData;
    /* 停掉旧轮询 */
    if(state.pollTimer){clearInterval(state.pollTimer);state.pollTimer=null;}
    /* 应用 UI */
    applySpaceModeUI();
    /* 重渲染 */
    renderAll();
    /* 团队空间：拉云端 + 启动轮询；个人空间：显示仅本地状态 */
    if(mode==='team'){
      setSyncStatus('connecting');
      pullRemote(function(){renderAll();startPolling();});
    }else{
      setSyncStatus('personal');
    }
    showToast(mode==='personal'?'已切换到个人空间（仅本地）':'已切换到团队空间（云端同步）');
  }
}""",
"""function switchSpace(mode){
  if(mode===state.spaceMode){return;}
  /* 未登录（本地试用）：保持老的纯本地双空间逻辑 */
  if(!auth.session){
    if(state.spaceMode==='personal'){state.personalData=state.data;}
    else{state.teamData=state.data;}
    state.spaceMode=mode;
    setLSSpaceMode(mode);
    state.data=(mode==='personal')?state.personalData:state.teamData;
    if(state.pollTimer){clearInterval(state.pollTimer);state.pollTimer=null;}
    applySpaceModeUI();
    renderAll();
    setSyncStatus('local');
    showToast(mode==='personal'?'已切到个人空间（本地）':'已切到团队空间（本地）');
    return;
  }
  /* 已登录：切到对应的 Supabase 空间，两个空间都云端同步 */
  var target=(mode==='personal')?auth.personalWs:auth.teamWs;
  if(!target){
    /* 该空间还不存在，现建一个 */
    setSyncStatus('syncing');
    createWorkspace(mode==='personal'?'我的个人空间':'青甘四人组',mode,function(err,ws){
      if(err){showToast('创建空间失败：'+err.message);setSyncStatus('offline');return;}
      loadWorkspaces(function(){
        var t=(mode==='personal')?auth.personalWs:auth.teamWs;
        activateWorkspace(t||ws,function(){
          showToast(mode==='personal'?'已切到个人空间（私密云端）':'已切到团队空间（共享云端）');
        });
      });
    });
    return;
  }
  activateWorkspace(target,function(){
    showToast(mode==='personal'?'已切到个人空间（私密云端）':'已切到团队空间（共享云端）');
  });
}""")

# ---------------------------------------------------------------- 5. pullRemote
sub('pullRemote',
"""function pullRemote(cb){
  /* 个人空间：不拉云端，仅本地 */
  if(state.spaceMode==='personal'){setSyncStatus('personal');if(cb)cb();return;}
  if(!state.isOnline){setSyncStatus('offline');if(cb)cb();return;}
  remoteRead(function(err,data){
    if(err){setSyncStatus('offline');showAlert('读取云端失败，使用本地缓存');if(cb)cb();return;}
    if(data){
      var merged=mergeData(state.data,data);
      /* 云端合并后同样过滤预置示例条目，防止旧预置数据回流 */
      merged.prepItems=filterPreset(merged.prepItems,'pi');
      merged.todos=filterPreset(merged.todos,'td');
      state.data=merged;state.lastRemoteData=data;setLSCache(merged);
    }
    setSyncStatus('synced');hideAlert();if(cb)cb();
  });
}""",
"""function pullRemote(cb){
  /* 未登录：纯本地模式，不访问云端 */
  if(!auth.session||!auth.currentWs){setSyncStatus('local');if(cb)cb();return;}
  if(!state.isOnline){setSyncStatus('offline');if(cb)cb();return;}
  var ws=auth.currentWs,modeKey=(ws.kind==='personal')?'personal':'team';
  remoteRead(function(err,data){
    if(err){
      setSyncStatus('offline');
      showAlert('读取云端失败，正在用本地缓存，联网后自动重试');
      if(cb)cb(err);return;
    }
    if(data){
      var merged=mergeData(state.data,data);
      merged.prepItems=filterPreset(merged.prepItems,'pi');
      merged.todos=filterPreset(merged.todos,'td');
      /* 云端的空间名以 workspaces 表为准（团队名多设备同步） */
      if(data._meta&&data._meta.teamName&&data._meta.teamName!==ws.name){
        /* 云端 meta 比本地新，说明别人改了名，采用云端的 */
        ws.name=data._meta.teamName;
        for(var i=0;i<auth.workspaces.length;i++){
          if(auth.workspaces[i].id===ws.id){auth.workspaces[i].name=ws.name;}
        }
        applySpaceModeUI();
      }
      state.data=merged;state.lastRemoteData=data;setLSCache(merged,modeKey);
    }else{
      /* 云端是空的：首次登录，把本地数据上传上去（数据迁移） */
      if(!state.migrated_[ws.id]){
        state.migrated_[ws.id]=true;
        var local=state.data;
        var hasLocal=local&&((local.expenses||[]).length||(local.prepaid||[]).length||
                             (local.prepItems||[]).length||(local.todos||[]).length);
        if(hasLocal){
          setSyncStatus('syncing');
          remoteWrite(local,function(e){
            setSyncStatus(e?'offline':'synced');
            if(!e){showToast('本机数据已上传到云端');}
            if(cb)cb();
          });
          return;
        }
      }
    }
    setSyncStatus('synced');hideAlert();if(cb)cb();
  });
}""")

# ---------------------------------------------------------------- 6. doWrite
sub('doWrite',
"""function doWrite(){
  if(!state.isOnline){state.pendingWrites=true;setSyncStatus('offline');return;}""",
"""function doWrite(){
  if(!auth.session||!auth.currentWs){setSyncStatus('local');return;}
  if(!state.isOnline){state.pendingWrites=true;setSyncStatus('offline');return;}""")

# ---------------------------------------------------------------- 7. saveData
sub('saveData',
"""function saveData(){
  setLSCache(state.data);
  /* 个人空间：仅本地保存，不同步云端 */
  if(state.spaceMode==='personal'){return;}
  /* 团队空间：触发防抖写入 */
  scheduleWrite();
}""",
"""function saveData(){
  setLSCache(state.data,state.spaceMode);
  /* 未登录（本地试用）：只存本机 */
  if(!auth.session||!auth.currentWs){setSyncStatus('local');return;}
  /* 已登录：团队空间和个人空间都同步到云端（个人空间由 RLS 保证只有本人可见） */
  scheduleWrite();
}""")

# ---------------------------------------------------------------- 8. setSyncStatus 增加 local / personal 文案
sub('setSyncStatus',
"""    case 'personal':
      text.textContent='个人空间 · 仅本地';
      dot.classList.add('offline');
      retry.style.display='none';
      break;""",
"""    case 'personal':
      text.textContent='私密空间 · 已同步';
      retry.style.display='none';
      break;
    case 'local':
      text.textContent='本地模式 · 未登录';
      dot.classList.add('offline');
      retry.style.display='none';
      break;""")

# ---------------------------------------------------------------- 9. startPolling：改成 Realtime 兜底轮询
sub('startPolling',
"""function startPolling(){
  /* 个人空间：无需轮询云端 */
  if(state.spaceMode==='personal'){setSyncStatus('personal');return;}
  if(state.pollTimer){clearInterval(state.pollTimer);}
  state.pollTimer=setInterval(function(){pullRemote(function(){renderAll();});},POLL_INTERVAL);
}""",
"""function startPolling(){
  /* 未登录：无云端可轮询 */
  if(!auth.session||!auth.currentWs){setSyncStatus('local');return;}
  if(state.pollTimer){clearInterval(state.pollTimer);}
  /* Realtime 已经推送变更，这里只做兜底轮询（防止 WebSocket 被网络环境掐断） */
  var interval=auth.rtChannel?120000:POLL_INTERVAL;
  state.pollTimer=setInterval(function(){pullRemote(function(){renderAll();});},interval);
}""")

# ---------------------------------------------------------------- 10. visibilitychange / online
sub('visibilitychange',
"""document.addEventListener('visibilitychange',function(){
  if(document.hidden){return;}
  if(state.spaceMode==='personal'){renderAll();return;}
  pullRemote(function(){renderAll();});
});""",
"""document.addEventListener('visibilitychange',function(){
  if(document.hidden){return;}
  if(!auth.session||!auth.currentWs){renderAll();return;}
  /* 回到前台立刻拉一次，并重连 Realtime */
  pullRemote(function(){renderAll();});
  if(!auth.rtChannel){startRealtime(auth.currentWs.id);}
});""")

# ---------------------------------------------------------------- 11. 旧 showSyncModal / bindSyncCode / handleSyncUrlParam 相关
sub('showSyncModal',
"""function showSyncModal(){
  if(state.spaceMode==='personal'){
    showToast('个人空间不需要同步码');
    return;
  }""",
"""function showSyncModal(){
  showWorkspaceModal();
  return;
  /* eslint-disable no-unreachable */
  if(false){""")

# 关闭上面被短路的旧函数体：找到旧 showSyncModal 尾部的 switchSyncTab 调用块
sub('showSyncModal tail',
"""  /* 重置到第一个 tab */
  switchSyncTab('qr');
  document.getElementById('syncModal').classList.add('show');
}""",
"""  }
}""")

# ---------------------------------------------------------------- 12. buildShareLink 改成邀请码链接
sub('buildShareLink',
"""function buildShareLink(){
  return 'https://htwo666.github.io/qinggan-trip-ledger/?sync='+encodeURIComponent(state.workspaceId||'');
}""",
"""function buildShareLink(){
  var code=(auth.teamWs&&auth.teamWs.invite_code)||'';
  return 'https://htwo666.github.io/qinggan-trip-ledger/?join='+encodeURIComponent(code);
}""")

# ---------------------------------------------------------------- 13. init()
sub('init',
"""function init(){
  initWorkspace();
  handleSyncUrlParam(); /* 处理 URL 中的 ?sync=xxx 邀请链接 */
  renderCountdown();
  renderTabs();
  renderPanels();
  initAIModule(); /* 初始化 AI 旅伴模块 */
  /* 根据空间模式决定初始状态 */
  if(state.spaceMode==='personal'){
    setSyncStatus('personal');
  }else{
    setSyncStatus('connecting');
  }
  /* 先渲染界面（用本地缓存）后拉云端 */
  pullRemote(function(){
    renderCountdown();
    renderCurrentPanel();
    startPolling();
  });
  registerSW();
}""",
"""function init(){
  state.migrated_={};
  initWorkspace();
  handleJoinUrlParam();  /* 处理 URL 中的 ?join=邀请码 */
  renderCountdown();
  renderTabs();
  renderPanels();
  initAIModule();
  initAuthModule();
  registerSW();
  /* 恢复已保存的登录会话 */
  auth.session=loadSession();
  var guestOk=false;
  try{guestOk=localStorage.getItem('qinggan_guest_ok')==='1';}catch(e){}
  updateUserBadge();
  if(auth.session&&auth.session.refresh_token){
    /* 有会话：刷新 token 后进入正常流程 */
    setSyncStatus('connecting');
    refreshToken(function(err){
      if(err){
        /* 会话失效，回到登录页 */
        setSyncStatus('local');
        updateUserBadge();
        showAuthScreen();
        return;
      }
      bootAfterLogin(function(e){
        updateUserBadge();
        if(e){showToast('加载云端数据失败，正在用本地缓存');}
        consumePendingJoin(function(){
          startPolling();
          state.bootDone=true;
        });
      });
    });
  }else if(state.pendingJoinCode){
    /* 通过邀请链接进来的新用户：直接引导注册 */
    setSyncStatus('local');
    showAuthScreen();
    setAuthTab('signup');
    setAuthMsg('注册后将自动加入团队（邀请码 <b>'+escapeHtml(state.pendingJoinCode)+'</b>）','info');
  }else if(guestOk){
    /* 之前选过"本地试用" */
    auth.guestMode=true;
    setSyncStatus('local');
    renderCurrentPanel();
  }else{
    /* 首次打开：显示登录页 */
    setSyncStatus('local');
    showAuthScreen();
  }
}""")

# ---------------------------------------------------------------- 14. 插入 Supabase 客户端模块
module = io.open('supabase/client_module.js', encoding='utf-8').read()
anchor = "/* 初始化默认数据结构（复用给团队空间和个人空间） */"
if anchor in src:
    src = src.replace(anchor, module + "\n" + anchor, 1)
    applied.append('client module inserted')
    print('  OK    client module inserted')
else:
    print('  MISS  client module anchor')

io.open(P, 'w', encoding='utf-8').write(src)
print('\n%d patches applied. %d -> %d bytes' % (len(applied), orig_len, len(src)))
