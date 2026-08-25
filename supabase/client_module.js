/* ============================================================
   Supabase 后端模块 v4
   真实账号鉴权 + 团队共享空间 + 私密个人空间 + Realtime 实时同步
   ============================================================ */
var SB_URL='https://cxvwynfwoppyzjopzpkz.supabase.co';
var SB_ANON='sb_publishable_tL1-YiaZ0AJcVCpqCt5d8A_p91RFmYJ';
var SB_SESSION_KEY='qinggan_sb_session';
var SB_WS_KEY='qinggan_sb_current_ws';
/* 数据类型 <-> records.kind 映射 */
var KIND_MAP={prepItems:'prepItem',prepaid:'prepaid',expenses:'expense',
              outfits:'outfit',todos:'todo',prepTodos:'prepTodo',members:'member'};
var KIND_REVERSE={};
(function(){for(var k in KIND_MAP){if(KIND_MAP.hasOwnProperty(k)){KIND_REVERSE[KIND_MAP[k]]=k;}}})();
var DATA_TYPES=['prepItems','prepaid','expenses','outfits','todos','members','prepTodos'];

var auth={
  session:null,        /* {access_token, refresh_token, expires_at, user:{id,email}} */
  profile:null,        /* {id, nickname} */
  workspaces:[],       /* my_workspaces() 结果 */
  currentWs:null,      /* 当前激活的 workspace 对象 */
  teamWs:null,         /* 团队空间（最近使用的） */
  personalWs:null,     /* 个人空间 */
  guestMode:false,     /* 未登录本地试用 */
  wsMembers:[],        /* 当前空间成员 */
  rtChannel:null,      /* Realtime WebSocket */
  rtRef:0
};

/* ---------- 会话持久化 ---------- */
function saveSession(s){
  try{
    if(s){localStorage.setItem(SB_SESSION_KEY,JSON.stringify(s));}
    else{localStorage.removeItem(SB_SESSION_KEY);}
  }catch(e){}
}
function loadSession(){
  try{return JSON.parse(localStorage.getItem(SB_SESSION_KEY)||'null');}catch(e){return null;}
}
function saveCurrentWsId(id){
  try{
    if(id){localStorage.setItem(SB_WS_KEY,id);}
    else{localStorage.removeItem(SB_WS_KEY);}
  }catch(e){}
}
function loadCurrentWsId(){try{return localStorage.getItem(SB_WS_KEY);}catch(e){return null;}}

/* ---------- 通用 HTTP（JSON，带鉴权） ---------- */
function sbRequest(path,opts,cb){
  opts=opts||{};
  var xhr=new XMLHttpRequest();
  xhr.open(opts.method||'GET',SB_URL+path,true);
  xhr.timeout=opts.timeout||20000;
  xhr.setRequestHeader('apikey',SB_ANON);
  var tok=(auth.session&&auth.session.access_token)?auth.session.access_token:SB_ANON;
  if(opts.noAuth){tok=SB_ANON;}
  xhr.setRequestHeader('Authorization','Bearer '+tok);
  xhr.setRequestHeader('Content-Type','application/json');
  if(opts.prefer){xhr.setRequestHeader('Prefer',opts.prefer);}
  xhr.onreadystatechange=function(){
    if(xhr.readyState!==4){return;}
    var body=null;
    if(xhr.responseText&&xhr.responseText.trim()!==''){
      try{body=JSON.parse(xhr.responseText);}catch(e){body=xhr.responseText;}
    }
    if(xhr.status>=200&&xhr.status<300){cb(null,body,xhr.status);}
    else{
      var msg=(body&&(body.message||body.error_description||body.msg||body.error))||('HTTP '+xhr.status);
      var err=new Error(msg);err.status=xhr.status;err.body=body;
      cb(err,body,xhr.status);
    }
  };
  xhr.ontimeout=function(){cb(new Error('请求超时，请检查网络'));};
  xhr.onerror=function(){cb(new Error('网络错误，请检查网络连接'));};
  xhr.send(opts.body?JSON.stringify(opts.body):null);
}
/* 带 token 自动刷新的请求 */
function sbAuthed(path,opts,cb){
  if(auth.session&&auth.session.expires_at&&
     (auth.session.expires_at*1000-Date.now())<60000&&auth.session.refresh_token){
    refreshToken(function(){sbRequest(path,opts,cb);});
    return;
  }
  sbRequest(path,opts,function(err,body,status){
    if(err&&status===401&&auth.session&&auth.session.refresh_token){
      refreshToken(function(rerr){
        if(rerr){cb(err,body,status);return;}
        sbRequest(path,opts,cb);
      });
      return;
    }
    cb(err,body,status);
  });
}
function rpc(fn,args,cb){sbAuthed('/rest/v1/rpc/'+fn,{method:'POST',body:args||{}},cb);}

