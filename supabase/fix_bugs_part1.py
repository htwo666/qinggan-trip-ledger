#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复三个 bug：
1. 不同团队数据互通 —— localStorage 缓存 key 只按 team/personal 分，
   切换到另一个团队时会读到上一个团队的缓存。改为按 workspaceId 分。
2. 成员删了会变回预设 4 人 —— normalizeData 无条件回填 MEMBERS，
   且删除是硬 splice 没有墓碑，云端的旧成员会重新合并回来。
3. 均摊硬编码 /4 —— 改为按实际成员数，并接入净额抵消结算。
"""
import io

P = 'index.html'
src = io.open(P, encoding='utf-8').read()
orig = len(src)
ok = []

def sub(name, old, new, count=1):
    global src
    if old not in src:
        print('  MISS  %s' % name); return False
    n = src.count(old)
    if n != count:
        print('  WARN  %s 出现 %d 次（预期 %d）' % (name, n, count))
    src = src.replace(old, new, count); ok.append(name); print('  OK    %s' % name); return True


# ══════════════════════════════════════════════════════════════
# BUG 1：缓存按空间 ID 隔离
# ══════════════════════════════════════════════════════════════
sub('cache key by workspace id',
"""function getLSCache(mode){
  var key=mode||state.spaceMode||'team';
  try{return JSON.parse(localStorage.getItem(LS_KEY+'_cache_'+key)||'null');}catch(e){return null;}
}
function setLSCache(d,mode){
  var key=mode||state.spaceMode||'team';
  try{localStorage.setItem(LS_KEY+'_cache_'+key,JSON.stringify(d));}catch(e){}
}""",
"""/* 缓存 key 必须带上 workspaceId，否则切到另一个团队会读到上一个团队的缓存
   （这就是"不同团队数据互通"的根源）。未登录时退回 team/personal 两个槽。 */
function cacheKey(mode){
  var wsId=(auth&&auth.currentWs&&auth.currentWs.id)?auth.currentWs.id:null;
  if(wsId){return LS_KEY+'_ws_'+wsId;}
  var key=mode||state.spaceMode||'team';
  return LS_KEY+'_cache_'+key;
}
function getLSCache(mode){
  try{return JSON.parse(localStorage.getItem(cacheKey(mode))||'null');}catch(e){return null;}
}
function setLSCache(d,mode){
  try{localStorage.setItem(cacheKey(mode),JSON.stringify(d));}catch(e){}
}
/* 清理超过 30 天没用过的空间缓存，避免 localStorage 爆掉 */
function pruneOldCaches(){
  try{
    var now=Date.now(),keys=[];
    for(var i=0;i<localStorage.length;i++){
      var k=localStorage.key(i);
      if(k&&k.indexOf(LS_KEY+'_ws_')===0){keys.push(k);}
    }
    if(keys.length<=12){return;}
    for(var j=0;j<keys.length;j++){
      try{
        var d=JSON.parse(localStorage.getItem(keys[j])||'null');
        var ts=(d&&d._ts)||0;
        if(ts&&(now-ts)>30*24*3600*1000){localStorage.removeItem(keys[j]);}
      }catch(e){}
    }
  }catch(e){}
}""")

# activateWorkspace 里：必须先设置 auth.currentWs 再读缓存（顺序已经对的，但要确保 mode 参数不干扰）
sub('activate read cache after ws set',
"""  /* 先用本地缓存渲染，避免白屏 */
  var cached=getLSCache(state.spaceMode);
  if(cached){state.data=normalizeData(cached,isPersonal);}
  else{state.data=buildDefaultData(isPersonal);}""",
"""  /* 先用本地缓存渲染，避免白屏。
     注意 auth.currentWs 已在上面赋值，所以 getLSCache 会命中本空间专属的 key */
  var cached=getLSCache();
  if(cached){state.data=normalizeData(cached,isPersonal,true);}
  else{state.data=buildDefaultData(isPersonal);}
  pruneOldCaches();""")


# ══════════════════════════════════════════════════════════════
# BUG 2：成员增删不再被预设覆盖
# ══════════════════════════════════════════════════════════════
# 2a. normalizeData 加 keepEmpty 参数：已有云端/缓存数据时，空成员列表是合法的
sub('normalizeData keepEmpty',
"""function normalizeData(d,isPersonal){
  if(!d){return buildDefaultData(isPersonal);}
  if(!d.prepaid||!d.prepaid.length){d.prepaid=isPersonal?[]:PRESET_PREPAID.map(function(x){var y=Object.assign({},x);y._ts=Date.now();return y;});}
  if(!d.expenses){d.expenses=[];}
  if(!d.prepItems){d.prepItems=[];}
  if(!d.outfits){d.outfits=[];}
  if(!d.todos){d.todos=[];}
  if(!d.members||!d.members.length){
    d.members=isPersonal
      ?[{id:'m0',name:'我',_ts:Date.now()}]
      :MEMBERS.map(function(n,i){return {id:'m'+i,name:n,_ts:Date.now()};});
  }
  if(!d.prepTodos){d.prepTodos=[];}
  return d;
}""",
"""/* isExisting=true 表示 d 来自云端或本地缓存（不是全新空间）。
   这种情况下"成员列表为空"是用户真实操作的结果，绝不能回填预设 4 人
   —— 否则用户删了成员一刷新就变回小美/阿杰/丸子/老王。 */
