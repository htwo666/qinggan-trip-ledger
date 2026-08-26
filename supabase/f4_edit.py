#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""顺手优化：花费可编辑（原来只能删了重记）"""
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

# 1. 函数签名接收 item
sub('form signature',
"""function showExpenseForm(){
  var today=todayStr();""",
"""function showExpenseForm(item){
  var editing=!!item;
  var today=todayStr();""")

# 2. 默认值取自 item
sub('form defaults from item',
"""  var mine=myMember();
  var payerDefault=isPersonal?personalPayer:(mine?mine.id:'');""",
"""  var mine=myMember();
  var payerDefault=isPersonal?personalPayer:(mine?mine.id:'');
  /* 编辑模式：各字段回填原值 */
  if(editing){payerDefault=item.payer||'';}
  var vDate=editing?(item.date||today):today;
  var vAmount=editing?(item.amount||''):'';
  var vCat=editing?(item.category||''):'';
  var vType=editing?(item.type||'collective'):'collective';
  var vNote=editing?(item.note||''):'';""")

# 3. 分类下拉：编辑时选中原分类
sub('category selected',
"""  for(var i=0;i<EXPENSE_CATEGORIES.length;i++){catOpts+='<option>'+EXPENSE_CATEGORIES[i]+'</option>';}""",
"""  for(var i=0;i<EXPENSE_CATEGORIES.length;i++){
    var cn=EXPENSE_CATEGORIES[i];
    catOpts+='<option'+((item&&item.category===cn)?' selected':'')+'>'+cn+'</option>';
  }""")

# 4. 付款人下拉：编辑时选中原付款人
sub('payer selected',
"""    payerOpts+='<option value="'+escapeHtml(members[m].id)+'">'+escapeHtml(members[m].name)+'</option>';""",
"""    payerOpts+='<option value="'+escapeHtml(members[m].id)+'"'+
      ((item&&item.payer===members[m].id)?' selected':'')+'>'+escapeHtml(members[m].name)+'</option>';""")

# 5. 参与人勾选：编辑时按原 parts 勾
sub('parts checked from item',
"""      partHtml+='<label class="part-chip"><input type="checkbox" class="fPart" value="'+
        escapeHtml(members[pm].id)+'" checked><span>'+escapeHtml(members[pm].name)+'</span></label>';""",
"""      /* 编辑模式：原来有 parts 就按它勾，没有 parts 说明是全员，全勾上 */
      var pchk=true;
      if(editing&&item.parts&&item.parts.length){
        pchk=false;
        for(var pk=0;pk<item.parts.length;pk++){
          if(item.parts[pk]===members[pm].id){pchk=true;break;}
        }
      }
      partHtml+='<label class="part-chip'+(pchk?' on':'')+'"><input type="checkbox" class="fPart" value="'+
        escapeHtml(members[pm].id)+'"'+(pchk?' checked':'')+'><span>'+escapeHtml(members[pm].name)+'</span></label>';""")

# 6. 保存：编辑就改原对象，不新建
sub('save edit or create',
"""  document.getElementById('saveExpBtn').onclick=function(){
    var exp={
      id:genId(),
      date:document.getElementById('fDate').value,""",
"""  document.getElementById('saveExpBtn').onclick=function(){
    var exp={
      id:editing?item.id:genId(),
      date:document.getElementById('fDate').value,""")

sub('save write back',
"""    state.data.expenses.push(exp);saveData();
    document.getElementById('formModal').classList.remove('show');
    renderExpense();showToast('已记录');""",
"""    if(editing){
      /* 改原对象：先清掉可能残留的 parts，再按本次选择写 */
      var arr=state.data.expenses||[],found=false;
      for(var ei=0;ei<arr.length;ei++){
        if(arr[ei].id===exp.id){
          delete arr[ei].parts;
          for(var kk in exp){if(exp.hasOwnProperty(kk)){arr[ei][kk]=exp[kk];}}
          found=true;break;
        }
      }
      if(!found){state.data.expenses.push(exp);}
    }else{
      state.data.expenses.push(exp);
    }
    saveData();
    document.getElementById('formModal').classList.remove('show');
    renderExpense();showToast(editing?'已修改':'已记录');""")

# 7. 标题区分
sub('form title',
"""  sheet.innerHTML='<div class="form-modal-title">记一笔（'+(isPersonal?'个人空间':'途中花费')+'）<button id="closeForm">✕</button></div>'+""",
"""  sheet.innerHTML='<div class="form-modal-title">'+(editing?'修改这笔':'记一笔')+'（'+(isPersonal?'个人空间':'途中花费')+'）<button id="closeForm">✕</button></div>'+""")

# 8. 表单里的日期/金额/备注默认值改成变量
sub('date value',"""value="'+today+'" ""","""value="'+vDate+'" """)

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