/* ---------- 认证 ---------- */
function refreshToken(cb){
  var rt=auth.session&&auth.session.refresh_token;
  if(!rt){cb(new Error('no refresh token'));return;}
  sbRequest('/auth/v1/token?grant_type=refresh_token',
    {method:'POST',body:{refresh_token:rt},noAuth:true},
    function(err,body){
      if(err||!body||!body.access_token){
        auth.session=null;saveSession(null);cb(err||new Error('refresh failed'));return;
      }
      auth.session=body;saveSession(body);cb(null);
    });
}
function signUp(email,password,nickname,cb){
  sbRequest('/auth/v1/signup',
    {method:'POST',noAuth:true,body:{email:email,password:password,data:{nickname:nickname||''}}},
    function(err,body){
      if(err){cb(err);return;}
      /* 免验证模式下 signup 直接返回 session */
      if(body&&body.access_token){auth.session=body;saveSession(body);cb(null,body);return;}
      /* 兜底：立刻用密码登录一次 */
      signIn(email,password,cb);
    });
}
function signIn(email,password,cb){
  sbRequest('/auth/v1/token?grant_type=password',
    {method:'POST',noAuth:true,body:{email:email,password:password}},
    function(err,body){
      if(err){cb(err);return;}
      if(!body||!body.access_token){cb(new Error('登录失败，请重试'));return;}
      auth.session=body;saveSession(body);cb(null,body);
    });
}
function signOut(cb){
  var done=function(){
    stopRealtime();
    auth.session=null;auth.profile=null;auth.workspaces=[];
    auth.currentWs=null;auth.teamWs=null;auth.personalWs=null;auth.wsMembers=[];
    saveSession(null);saveCurrentWsId(null);
    if(cb)cb();
  };
  if(!auth.session){done();return;}
  sbRequest('/auth/v1/logout',{method:'POST'},function(){done();});
}
function currentUserId(){
  return (auth.session&&auth.session.user&&auth.session.user.id)||null;
}
function currentNickname(){
  if(auth.profile&&auth.profile.nickname){return auth.profile.nickname;}
  var u=auth.session&&auth.session.user;
  if(u&&u.user_metadata&&u.user_metadata.nickname){return u.user_metadata.nickname;}
  if(u&&u.email){return u.email.split('@')[0];}
  return '旅行者';
}

/* ---------- 用户资料 ---------- */
function loadProfile(cb){
  var uid=currentUserId();
  if(!uid){cb(new Error('not logged in'));return;}
  sbAuthed('/rest/v1/profiles?id=eq.'+uid+'&select=*',{},function(err,body){
    if(err){cb(err);return;}
    auth.profile=(body&&body.length)?body[0]:null;
    cb(null,auth.profile);
  });
}
function updateNickname(nick,cb){
  var uid=currentUserId();
  if(!uid){cb&&cb(new Error('not logged in'));return;}
  sbAuthed('/rest/v1/profiles?id=eq.'+uid,
    {method:'PATCH',body:{nickname:nick},prefer:'return=representation'},
    function(err,body){
      if(!err&&body&&body.length){auth.profile=body[0];}
      cb&&cb(err,body);
    });
}

