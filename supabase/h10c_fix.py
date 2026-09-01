#!/usr/bin/env python3
# h10c_fix.py — 修复 renderPrep 里 clearPrepSampleBtn 的删除（shell 转义坑了）
src = open('index.html', encoding='utf-8').read()

# 删除 toolbar 里的清空按钮
old1 = '<button class="btn btn-outline btn-sm" id="clearPrepSampleBtn">清空数据</button></div>\';'
new1 = "</div>';"
c1 = src.count(old1)
print(f'toolbar btn count: {c1}')
if c1 == 1:
    src = src.replace(old1, new1)

# 删除 clearBtn 的 onclick 绑定块
old2 = """  var clearBtn=document.getElementById('clearPrepSampleBtn');
  if(clearBtn){clearBtn.onclick=function(){
    showConfirm('清空准备数据','将删除全部计划与物品记录，此操作不可撤销。确定继续吗？',function(){
      state.data.prepItems=[];state.data.prepCategories=[];state.data.todos=[];saveData();renderPrep();showToast('已清空');
    });
  };"""
new2 = ""
c2 = src.count(old2)
print(f'handler block count: {c2}')
if c2 == 1:
    src = src.replace(old2, new2)
else:
    # 可能前面已经删了一部分，用更短的 anchor
    old2b = "  var clearBtn=document.getElementById('clearPrepSampleBtn');"
    c2b = src.count(old2b)
    print(f'  short anchor count: {c2b}')
    if c2b == 1:
        # 找到这一行开始到下一个 ; 闭合
        idx = src.index(old2b)
        # 找到这个块的结束：第一个 "  }\n" 后面的 "}\n"
        end_marker = "    });\n  }\n"
        end_idx = src.index(end_marker, idx)
        block = src[idx:end_idx + len(end_marker)]
        print(f'  block to remove ({len(block)} chars):')
        print(block)
        src = src[:idx] + src[end_idx + len(end_marker):]

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