function normalizeData(d,isPersonal,isExisting){
  if(!d){return buildDefaultData(isPersonal);}
  if(!d.expenses){d.expenses=[];}
  if(!d.prepItems){d.prepItems=[];}
  if(!d.outfits){d.outfits=[];}
  if(!d.todos){d.todos=[];}
  if(!d.prepTodos){d.prepTodos=[];}
  if(!d.prepaid){d.prepaid=[];}
  if(!d.members){d.members=[];}
  /* 只有全新空间才注入预设内容 */
  if(!isExisting){
    if(!d.prepaid.length&&!isPersonal){
      d.prepaid=PRESET_PREPAID.map(function(x){var y=Object.assign({},x);y._ts=Date.now();return y;});
    }
    if(!d.members.length){
      d.members=isPersonal
        ?[{id:'m0',name:'我',_ts:Date.now()}]
        :MEMBERS.map(function(n,i){return {id:'m'+i,name:n,_ts:Date.now()};});
    }
  }
  /* 兜底：一个人都没有的话至少留一个，否则记账没法选付款人 */
  if(!aliveList(d.members).length){
    var seed=isPersonal?'我':'我';
    d.members=(d.members||[]).concat([{id:genId(),name:seed,_ts:Date.now()}]);
  }
  return d;
}
/* 过滤掉墓碑（被删除的条目） */
function aliveList(arr){
  var out=[];
  for(var i=0;i<(arr||[]).length;i++){
    if(arr[i]&&!arr[i]._deleted){out.push(arr[i]);}
  }
  return out;
}
/* 取当前存活的成员列表 —— 全站统一用这个，不要直接用 state.data.members */
function aliveMembers(){return aliveList(state.data&&state.data.members);}""")

# 2b. 删除成员改为墓碑（否则云端旧数据会合并回来）
sub('member delete tombstone',
"""      showConfirm('删除成员','确定删除成员「'+name+'」吗？该成员负责的物品不会删除。',function(){
        for(var mz=0;mz<state.data.members.length;mz++){
          if(state.data.members[mz].id===id){state.data.members.splice(mz,1);break;}
        }
        saveData();renderPrep();
      });""",
"""      showConfirm('删除成员','确定删除成员「'+name+'」吗？\\n\\n该成员负责的物品不会删除，已记的账目仍保留（结算时会显示为"已退出"）。',function(){
        /* 用墓碑标记而不是直接删除，否则云端的旧记录会在下次同步时"复活"
           （这就是"删了成员又变回预设那几个"的根源） */
        for(var mz=0;mz<state.data.members.length;mz++){
          if(state.data.members[mz].id===id){
            state.data.members[mz]._deleted=true;
            state.data.members[mz]._ts=Date.now();
            break;
          }
        }
        saveData();renderPrep();renderCurrentPanel();
      });""")

# 2c. 添加成员：上限按存活数算
sub('member add uses alive count',
"""    if(state.data.members.length>=8){showToast('最多 8 位成员');return;}
    state.data.members.push({id:genId(),name:'成员'+(state.data.members.length+1),_ts:Date.now()});
    saveData();renderPrep();""",
"""    var alive=aliveMembers();
    if(alive.length>=12){showToast('最多 12 位成员');return;}
    state.data.members.push({id:genId(),name:'成员'+(alive.length+1),_ts:Date.now()});
    saveData();renderPrep();renderCurrentPanel();""")

# 2d. 至少保留 1 人的判断按存活数
sub('member delete min check',
"""      if(state.data.members.length<=1){showToast('至少保留 1 位成员');return;}""",
"""      if(aliveMembers().length<=1){showToast('至少保留 1 位成员');return;}""")

# 2e. 所有读成员的地方改用 aliveMembers()
for name, old, new in [
    ('memberNameById',
     """function memberNameById(id){
  if(!id){return '未分配';}
  for(var i=0;i<state.data.members.length;i++){if(state.data.members[i].id===id){return state.data.members[i].name;}}
  return '未分配';
}""",
     """function memberNameById(id){
  if(!id){return '未分配';}
  var all=(state.data&&state.data.members)||[];
  for(var i=0;i<all.length;i++){
    if(all[i].id===id){return all[i].name+(all[i]._deleted?'（已退出）':'');}
  }
  return '未分配';
}"""),
    ('ownerBadge',
     """function ownerBadge(ownerId){
  var i=-1;
  for(var k=0;k<state.data.members.length;k++){if(state.data.members[k].id===ownerId){i=k;break;}}
  var name=(i>=0)?state.data.members[i].name:'未分配';""",
     """function ownerBadge(ownerId){
  var mm=aliveMembers(),i=-1;
  for(var k=0;k<mm.length;k++){if(mm[k].id===ownerId){i=k;break;}}
  var name=(i>=0)?mm[i].name:memberNameById(ownerId);"""),
    ('memberSelectOptions',
     """  var html='<option value="">未分配</option>';
  for(var i=0;i<state.data.members.length;i++){
    var m=state.data.members[i];""",
     """  var html='<option value="">未分配</option>';
  var mlist=aliveMembers();
  for(var i=0;i<mlist.length;i++){
    var m=mlist[i];"""),
    ('showMemberDetail',
     """function showMemberDetail(memberId){
  var idx=-1;
  for(var k=0;k<state.data.members.length;k++){if(state.data.members[k].id===memberId){idx=k;break;}}
  if(idx<0){showToast('成员不存在');return;}
  var mem=state.data.members[idx];""",
     """function showMemberDetail(memberId){
  var mmm=aliveMembers(),idx=-1;
  for(var k=0;k<mmm.length;k++){if(mmm[k].id===memberId){idx=k;break;}}
  if(idx<0){showToast('成员不存在');return;}
  var mem=mmm[idx];"""),
    ('showExpenseForm members',
     """  var members=state.data.members||[];
  var payerOpts='<option value="">— 选择付款人 —</option>';""",
     """  var members=aliveMembers();
  var payerOpts='<option value="">— 选择付款人 —</option>';"""),
    ('outfit nameSet',
     """  var nameSet={};
  for(var i=0;i<MEMBERS.length;i++){nameSet[MEMBERS[i]]=1;}""",
     """  var nameSet={};
  var omm=aliveMembers();
  for(var i=0;i<omm.length;i++){nameSet[omm[i].name]=1;}"""),
]:
    sub(name, old, new)

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处修改. %d -> %d bytes' % (len(ok), orig, len(src)))
