from pathlib import Path
p=Path('combined/build_v011.sh')
s=p.read_text(encoding='utf-8')
s=s.replace("@Override\\\\n    protected void onCreate", "@Override\\n    protected void onCreate")
s=s.replace("s.index('\\\\n    @Override'", "s.index('\\n    @Override'")
p.write_text(s, encoding='utf-8')
print('build_v011 newline fix applied')
