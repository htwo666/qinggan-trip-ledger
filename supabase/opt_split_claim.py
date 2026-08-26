#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化 1：不等额分摊 —— 记账时可勾选"这笔谁参与"，只在参与者之间分。
优化 2：成员认领 —— 登录账号可认领某个成员，记账时默认自己付款。
顺手修：4 处硬删除没有墓碑（同步后会复活，和成员那个 bug 同一类）。
"""
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


# ══════════════════════════════════════════════════════════
# A. 硬删除改墓碑（否则同步后复活，和成员 bug 同一类）
# ══════════════════════════════════════════════════════════
sub('todo delete tombstone',
"""        if(state.data.todos[i].id===id){state.data.todos.splice(i,1);break;}""",
"""        if(state.data.todos[i].id===id){state.data.todos[i]._deleted=true;state.data.todos[i]._ts=Date.now();break;}""")

sub('prepItem delete tombstone',
"""            state.data.prepItems.splice(bi,1);break;""",
"""            state.data.prepItems[bi]._deleted=true;state.data.prepItems[bi]._ts=Date.now();break;""")

sub('expense delete tombstone',
"""            state.data.expenses.splice(i,1);break;""",
"""            state.data.expenses[i]._deleted=true;state.data.expenses[i]._ts=Date.now();break;""")

sub('outfit delete tombstone',
"""          if(state.data.outfits[i].id===id){state.data.outfits.splice(i,1);break;}""",
"""          if(state.data.outfits[i].id===id){state.data.outfits[i]._deleted=true;state.data.outfits[i]._ts=Date.now();break;}""")


# ══════════════════════════════════════════════════════════
# B. 成员认领：账号 <-> 成员 绑定
# ══════════════════════════════════════════════════════════
sub('claim helpers',
"""/* 过滤掉墓碑（被删除的条目） */""",
"""/* ---------- 成员认领：把登录账号和团队成员对应起来 ----------
   存在 members[i].uid 字段。认领后记账默认自己付款，结算表里高亮"我"。
   一个账号在一个空间只能认领一个成员，一个成员也只能被一个账号认领。 */