/* ---------- 空间管理 ---------- */
function loadWorkspaces(cb){
  rpc('my_workspaces',{},function(err,body){
    if(err){cb(err);return;}
    auth.workspaces=body||[];
    auth.teamWs=null;auth.personalWs=null;
    for(var i=0;i<auth.workspaces.length;i++){
      var w=auth.workspaces[i];
      if(w.kind==='personal'&&!auth.personalWs){auth.personalWs=w;}
      if(w.kind==='team'&&!auth.teamWs){auth.teamWs=w;}
    }
    cb(null,auth.workspaces);
  });
}
function createWorkspace(name,kind,cb){
  rpc('create_workspace',{p_name:name,p_kind:kind},function(err,body){
    if(err){cb(err);return;}
    var ws=Array.isArray(body)?body[0]:body;
    cb(null,ws);
  });
}
function joinWorkspace(code,cb){
  rpc('join_workspace',{p_code:String(code||'').toUpperCase().trim()},function(err,body){
    if(err){cb(err);return;}
    var ws=Array.isArray(body)?body[0]:body;
    cb(null,ws);
  });
}
function loadWsMembers(wsId,cb){
  rpc('ws_members',{p_ws:wsId},function(err,body){
    if(!err){auth.wsMembers=body||[];}
    cb&&cb(err,body);
  });
}
/* 确保用户至少有一个团队空间和一个个人空间 */
function ensureWorkspaces(cb){
  loadWorkspaces(function(err){
    if(err){cb(err);return;}
    var need=[];
    if(!auth.teamWs){need.push(['青甘四人组','team']);}
    if(!auth.personalWs){need.push(['我的个人空间','personal']);}
    if(!need.length){cb(null);return;}
    var i=0;
    var next=function(){
      if(i>=need.length){loadWorkspaces(function(e){cb(e||null);});return;}
      var item=need[i++];
      createWorkspace(item[0],item[1],function(e){
        if(e){cb(e);return;}
        next();
      });
    };
    next();
  });
}

