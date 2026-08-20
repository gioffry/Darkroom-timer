from pathlib import Path
p=Path('combined/src/main/java/it/darkroom/timer/MainActivity.java')
s=p.read_text(encoding='utf-8')
start=s.index('    private void showSettingsDialog() {')
end=s.index('\n    private ', start+10)
seg=s[start:end]
old='        dialog.setContentView(panel);'
if old not in seg:
    raise SystemExit('settings dialog content marker missing')
new='''        ScrollView settingsScroll = new ScrollView(this);
        settingsScroll.setFillViewport(true);
        settingsScroll.addView(panel, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        dialog.setContentView(settingsScroll);'''
seg=seg.replace(old,new,1)
s=s[:start]+seg+s[end:]
p.write_text(s,encoding='utf-8')
print('settings scroll fix applied')
