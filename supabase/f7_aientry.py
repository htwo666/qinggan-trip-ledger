#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 入口优化：把 AI 放到用户真正需要它的地方
 1. 记账页：「花费体检」按钮 —— AI 看真实数据给省钱建议
 2. 汇总页：「AI 解读账单」
 3. 预算超支时：提示条里直接给个「问问 AI 怎么省」
 4. AI 输入框 placeholder 提示可以直接说话记账
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

# 1. 通用：打开 AI 并自动发一个问题
sub('askAI helper',
"""/* ---------- AI 自然语言记账 ----------""",
"""/* 打开 AI 面板并自动问一个问题（各页面的 AI 快捷入口都走这个） */
function askAI(question){
  openAIPanel();
  setTimeout(function(){sendAIMessage(question);},350);
}

/* ---------- AI 自然语言记账 ----------""")

# 2. 记账页工具栏加「花费体检」
sub('expense page AI button',
"""'</button><button class="btn btn-outline btn-sm" id="exportCsvBtn">'+svgIcon('download')+'导出CSV</button></div>';""",
"""'</button><button class="btn btn-outline btn-sm" id="aiCheckBtn">✨ 花费体检</button><button class="btn btn-outline btn-sm" id="exportCsvBtn">'+svgIcon('download')+'导出CSV</button></div>';""")

sub('bind expense AI button',
"""  var csvBtn=document.getElementById('exportCsvBtn');""",
"""  var acb=document.getElementById('aiCheckBtn');
  if(acb){acb.onclick=function(){
    askAI('帮我看看这个账本，我们花钱有啥问题吗？哪些地方能省？给几条具体的建议，别说空话。');
  };}
  var csvBtn=document.getElementById('exportCsvBtn');""")

# 3. 汇总页加「AI 解读账单」
sub('summary page AI button',
"""  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="exportImgBtn">'+svgIcon('download')+'导出图片发群</button>""",
"""  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="exportImgBtn">'+svgIcon('download')+'导出图片发群</button><button class="btn btn-outline btn-sm" id="aiReadBtn">✨ AI 解读账单</button>""")

sub('bind summary AI button',
"""  var imgb=document.getElementById('exportImgBtn');
  if(imgb){imgb.onclick=exportSettleImage;}""",
"""  var imgb=document.getElementById('exportImgBtn');
  if(imgb){imgb.onclick=exportSettleImage;}
  var arb=document.getElementById('aiReadBtn');
  if(arb){arb.onclick=function(){
    askAI('用大白话解读一下我们这次的账单：钱主要花在哪、有没有异常的花销、和一般青甘环线的花费比算多还是少、结算清单看着合理吗。');
  };}""")

# 4. 超支提示条里加「问 AI 怎么省」
sub('budget alert AI link',
"""    '<a href="javascript:void(0)" id="editBudgetLink" style="color:'+fg+
    ';font-size:0.68rem;text-decoration:underline;flex-shrink:0;opacity:.75">改预算</a></div>';""",
"""    (a.level==='over'
      ?'<a href="javascript:void(0)" id="askSaveLink" style="color:'+fg+
        ';font-size:0.68rem;text-decoration:underline;flex-shrink:0;font-weight:600">问AI咋省</a>'
      :'')+
    '<a href="javascript:void(0)" id="editBudgetLink" style="color:'+fg+
    ';font-size:0.68rem;text-decoration:underline;flex-shrink:0;opacity:.75">改预算</a></div>';""")

sub('bind budget alert AI link',
"""  var ebl=document.getElementById('editBudgetLink');
  if(ebl){ebl.onclick=editBudget;}""",
"""  var ebl=document.getElementById('editBudgetLink');
  if(ebl){ebl.onclick=editBudget;}
  var asl=document.getElementById('askSaveLink');
  if(asl){asl.onclick=function(){
    askAI('我们今天超预算了，看看账本里今天都花哪了，接下来几天怎么省着点？给点实际的招。');
  };}""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