/* ---------- 数据读写：records 表 <-> state.data ---------- */
/* state.data 转 records 数组 */
function dataToRecords(data){
  var out=[];
  for(var t=0;t<DATA_TYPES.length;t++){
    var type=DATA_TYPES[t],kind=KIND_MAP[type],arr=data[type]||[];
    for(var i=0;i<arr.length;i++){
      var it=arr[i];
      if(!it||!it.id){continue;}
      var payload={};
      for(var k in it){
        if(it.hasOwnProperty(k)&&k!=='_ts'&&k!=='_deleted'){payload[k]=it[k];}
      }
      out.push({id:kind+':'+it.id,kind:kind,payload:payload,
                ts:it._ts||Date.now(),deleted:!!it._deleted});
    }
  }
  /* 空间元数据（团队名等） */
  if(data._meta){
    out.push({id:'meta:main',kind:'meta',payload:data._meta,
              ts:data._metaTs||Date.now(),deleted:false});
  }
  return out;
}
/* records 数组转 state.data */
function recordsToData(rows,isPersonal){
  var d={prepItems:[],prepaid:[],expenses:[],outfits:[],todos:[],members:[],prepTodos:[]};
  var hasAny=false;
  for(var i=0;i<(rows||[]).length;i++){
    var r=rows[i];
    if(!r||!r.kind){continue;}
    if(r.kind==='meta'){
      d._meta=r.payload||{};d._metaTs=r.ts||0;continue;
    }
    var type=KIND_REVERSE[r.kind];
    if(!type){continue;}
    hasAny=true;
    var it=r.payload||{};
    var obj={};
    for(var k in it){if(it.hasOwnProperty(k)){obj[k]=it[k];}}
    /* id 去掉 kind 前缀 */
    var rawId=String(r.id||'');
    var colon=rawId.indexOf(':');
    obj.id=(colon>=0)?rawId.slice(colon+1):rawId;
    obj._ts=r.ts||0;
    if(r.deleted){obj._deleted=true;}
    d[type].push(obj);
  }
  d.__empty=!hasAny;
  return d;
}
/* 从云端拉取整个空间的数据 */
function sbPull(wsId,cb){
  sbAuthed('/rest/v1/records?workspace_id=eq.'+wsId+'&select=id,kind,payload,ts,deleted&order=ts.asc',
    {},function(err,body){
      if(err){cb(err);return;}
      cb(null,body||[]);
    });
}
/* 推送整个空间的数据 */
function sbPush(wsId,data,cb){
  var recs=dataToRecords(data);
  if(!recs.length){cb&&cb(null,0);return;}
  rpc('push_records',{p_ws:wsId,p_records:recs},function(err,body){
    cb&&cb(err,body);
  });
}
/* 推送单条变更（增量，性能更好） */
function sbPushOne(wsId,type,item,cb){
  var kind=KIND_MAP[type];
  if(!kind||!item||!item.id){cb&&cb(null);return;}
  var payload={};
  for(var k in item){
    if(item.hasOwnProperty(k)&&k!=='_ts'&&k!=='_deleted'){payload[k]=item[k];}
  }
  rpc('push_records',{p_ws:wsId,p_records:[{
    id:kind+':'+item.id,kind:kind,payload:payload,
    ts:item._ts||Date.now(),deleted:!!item._deleted
  }]},function(err){cb&&cb(err);});
}
/* 推送空间元数据 */
function sbPushMeta(wsId,meta,cb){
  rpc('push_records',{p_ws:wsId,p_records:[{
    id:'meta:main',kind:'meta',payload:meta||{},ts:Date.now(),deleted:false
  }]},function(err){cb&&cb(err);});
}
/* 重命名空间 */
function renameWorkspace(wsId,name,cb){
  sbAuthed('/rest/v1/workspaces?id=eq.'+wsId,
    {method:'PATCH',body:{name:name},prefer:'return=representation'},
    function(err,body){cb&&cb(err,body);});
}

/* ---------- Realtime 实时订阅（WebSocket） ---------- */
function stopRealtime(){
  if(auth.rtChannel){
    try{auth.rtChannel.close();}catch(e){}
    auth.rtChannel=null;
  }
}
function startRealtime(wsId){
  stopRealtime();
  if(!wsId||!auth.session||!window.WebSocket){return;}
  try{
    var wsUrl=SB_URL.replace(/^https/,'wss')+'/realtime/v1/websocket?apikey='+
              encodeURIComponent(SB_ANON)+'&vsn=1.0.0';
    var sock=new WebSocket(wsUrl);
    auth.rtChannel=sock;
    var topic='realtime:qg:'+wsId;
    var hb=null;
    sock.onopen=function(){
      sock.send(JSON.stringify({
        topic:topic,event:'phx_join',
        payload:{config:{
          broadcast:{self:false},presence:{key:''},
          postgres_changes:[{event:'*',schema:'public',table:'records',
                             filter:'workspace_id=eq.'+wsId}]
        },access_token:auth.session.access_token},
        ref:String(++auth.rtRef)
      }));
      hb=setInterval(function(){
        if(sock.readyState===1){
          sock.send(JSON.stringify({topic:'phoenix',event:'heartbeat',payload:{},ref:String(++auth.rtRef)}));
        }
      },28000);
    };
    sock.onmessage=function(ev){
      var m;try{m=JSON.parse(ev.data);}catch(e){return;}
      if(m.event==='postgres_changes'&&m.payload&&m.payload.data){
        /* 别人改了数据，300ms 防抖后拉取（合并多条连续变更） */
        if(state.rtPullTimer){clearTimeout(state.rtPullTimer);}
        state.rtPullTimer=setTimeout(function(){
          pullRemote(function(){renderAll();});
        },350);
      }
    };
    sock.onclose=function(){
      if(hb){clearInterval(hb);hb=null;}
      /* 5 秒后自动重连（仅当仍是同一空间且已登录） */
      setTimeout(function(){
        if(auth.session&&auth.currentWs&&auth.currentWs.id===wsId&&!auth.rtChannel){
          startRealtime(wsId);
        }
      },5000);
      if(auth.rtChannel===sock){auth.rtChannel=null;}
    };
    sock.onerror=function(){};
  }catch(e){}
}

