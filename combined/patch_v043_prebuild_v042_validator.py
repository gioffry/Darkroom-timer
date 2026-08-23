#!/usr/bin/env python3
from pathlib import Path

# v0.4.3 is based on the verified v0.4.2 content.  The repository copy of the
# v0.4.2 validator still counts FAQ entries by indentation, while historical
# arrays such as Q_COLOR3 contain several Java strings on the same source line.
# Normalize only the inherited build-time validators before executing v0.4.2.

p = Path('combined/patch_v042_technique_faqs.py')
s = p.read_text(encoding='utf-8')
old = '''def count_entries(text, qname, next_name):
    a=text.index('private static final String[] '+qname)
    b=text.index('private static final String[] '+next_name, a)
    return text[a:b].count('            "')
'''
new = '''def count_entries(text, qname, next_name):
    import re
    a=text.index('private static final String[] '+qname)
    b=text.index('private static final String[] '+next_name, a)
    block=text[a:b]
    return len(re.findall(r'"(?:\\\\.|[^"\\\\])*"', block))
'''
if old not in s:
    raise SystemExit('v0.4.3 prebuild: v0.4.2 patch validator marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

b = Path('combined/build_v042.sh')
bs = b.read_text(encoding='utf-8')
old2 = '''def count(a,b):
    x=s.index('private static final String[] '+a)
    y=s.index('private static final String[] '+b,x)
    return s[x:y].count('            "')
'''
new2 = '''def count(a,b):
    import re
    x=s.index('private static final String[] '+a)
    y=s.index('private static final String[] '+b,x)
    return len(re.findall(r'"(?:\\\\.|[^"\\\\])*"', s[x:y]))
'''
if old2 not in bs:
    raise SystemExit('v0.4.3 prebuild: v0.4.2 shell validator marker missing')
bs = bs.replace(old2, new2, 1)
b.write_text(bs, encoding='utf-8')

print('v0.4.3 inherited v0.4.2 FAQ validators normalized')
