#!/usr/bin/env python3
# h9_migration_safe.py — 让老数据迁移保留"已购+负责人"进度
import sys
src = open('index.html', encoding='utf-8').read()

old = """      _pi.cat=_pcByName[_cname];
      if(!_pi.readyBy){_pi.readyBy={};}
    }
  }
  if(!d.outfits){d.outfits=[];}"""

new = """      _pi.cat=_pcByName[_cname];
      if(!_pi.readyBy){_pi.readyBy={};}
      /* 老数据保留"已购"进度：如果旧 owner 已标记 bought=true，
         把 readyBy[owner] 置为 true，这样老用户的"谁备好了"不会丢。
         只在 readyBy 还没有这个成员的记录时才补，不覆盖新数据。 */
      if(_pi.bought&&_pi.owner&&!_pi.readyBy[_pi.owner]){
        _pi.readyBy[_pi.owner]=true;
      }
    }
  }
  if(!d.outfits){d.outfits=[];}"""

if src.count(old) != 1:
    print(f'!! migration block ({src.count(old)})')
    sys.exit(1)
src = src.replace(old, new)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