function myUid(){
  return (auth&&auth.session&&auth.session.user&&auth.session.user.id)?auth.session.user.id:'';
}
/* 我认领的成员对象，没认领返回 null */
function myMember(){
  var uid=myUid();
  if(!uid){return null;}
  var ms=aliveMembers();
  for(var i=0;i<ms.length;i++){if(ms[i].uid===uid){return ms[i];}}
  return null;
}
/* 认领某个成员（会先解绑我之前认领的） */
function claimMember(mid,cb){
  var uid=myUid();
  if(!uid){showToast('请先登录再认领');cb&&cb();return;}
  var all=(state.data&&state.data.members)||[];
  var target=null,i;
  for(i=0;i<all.length;i++){if(all[i].id===mid){target=all[i];break;}}
  if(!target){showToast('成员不存在');cb&&cb();return;}
  if(target.uid&&target.uid!==uid){showToast('「'+target.name+'」已被其他人认领');cb&&cb();return;}
  var isCancel=(target.uid===uid);
  /* 先解绑我原来认领的（保证一个账号只占一个成员） */
  for(i=0;i<all.length;i++){
    if(all[i].uid===uid){delete all[i].uid;all[i]._ts=Date.now();}
  }
  if(!isCancel){
    target.uid=uid;
    target._ts=Date.now();
    /* 认领时顺手把成员名字改成我的昵称，除了名字是"成员N"这种默认名才改 */
    var nick=displayName&&displayName();
    if(nick&&/^成员\\d+$/.test(target.name)){target.name=nick;}
  }
  saveData();
  showToast(isCancel?'已取消认领':('已认领为「'+target.name+'」'));
  cb&&cb();
}
/* 过滤掉墓碑（被删除的条目） */""")


# ══════════════════════════════════════════════════════════
# C. 不等额分摊：记账表单加"参与人"勾选
# ══════════════════════════════════════════════════════════
sub('expense form participants',
"""  /* 个人空间默认付款人锁定为"我" */
  var isPersonal=state.spaceMode==='personal';
  var personalPayer=isPersonal&&members.length>0?members[0].id:'';
  var payerDefault=isPersonal?personalPayer:'';""",
"""  /* 个人空间默认付款人锁定为"我" */
  var isPersonal=state.spaceMode==='personal';
  var personalPayer=isPersonal&&members.length>0?members[0].id:'';
  /* 团队空间：如果我认领了成员，付款人默认选我自己 */
  var mine=myMember();
  var payerDefault=isPersonal?personalPayer:(mine?mine.id:'');
  /* 参与人勾选区：默认全选。只有集体AA才用得上 */
  var partHtml='';
  if(!isPersonal&&members.length>1){
    partHtml='<div id="fPartWrap" class="form-row" style="flex-direction:column;align-items:stretch">'+
      '<label style="display:flex;align-items:center;justify-content:space-between">'+
        '<span>参与分摊的人</span>'+
        '<span style="font-weight:400;font-size:0.68rem;color:var(--text-light)">'+
          '<a href="javascript:void(0)" id="fPartAll" style="color:var(--primary)">全选</a> · '+
          '<a href="javascript:void(0)" id="fPartNone" style="color:var(--text-light)">全不选</a>'+
        '</span>'+
      '</label>'+
      '<div class="part-grid">';
    for(var pm=0;pm<members.length;pm++){
      partHtml+='<label class="part-chip"><input type="checkbox" class="fPart" value="'+
        escapeHtml(members[pm].id)+'" checked><span>'+escapeHtml(members[pm].name)+'</span></label>';
    }
    partHtml+='</div>'+
      '<div id="fPartHint" style="font-size:0.68rem;color:var(--text-light);margin-top:4px"></div>'+
      '</div>';
  }""")

sub('expense form insert participants html',
"""    '<div class="form-row"><div style="flex:1"><label>付款人 '+(isPersonal?'':'（集体AA必填，便于结算）')+'</label><select id="fPayer" '+(isPersonal?'disabled':'')+'>'+payerOpts+'</select></div></div>'+
    '<div class="form-row"><div style="flex:1"><label>备注</label><input type="text" id="fNote" placeholder="如：4人午餐"></div></div>'+""",
"""    '<div class="form-row"><div style="flex:1"><label>付款人 '+(isPersonal?'':'（集体AA必填，便于结算）')+'</label><select id="fPayer" '+(isPersonal?'disabled':'')+'>'+payerOpts+'</select></div></div>'+
    partHtml+
    '<div class="form-row"><div style="flex:1"><label>备注</label><input type="text" id="fNote" placeholder="如：3人午餐，老王没吃"></div></div>'+""")

sub('expense form bind participants',
"""  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  if(isPersonal){
    var fp=document.getElementById('fPayer');
    if(fp&&personalPayer){fp.value=personalPayer;}
  }""",
"""  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  var fp=document.getElementById('fPayer');
  if(isPersonal){
    if(fp&&personalPayer){fp.value=personalPayer;}
  }else if(fp&&payerDefault){
    fp.value=payerDefault;   /* 认领过成员的话默认选自己 */
  }
  /* ---- 参与人勾选交互 ---- */
  function getParts(){
    var cbs=document.querySelectorAll('.fPart'),out=[];
    for(var i=0;i<cbs.length;i++){if(cbs[i].checked){out.push(cbs[i].value);}}
    return out;
  }
  function refreshPartHint(){
    var hint=document.getElementById('fPartHint');
    if(!hint){return;}
    var parts=getParts();
    var amt=parseFloat(document.getElementById('fAmount').value)||0;
    var tSel=document.getElementById('fType');
    var isCol=!tSel||tSel.value==='collective';
    if(!isCol){hint.textContent='个人物品由付款人自付，不分摊';return;}
    if(!parts.length){hint.innerHTML='<span style="color:var(--danger)">至少选 1 人参与</span>';return;}
    if(amt>0){
      hint.textContent=parts.length+' 人分摊，每人 '+fmtMoney(amt/parts.length)+
        (parts.length<members.length?('（'+(members.length-parts.length)+' 人不参与）'):'');
    }else{
      hint.textContent=parts.length+' 人参与分摊'+
        (parts.length<members.length?('，'+(members.length-parts.length)+' 人不参与'):'');
    }
  }
  var partCbs=document.querySelectorAll('.fPart');
  for(var pc=0;pc<partCbs.length;pc++){partCbs[pc].onchange=refreshPartHint;}
  var allBtn=document.getElementById('fPartAll');
  if(allBtn){allBtn.onclick=function(){
    var cbs=document.querySelectorAll('.fPart');
    for(var i=0;i<cbs.length;i++){cbs[i].checked=true;}
    refreshPartHint();
  };}
  var noneBtn=document.getElementById('fPartNone');
  if(noneBtn){noneBtn.onclick=function(){
    var cbs=document.querySelectorAll('.fPart');
    for(var i=0;i<cbs.length;i++){cbs[i].checked=false;}
    refreshPartHint();
  };}
  var amtIn=document.getElementById('fAmount');
  if(amtIn){amtIn.oninput=refreshPartHint;}
  var typeSel=document.getElementById('fType');
  var partWrap=document.getElementById('fPartWrap');
  if(typeSel){typeSel.onchange=function(){
    /* 个人物品不需要选参与人 */
    if(partWrap){partWrap.style.display=(this.value==='collective')?'':'none';}
    refreshPartHint();
  };}
  refreshPartHint();""")

sub('expense form save with participants',
"""    var exp={
      id:genId(),
      date:document.getElementById('fDate').value,
      amount:parseFloat(document.getElementById('fAmount').value)||0,
      category:document.getElementById('fCategory').value,
      type:isPersonal?'personal':document.getElementById('fType').value,
      payer:isPersonal?personalPayer:(document.getElementById('fPayer').value||''),
      note:document.getElementById('fNote').value.trim(),
      _ts:Date.now()
    };
    if(!exp.date){showToast('请选择日期');return;}
    if(exp.amount<=0){showToast('请输入有效金额');return;}
    if(exp.type==='collective'&&!exp.payer){showToast('集体AA账目请选择付款人');return;}""",
"""    var exp={
      id:genId(),
      date:document.getElementById('fDate').value,
      amount:parseFloat(document.getElementById('fAmount').value)||0,
      category:document.getElementById('fCategory').value,
      type:isPersonal?'personal':document.getElementById('fType').value,
      payer:isPersonal?personalPayer:(document.getElementById('fPayer').value||''),
      note:document.getElementById('fNote').value.trim(),
      _ts:Date.now()
    };
    if(!exp.date){showToast('请选择日期');return;}
    if(exp.amount<=0){showToast('请输入有效金额');return;}
    if(exp.type==='collective'&&!exp.payer){showToast('集体AA账目请选择付款人');return;}
    /* 集体AA：记下参与人。全员参与时不存 parts 字段，省空间也兼容老数据 */
    if(exp.type==='collective'){
      var parts=getParts();
      if(partCbs.length&&!parts.length){showToast('请至少选 1 人参与分摊');return;}
      if(parts.length&&parts.length<members.length){exp.parts=parts;}
    }""")


# ══════════════════════════════════════════════════════════
# D. 结算算法支持不等额分摊
# ══════════════════════════════════════════════════════════
sub('settlement unequal split',
"""  /* 2. 统计每人应承担金额（集体AA均摊 + 个人物品自付） */
  var owed={};
  for(i=0;i<N;i++){owed[members[i].id]=0;}
  var collectiveTotal=0;
  for(i=0;i<expenses.length;i++){
    var e2=expenses[i];
    var amt2=Number(e2.amount)||0;
    if(e2.type==='collective'){
      collectiveTotal+=amt2;
    }else{
      /* 个人物品：付款人自付，老数据无 payer 则跳过 */
      if(e2.payer&&owed.hasOwnProperty(e2.payer)){
        owed[e2.payer]+=amt2;
      }
    }
  }
  /* 集体AA按人头均摊到每人 */
  var sharePerPerson=collectiveTotal/N;
  for(i=0;i<N;i++){owed[members[i].id]+=sharePerPerson;}""",
"""  /* 2. 统计每人应承担金额（集体AA按参与人分摊 + 个人物品自付） */
  var owed={};
  for(i=0;i<N;i++){owed[members[i].id]=0;}
  var collectiveTotal=0,hasUnequal=false;
  for(i=0;i<expenses.length;i++){
    var e2=expenses[i];
    var amt2=Number(e2.amount)||0;
    if(e2.type==='collective'){
      collectiveTotal+=amt2;
      /* parts 为空 = 全员参与（兼容老数据）；有 parts = 只在这些人之间分 */
      var pl=[],j;
      if(e2.parts&&e2.parts.length){
        for(j=0;j<e2.parts.length;j++){
          if(owed.hasOwnProperty(e2.parts[j])){pl.push(e2.parts[j]);}
        }
        if(pl.length&&pl.length<N){hasUnequal=true;}
      }
      /* 参与人都被删了的话退回全员分摊，避免这笔钱没人承担 */
      if(!pl.length){for(j=0;j<N;j++){pl.push(members[j].id);}}
      var each=amt2/pl.length;
      for(j=0;j<pl.length;j++){owed[pl[j]]+=each;}
    }else{
      /* 个人物品：付款人自付，老数据无 payer 则跳过 */
      if(e2.payer&&owed.hasOwnProperty(e2.payer)){
        owed[e2.payer]+=amt2;
      }
    }
  }""")

# 结算表里高亮"我"，并提示有不等额分摊
sub('settlement highlight me',
"""  for(i=0;i<N;i++){
    var m=members[i];
    var n=net[m.id];
    var netCls=n>0?'income':'expense';
    var netLabel=n>0?'应收':(n<0?'应付':'已平衡');
    settleHtml+='<tr><td>'+escapeHtml(m.name)+'</td><td>'+fmtMoney(paid[m.id])+'</td><td>'+fmtMoney(owed[m.id])+'</td><td class="'+netCls+'"><strong>'+fmtMoney(Math.abs(n))+'</strong> <span style="font-size:0.68rem;color:var(--text-light)">'+netLabel+'</span></td></tr>';
  }""",
"""  var meId=(myMember()||{}).id;
  for(i=0;i<N;i++){
    var m=members[i];
    var n=net[m.id];
    var netCls=n>0?'income':'expense';
    var netLabel=n>0?'应收':(n<0?'应付':'已平衡');
    var isMe=(meId&&m.id===meId);
    settleHtml+='<tr'+(isMe?' style="background:var(--primary-bg)"':'')+'><td>'+escapeHtml(m.name)+
      (isMe?' <span style="font-size:0.62rem;color:var(--primary);font-weight:600">我</span>':'')+
      '</td><td>'+fmtMoney(paid[m.id])+'</td><td>'+fmtMoney(owed[m.id])+'</td><td class="'+netCls+'"><strong>'+fmtMoney(Math.abs(n))+'</strong> <span style="font-size:0.68rem;color:var(--text-light)">'+netLabel+'</span></td></tr>';
  }""")

sub('settlement unequal notice',
"""  settleHtml+='<div class="table-wrap"><table><thead><tr><th>成员</th><th>实付</th><th>应承担</th><th>净额</th></tr></thead><tbody>';""",
"""  if(hasUnequal){
    settleHtml+='<div style="font-size:0.72rem;color:var(--primary-dark);background:var(--primary-bg);padding:8px 10px;border-radius:8px;margin-bottom:10px;">✓ 已按每笔账的实际参与人分摊（有账目不是全员参与）</div>';
  }
  settleHtml+='<div class="table-wrap"><table><thead><tr><th>成员</th><th>实付</th><th>应承担</th><th>净额</th></tr></thead><tbody>';""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处修改. %d -> %d bytes'%(len(ok),orig,len(src)))