/* ---------- 登录 UI ---------- */
var authTab='login';
function showAuthScreen(){
  document.getElementById('authScreen').classList.add('show');
  setAuthTab('login');
  setAuthMsg('','');
}
function hideAuthScreen(){
  document.getElementById('authScreen').classList.remove('show');
}
function setAuthTab(tab){
  authTab=tab;
  var tabs=document.querySelectorAll('.auth-tab');
  for(var i=0;i<tabs.length;i++){
    tabs[i].classList.toggle('active',tabs[i].getAttribute('data-authtab')===tab);
  }
  document.getElementById('authNickField').style.display=(tab==='signup')?'block':'none';
  document.getElementById('authSubmit').textContent=(tab==='signup')?'注册并开始使用':'登录';
  document.getElementById('authPassword').setAttribute('autocomplete',
    (tab==='signup')?'new-password':'current-password');
  document.getElementById('authPwHint').textContent=(tab==='signup')
    ? '注册不需要邮箱验证，填完直接就能用。'
    : '忘记密码？换个邮箱重新注册，再用邀请码加回团队。';
  setAuthMsg('','');
}
function setAuthMsg(msg,type){
  var el=document.getElementById('authMsg');
  if(!msg){el.className='auth-msg';el.textContent='';return;}
  el.className='auth-msg show '+(type||'err');
  el.innerHTML=msg;
}
function translateAuthError(msg){
  msg=String(msg||'');
  if(/Invalid login credentials/i.test(msg)){return '邮箱或密码不对。第一次用请点上面的「注册」。';}
  if(/User already registered|already been registered/i.test(msg)){return '这个邮箱已经注册过了，请点「登录」。';}
  if(/Password should be at least/i.test(msg)){return '密码太短，至少 6 位。';}
  if(/Unable to validate email|invalid format|valid email/i.test(msg)){return '邮箱格式不对，检查一下。';}
  if(/rate limit|too many/i.test(msg)){return '操作太频繁，等一分钟再试。';}
  if(/timeout|超时/i.test(msg)){return '网络超时，检查网络后重试。';}
  if(/network|网络/i.test(msg)){return '网络连不上，检查网络后重试。';}
  return msg;
}
function doAuthSubmit(){
  var email=document.getElementById('authEmail').value.trim();
  var pw=document.getElementById('authPassword').value;
  var nick=document.getElementById('authNick').value.trim();
  var btn=document.getElementById('authSubmit');
  if(!email||email.indexOf('@')<0){setAuthMsg('请填写正确的邮箱','err');return;}
  if(!pw||pw.length<6){setAuthMsg('密码至少 6 位','err');return;}
  btn.disabled=true;
  btn.textContent=(authTab==='signup')?'注册中...':'登录中...';
  setAuthMsg('','');
  var after=function(err){
    if(err){
      btn.disabled=false;
      btn.textContent=(authTab==='signup')?'注册并开始使用':'登录';
      setAuthMsg(translateAuthError(err.message),'err');
      return;
    }
    setAuthMsg('成功，正在加载你的数据...','ok');
    bootAfterLogin(function(e2){
      btn.disabled=false;
      btn.textContent=(authTab==='signup')?'注册并开始使用':'登录';
      if(e2){setAuthMsg(translateAuthError(e2.message),'err');return;}
      hideAuthScreen();
      showToast('欢迎，'+currentNickname()+'！');
    });
  };
  if(authTab==='signup'){signUp(email,pw,nick,after);}
  else{signIn(email,pw,after);}
}

