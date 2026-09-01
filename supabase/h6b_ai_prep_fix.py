#!/usr/bin/env python3
# h6b_ai_prep_fix.py — 修复 confirmAIPrep 和 prompt 例子
import sys
src = open('index.html', encoding='utf-8').read()

# 1) 重写 confirmAIPrep
old_cap = """function confirmAIPrep(o){
  var cats=['服饰装备','个护美妆','药品保健','证件','食品','其他'];
  var cat=o.category||'其他',okc=false,i;
  for(i=0;i<cats.length;i++){if(cats[i]===cat){okc=true;break;}}
  if(!okc){cat='其他';}
  var price=Number(o.price)||0;
  var owner=resolveMemberId(o.owner);
  var body='物品：'+o.name+'\\n'+
    '分类：'+cat+'\\n'+
    (price>0?('预估价：'+fmtMoney(price)+'\\n'):'')+
    '购买渠道：'+(o.channel||'待定')+'\\n'+
    '负责人：'+(owner?memberNameById(owner):'未指定')+'\\n'+
    '\\n加到必买清单吗？';
  showConfirm('AI 帮你加进必买清单',body,function(){
    state.data.prepItems.push({
      id:genId(),category:cat,name:String(o.name).trim(),
      price:price,channel:o.channel||'待定',owner:owner,
      bought:false,overdue:false,_ts:Date.now()
    });
    saveData();showToast('已加入必买清单');renderAll();
  });
}"""

NEW_CAP = """function confirmAIPrep(o){
  /* AI 加物品：自动找/建对应分类板块，新模型不要价格/渠道/负责人 */
  var catName=o.category||'其他';
  var catId=prepCatId(catName);
  var body='物品：'+o.name+'\\n'+
    '板块：'+escapeHtml(prepCatName(catId))+'\\n'+
    '\\n加到必买清单吗？';
  showConfirm('AI 帮你加进必买清单',body,function(){
    state.data.prepItems.push({
      id:genId(),cat:catId,name:String(o.name).trim(),
      readyBy:{},_ts:Date.now()
    });
    saveData();showToast('已加入必买清单');renderAll();
  });
}"""

if src.count(old_cap) != 1:
    print(f'!! confirmAIPrep ({src.count(old_cap)})')
    sys.exit(1)
src = src.replace(old_cap, NEW_CAP)

# 2) 更新 prompt 例子里的 prep 行
old_ex = '@@ADD{"kind":"prep","name":"登山杖","category":"服饰装备","price":80,"channel":"淘宝","owner":"小美"}'
new_ex = '@@ADD{"kind":"prep","name":"登山杖","category":"服饰装备"}'
if src.count(old_ex) != 1:
    print(f'!! prompt prep example ({src.count(old_ex)})')
    sys.exit(1)
src = src.replace(old_ex, new_ex)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
