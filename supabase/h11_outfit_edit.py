#!/usr/bin/env python3
# h11_outfit_edit.py — 穿搭记录加修改按钮
# 1. CSS: 加 .o-edit 样式
# 2. renderOutfit: 每条穿搭行加修改按钮
# 3. renderOutfit: 加修改按钮事件绑定
# 4. showOutfitForm: 改成支持编辑（传 editId 时回填+更新，不传时新建）

src = open('index.html', encoding='utf-8').read()

# ---- 1. CSS: 在 .o-del:hover 后面加 .o-edit 样式 ----
css_old = ".outfit-row .o-del:hover{opacity:1;color:var(--danger);}\n.outfit-row .o-del svg{width:13px;height:13px;}"
css_new = (
    ".outfit-row .o-del:hover{opacity:1;color:var(--danger);}\n"
    ".outfit-row .o-del svg{width:13px;height:13px;}\n"
    ".outfit-row .o-edit{border:none;background:transparent;color:var(--text-light);cursor:pointer;padding:0 2px;flex-shrink:0;display:flex;align-items:center;opacity:0.5;}\n"
    ".outfit-row .o-edit:hover{opacity:1;color:var(--primary);}\n"
    ".outfit-row .o-edit svg{width:13px;height:13px;}"
)
c1 = src.count(css_old)
print(f'css anchor: {c1}')
if c1 != 1:
    print('!! css anchor not unique'); exit(1)
src = src.replace(css_old, css_new)

# ---- 2. renderOutfit: 每条穿搭行加修改按钮 ----
row_old = """listHtml+='<div class="outfit-row"><span class="o-person">'+escapeHtml(o.person||'未署名')+'</span><span class="o-desc">'+escapeHtml(o.desc||'')+'</span><button class="o-del" data-action="delOutfit" data-id="'+o.id+'" title="删除">'+svgIcon('trash')+'</button></div>';"""
row_new = """listHtml+='<div class="outfit-row"><span class="o-person">'+escapeHtml(o.person||'未署名')+'</span><span class="o-desc">'+escapeHtml(o.desc||'')+'</span><button class="o-edit" data-action="editOutfit" data-id="'+o.id+'" title="修改">'+svgIcon('edit')+'</button><button class="o-del" data-action="delOutfit" data-id="'+o.id+'" title="删除">'+svgIcon('trash')+'</button></div>';"""
c2 = src.count(row_old)
print(f'row anchor: {c2}')
if c2 != 1:
    print('!! row anchor not unique'); exit(1)
src = src.replace(row_old, row_new)

# ---- 3. renderOutfit: 加修改按钮事件绑定（在 delBtns 绑定之前插入）----
handler_old = """  var delBtns=p.querySelectorAll('[data-action="delOutfit"]');"""
handler_new = """  var editBtns=p.querySelectorAll('[data-action="editOutfit"]');
  for(var eb=0;eb<editBtns.length;eb++){
    editBtns[eb].onclick=function(){
      var id=this.getAttribute('data-id');
      showOutfitForm(id);
    };
  }
  var delBtns=p.querySelectorAll('[data-action="delOutfit"]');"""
c3 = src.count(handler_old)
print(f'handler anchor: {c3}')
if c3 != 1:
    print('!! handler anchor not unique'); exit(1)
src = src.replace(handler_old, handler_new)