/* ---------- 登录后启动流程 ---------- */
function bootAfterLogin(cb){
  auth.guestMode=false;
  loadProfile(function(){
    ensureWorkspaces(function(err){
      if(err){cb&&cb(err);return;}
      /* 恢复上次使用的空间；否则按当前 spaceMode 选 */
      var savedId=loadCurrentWsId(),target=null;
      for(var i=0;i<auth.workspaces.length;i++){
        if(auth.workspaces[i].id===savedId){target=auth.workspaces[i];break;}
      }
      if(!target){
        target=(state.spaceMode==='personal')?auth.personalWs:auth.teamWs;
      }
      if(!target){target=auth.workspaces[0];}
      activateWorkspace(target,function(e){
        updateUserBadge();
        cb&&cb(e||null);
      });
    });
  });
}
/* 激活某个空间：切 spaceMode、拉数据、开实时订阅 */
function activateWorkspace(ws,cb){
  if(!ws){cb&&cb(new Error('空间不存在'));return;}
  auth.currentWs=ws;
  saveCurrentWsId(ws.id);
  var isPersonal=ws.kind==='personal';
  state.spaceMode=isPersonal?'personal':'team';
  setLSSpaceMode(state.spaceMode);
  if(ws.kind==='personal'){auth.personalWs=ws;}else{auth.teamWs=ws;}
  /* 先用本地缓存渲染，避免白屏 */
  var cached=getLSCache(state.spaceMode);
  if(cached){state.data=normalizeData(cached,isPersonal);}
  else{state.data=buildDefaultData(isPersonal);}
  applySpaceModeUI();
  renderAll();
  setSyncStatus('connecting');
  loadWsMembers(ws.id,function(){renderAll();});
  pullRemote(function(err){
    renderCountdown();
    renderAll();
    startRealtime(ws.id);
    cb&&cb(err||null);
  });
}

/* ---------- 用户徽章 ---------- */
function updateUserBadge(){
  var badge=document.getElementById('userBadge');
  if(!badge){return;}
  if(auth.session){
    var nick=currentNickname();
    badge.style.display='flex';
    document.getElementById('ubAvatar').textContent=nick.charAt(0);
    document.getElementById('ubName').textContent=nick;
    badge.title=(auth.session.user&&auth.session.user.email)||nick;
  }else{
    badge.style.display='flex';
    document.getElementById('ubAvatar').textContent='?';
    document.getElementById('ubName').textContent='登录';
    badge.title='点击登录，数据即可多设备同步';
  }
}

