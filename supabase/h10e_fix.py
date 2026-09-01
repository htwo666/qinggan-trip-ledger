#!/usr/bin/env python3
# h10e_fix.py — 修复 h10c 留下的多余 }
src = open('index.html', encoding='utf-8').read()

# h10c 删 clearBtn 块时多留了一个 }，导致 renderPrep 提前关闭
old = """  var addBoardBtn=document.getElementById('addBoardBtn');
  if(addBoardBtn){addBoardBtn.onclick=function(){showAddBoardForm();};}
}
  /* 待办完成/删除 */"""
new = """  var addBoardBtn=document.getElementById('addBoardBtn');
  if(addBoardBtn){addBoardBtn.onclick=function(){showAddBoardForm();};}
  /* 待办完成/删除 */"""

c = src.count(old)
print(f'anchor: {c}')
if c == 1:
    src = src.replace(old, new)
    open('index.html', 'w', encoding='utf-8').write(src)
    print(f'OK: {len(src.encode("utf-8"))} bytes')
else:
    print('NOT FOUND')