# ---- 4. showOutfitForm: 支持编辑模式 ----
form_old = """function showOutfitForm(){
  var today=todayStr();
  /* 从已有记录中提取用过的名字，生成 datalist 建议 */
  var nameSet={};
  var omm=aliveMembers();
  for(var i=0;i<omm.length;i++){nameSet[omm[i].name]=1;}
  for(var j=0;j<state.data.outfits.length;j++){
    if(state.data.outfits[j].person){nameSet[state.data.outfits[j].person]=1;}
  }
  var nameOpts='';
  for(var nk in nameSet){
    if(nameSet.hasOwnProperty(nk)&&nk){nameOpts+='<option value="'+escapeHtml(nk)+'">';}
  }
  var sheet=document.getElementById('formModalSheet');
  sheet.innerHTML='<div class="form-modal-title">记录穿搭<button id="closeForm">✕</button></div>'+
    '<div class="form-row"><div><label>日期</label><input type="date" id="fDate" value="'+today+'"></div>'+
    '<div><label>人物姓名（可自由输入）</label><input type="text" id="fPerson" list="personNameList" placeholder="输入姓名，如：小美"><datalist id="personNameList">'+nameOpts+'</datalist></div></div>'+
    '<div class="form-row"><div style="flex:1"><label>穿搭描述</label><textarea id="fDesc" placeholder="如：冲锋衣+抓绒+长裤，高原防晒帽"></textarea></div></div>'+
    '<button class="btn btn-primary btn-block" style="margin-top:12px" id="saveOutfitBtn">保存</button>';
  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  document.getElementById('saveOutfitBtn').onclick=function(){
    var o={
      id:genId(),
      date:document.getElementById('fDate').value,
      person:document.getElementById('fPerson').value.trim()||'未署名',
      desc:document.getElementById('fDesc').value.trim(),
      _ts:Date.now()
    };
    if(!o.date){showToast('请选择日期');return;}
    if(!o.desc){showToast('请填写描述');return;}
    state.data.outfits.push(o);saveData();
    document.getElementById('formModal').classList.remove('show');
    renderOutfit();showToast('已记录');
  };
}"""

form_new = """function showOutfitForm(editId){
  var today=todayStr();
  /* 编辑模式：找到对应记录 */
  var editing=false,editRec=null;
  if(editId){
    for(var ei=0;ei<state.data.outfits.length;ei++){
      if(state.data.outfits[ei].id===editId&&!state.data.outfits[ei]._deleted){
        editing=true;editRec=state.data.outfits[ei];break;
      }
    }
  }
  /* 从已有记录中提取用过的名字，生成 datalist 建议 */
  var nameSet={};
  var omm=aliveMembers();
  for(var i=0;i<omm.length;i++){nameSet[omm[i].name]=1;}
  for(var j=0;j<state.data.outfits.length;j++){
    if(state.data.outfits[j].person){nameSet[state.data.outfits[j].person]=1;}
  }
  var nameOpts='';
  for(var nk in nameSet){
    if(nameSet.hasOwnProperty(nk)&&nk){nameOpts+='<option value="'+escapeHtml(nk)+'">';}
  }
  var sheet=document.getElementById('formModalSheet');
  var initDate=editing?editRec.date:today;
  var initPerson=editing?(editRec.person||''):'';
  var initDesc=editing?(editRec.desc||''):'';
  sheet.innerHTML='<div class="form-modal-title">'+(editing?'修改穿搭':'记录穿搭')+'<button id="closeForm">✕</button></div>'+
    '<div class="form-row"><div><label>日期</label><input type="date" id="fDate" value="'+initDate+'"></div>'+
    '<div><label>人物姓名（可自由输入）</label><input type="text" id="fPerson" list="personNameList" placeholder="输入姓名，如：小美" value="'+escapeHtml(initPerson)+'"><datalist id="personNameList">'+nameOpts+'</datalist></div></div>'+
    '<div class="form-row"><div style="flex:1"><label>穿搭描述</label><textarea id="fDesc" placeholder="如：冲锋衣+抓绒+长裤，高原防晒帽">'+escapeHtml(initDesc)+'</textarea></div></div>'+
    '<button class="btn btn-primary btn-block" style="margin-top:12px" id="saveOutfitBtn">'+(editing?'保存修改':'保存')+'</button>';
  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  document.getElementById('saveOutfitBtn').onclick=function(){
    var vDate=document.getElementById('fDate').value;
    var vPerson=document.getElementById('fPerson').value.trim()||'未署名';
    var vDesc=document.getElementById('fDesc').value.trim();
    if(!vDate){showToast('请选择日期');return;}
    if(!vDesc){showToast('请填写描述');return;}
    if(editing){
      editRec.date=vDate;
      editRec.person=vPerson;
      editRec.desc=vDesc;
      editRec._ts=Date.now();
    }else{
      state.data.outfits.push({id:genId(),date:vDate,person:vPerson,desc:vDesc,_ts:Date.now()});
    }
    saveData();
    document.getElementById('formModal').classList.remove('show');
    renderOutfit();showToast(editing?'已更新':'已记录');
  };
}"""

c4 = src.count(form_old)
print(f'form anchor: {c4}')
if c4 != 1:
    print('!! form anchor not unique'); exit(1)
src = src.replace(form_old, form_new)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