/* ---------- 空间管理弹窗 ---------- */
function setWsMsg(msg,type){
  var el=document.getElementById('wsMsg');
  if(!el){return;}
  if(!msg){el.className='auth-msg';el.textContent='';return;}
  el.className='auth-msg show '+(type||'err');
  el.innerHTML=msg;
}
function showWorkspaceModal(){
  var guest=document.getElementById('wsGuestBox');
  var userBox=document.getElementById('wsUserBox');
  setWsMsg('','');
  if(!auth.session){
    guest.style.display='block';
    userBox.style.display='none';
  }else{
    guest.style.display='none';
    userBox.style.display='block';
    renderWsList();
    renderInviteBox();
  }
  document.getElementById('syncModal').classList.add('show');
}
function renderWsList(){
  var el=document.getElementById('wsList');
  if(!el){return;}
  if(!auth.workspaces.length){el.innerHTML='<div class="empty">暂无空间</div>';return;}
  var h='';
  for(var i=0;i<auth.workspaces.length;i++){
    var w=auth.workspaces[i];
    var cur=auth.currentWs&&auth.currentWs.id===w.id;
    var isP=w.kind==='personal';
    h+='<button class="ws-item'+(cur?' current':'')+' kind-'+w.kind+'" data-wsid="'+w.id+'">'
      + '<span class="ws-item-icon">'+(isP?'🔒':'👥')+'</span>'
      + '<span class="ws-item-body">'
      +   '<span class="ws-item-name">'+escapeHtml(w.name)+(cur?' ·<span style="color:var(--primary);font-size:0.72rem"> 当前</span>':'')+'</span>'
      +   '<span class="ws-item-meta">'+(isP?'私密 · 只有你能看':'团队 · '+w.member_count+' 人')
      +     (w.is_owner?' · 我创建的':'')+'</span>'
      + '</span>'
      + (w.invite_code?'<span class="ws-item-code">'+escapeHtml(w.invite_code)+'</span>':'')
      + '</button>';
  }
  el.innerHTML=h;
  var btns=el.querySelectorAll('.ws-item');
  for(var j=0;j<btns.length;j++){
    btns[j].addEventListener('click',function(){
      var id=this.getAttribute('data-wsid');
      var target=null;
      for(var k=0;k<auth.workspaces.length;k++){
        if(auth.workspaces[k].id===id){target=auth.workspaces[k];break;}
      }
      if(!target||(auth.currentWs&&auth.currentWs.id===id)){
        document.getElementById('syncModal').classList.remove('show');return;
      }
      document.getElementById('syncModal').classList.remove('show');
      showToast('正在切换到「'+target.name+'」...');
      activateWorkspace(target,function(){
        showToast('已切换到「'+target.name+'」');
      });
    });
  }
}
function renderInviteBox(){
  var box=document.getElementById('wsInviteBox');
  var ws=auth.teamWs;
  if(!ws||!ws.invite_code){box.style.display='none';return;}
  box.style.display='block';
  document.getElementById('wsInviteCode').textContent=ws.invite_code;
  var link=buildInviteLink(ws.invite_code);
  document.getElementById('wsShareLink').value=link;
  document.getElementById('wsQrImg').src=buildQrImageUrl(link);
}
function buildInviteLink(code){
  return 'https://htwo666.github.io/qinggan-trip-ledger/?join='+encodeURIComponent(code||'');
}
/* 处理 URL 中的 ?join=CODE 邀请链接 */
function handleJoinUrlParam(){
  var code=null;
  try{
    var url=new URL(window.location.href);
    code=url.searchParams.get('join');
    if(code){
      url.searchParams.delete('join');
      window.history.replaceState({},document.title,url.toString());
    }
  }catch(e){}
  if(!code){return;}
  state.pendingJoinCode=String(code).toUpperCase().trim();
}
/* 登录后消费待处理的邀请码 */
function consumePendingJoin(cb){
  var code=state.pendingJoinCode;
  if(!code||!auth.session){cb&&cb();return;}
  state.pendingJoinCode=null;
  joinWorkspace(code,function(err,ws){
    if(err){showToast('邀请码无效或已失效');cb&&cb();return;}
    loadWorkspaces(function(){
      activateWorkspace(ws,function(){
        showToast('已加入团队「'+ws.name+'」');
        cb&&cb();
      });
    });
  });
}
function doJoinTeam(){
  var input=document.getElementById('wsJoinInput');
  var code=String(input.value||'').toUpperCase().trim();
  if(code.length<4){setWsMsg('请输入完整的邀请码','err');return;}
  var btn=document.getElementById('wsJoinBtn');
  btn.disabled=true;btn.textContent='加入中...';
  joinWorkspace(code,function(err,ws){
    btn.disabled=false;btn.textContent='加入';
    if(err){setWsMsg(/邀请码无效/.test(err.message)?'邀请码不对，跟队友核对一下':translateAuthError(err.message),'err');return;}
    input.value='';
    loadWorkspaces(function(){
      renderWsList();renderInviteBox();
      setWsMsg('已加入「'+escapeHtml(ws.name)+'」，正在切换...','ok');
      setTimeout(function(){
        document.getElementById('syncModal').classList.remove('show');
        activateWorkspace(ws,function(){showToast('已加入团队「'+ws.name+'」');});
      },700);
    });
  });
}
function doCreateTeam(){
  var name=prompt('新团队叫什么名字？','我的新团队');
  if(name===null){return;}
  var btn=document.getElementById('wsNewTeamBtn');
  btn.disabled=true;btn.textContent='创建中...';
  createWorkspace(name||'我的新团队','team',function(err,ws){
    btn.disabled=false;btn.textContent='＋ 新建一个团队';
    if(err){setWsMsg(translateAuthError(err.message),'err');return;}
    loadWorkspaces(function(){
      renderWsList();renderInviteBox();
      setWsMsg('已创建「'+escapeHtml(ws.name)+'」，邀请码 '+ws.invite_code,'ok');
    });
  });
}

/* ---------- 绑定所有认证相关事件 ---------- */
function initAuthModule(){
  /* 登录页 tab */
  var tabs=document.querySelectorAll('.auth-tab');
  for(var i=0;i<tabs.length;i++){
    tabs[i].addEventListener('click',function(){
      setAuthTab(this.getAttribute('data-authtab'));
    });
  }
  document.getElementById('authSubmit').addEventListener('click',doAuthSubmit);
  var enterSubmit=function(e){if(e.key==='Enter'||e.keyCode===13){doAuthSubmit();}};
  document.getElementById('authEmail').addEventListener('keydown',enterSubmit);
  document.getElementById('authPassword').addEventListener('keydown',enterSubmit);
  document.getElementById('authNick').addEventListener('keydown',enterSubmit);
  /* 本地试用 */
  document.getElementById('authSkip').addEventListener('click',function(){
    auth.guestMode=true;
    try{localStorage.setItem('qinggan_guest_ok','1');}catch(e){}
    hideAuthScreen();
    setSyncStatus('local');
    updateUserBadge();
    renderAll();
    showToast('本地试用模式 · 数据仅存本机');
  });
  /* 用户徽章 → 未登录去登录页，已登录开空间管理 */
  document.getElementById('userBadge').addEventListener('click',function(){
    if(auth.session){showWorkspaceModal();}
    else{showAuthScreen();}
  });
  /* 空间弹窗内的按钮 */
  document.getElementById('wsGoLoginBtn').addEventListener('click',function(){
    document.getElementById('syncModal').classList.remove('show');
    showAuthScreen();
  });
  document.getElementById('wsJoinBtn').addEventListener('click',doJoinTeam);
  document.getElementById('wsJoinInput').addEventListener('keydown',function(e){
    if(e.key==='Enter'||e.keyCode===13){doJoinTeam();}
  });
  document.getElementById('wsNewTeamBtn').addEventListener('click',doCreateTeam);
  document.getElementById('wsCopyLinkBtn').addEventListener('click',function(){
    var inp=document.getElementById('wsShareLink');
    inp.select();
    try{document.execCommand('copy');showToast('邀请链接已复制');}
    catch(e){showToast('请长按手动复制');}
  });
  document.getElementById('wsLogoutBtn').addEventListener('click',function(){
    showConfirm('退出登录','退出后本设备将回到本地模式，云端数据不会丢失，重新登录即可恢复。',function(){
      signOut(function(){
        document.getElementById('syncModal').classList.remove('show');
        updateUserBadge();
        showAuthScreen();
        showToast('已退出登录');
      });
    });
  });
  /* 邀请码输入自动大写 */
  document.getElementById('wsJoinInput').addEventListener('input',function(){
    this.value=this.value.toUpperCase();
  });
}
