#!/usr/bin/env python3
from pathlib import Path

p = Path('combined/src/main/java/it/darkroom/timer/EnlargementActivity.java')
if not p.exists():
    raise SystemExit('v0.2.0 legacy recipe: EnlargementActivity missing')
s = p.read_text(encoding='utf-8')

old = '            ExposureRecipe oldR=ExposureRecipe.decode(sourceRecipe());\n            ExposureRecipe newR=scaleRecipe(oldR,oldBase,factor);'
new = '            ExposureRecipe oldR=sourceRecipeForResize(oldBase);\n            ExposureRecipe newR=scaleRecipe(oldR,oldBase,factor);'
if old not in s:
    raise SystemExit('v0.2.0 legacy recipe: resize recipe marker missing')
s = s.replace(old, new, 1)

marker = '    ExposureRecipe scaleRecipe(ExposureRecipe r,int oldBase,double factor){'
if marker not in s:
    raise SystemExit('v0.2.0 legacy recipe: scaleRecipe marker missing')
helper = r'''    ExposureRecipe sourceRecipeForResize(int base){
        ExposureRecipe r=ExposureRecipe.decode(sourceRecipe());
        if(r.hasBase())return r;
        r.originalBaseMs=base;
        r.operationalBaseMs=base;
        r.baseChosenAt=System.currentTimeMillis();
        if(originEntry!=null){
            String ft=ExposureRecipe.normalizeFilter(originEntry.testBaseFilterType);
            int fv=ExposureRecipe.snap5(originEntry.testBaseFilterValue);
            if(!ExposureRecipe.FILTER_NONE.equals(ft)){
                r.filterType=ft;r.filterValue=fv;
            }else{
                int m=parseFilterNumber(originEntry.magenta),y=parseFilterNumber(originEntry.yellow);
                // Old manual cards can contain both Y and M. ExposureRecipe can
                // represent one base contrast filter only, so never guess when both
                // are non-zero: preserve the card values in LOG and leave base filter NONE.
                if(m>0&&y<=0){r.filterType=ExposureRecipe.FILTER_MAGENTA;r.filterValue=ExposureRecipe.snap5(m);}
                else if(y>0&&m<=0){r.filterType=ExposureRecipe.FILTER_YELLOW;r.filterValue=ExposureRecipe.snap5(y);}
            }
            int dq=parseDensityQuarterSteps(originEntry.density);
            if(dq>=0)r.densityQuarterSteps=dq;
        }
        return r;
    }

    int parseFilterNumber(String value){
        if(value==null)return 0;
        try{return (int)Math.round(Double.parseDouble(value.trim().replace(',','.')));}catch(Exception e){return 0;}
    }

    int parseDensityQuarterSteps(String value){
        if(value==null||value.trim().isEmpty())return -1;
        String v=value.trim().toUpperCase(Locale.ITALY).replace("D","").replace(',','.');
        try{
            double density=Double.parseDouble(v);
            if(density<=8 && !value.toUpperCase(Locale.ITALY).contains("D")) return ExposureRecipe.clampDensity((int)Math.round(density));
            return ExposureRecipe.clampDensity((int)Math.round(density/7.5));
        }catch(Exception e){return -1;}
    }

'''
s = s.replace(marker, helper + marker, 1)

# For a resize launched from the active plan rather than a LOG entry, make the
# derived LOG card reflect the preserved recipe filter/density as well.
old_active = '            d.title="Stampa ridimensionata";d.negative=x.is35?"35mm":"6x6";d.exposureMethod=TimingMath.normalizeMethod(p.getString("timingMethod",TimingMath.METHOD_SECONDS));d.exposureStep=TimingMath.stepLabel(d.exposureMethod);d.testBaseFilterType=ExposureRecipe.normalizeFilter(x.newRecipe.filterType);d.testBaseFilterValue=ExposureRecipe.snap5(x.newRecipe.filterValue);'
new_active = '            d.title="Stampa ridimensionata";d.negative=x.is35?"35mm":"6x6";d.paper="Fomaspeed Variant 311 RC lucida";d.exposureMethod=TimingMath.normalizeMethod(p.getString("timingMethod",TimingMath.METHOD_SECONDS));d.exposureStep=TimingMath.stepLabel(d.exposureMethod);d.testBaseFilterType=ExposureRecipe.normalizeFilter(x.newRecipe.filterType);d.testBaseFilterValue=ExposureRecipe.snap5(x.newRecipe.filterValue);if(ExposureRecipe.FILTER_MAGENTA.equals(x.newRecipe.filterType))d.magenta=String.valueOf(x.newRecipe.filterValue);if(ExposureRecipe.FILTER_YELLOW.equals(x.newRecipe.filterType))d.yellow=String.valueOf(x.newRecipe.filterValue);d.density=x.newRecipe.densityLabel();'
if old_active not in s:
    raise SystemExit('v0.2.0 legacy recipe: active derived LOG marker missing')
s = s.replace(old_active, new_active, 1)

p.write_text(s, encoding='utf-8')

out = p.read_text(encoding='utf-8')
for guard in ['sourceRecipeForResize(oldBase)', 'parseFilterNumber(originEntry.magenta)', 'parseDensityQuarterSteps(originEntry.density)', 'if(m>0&&y<=0)']:
    if guard not in out:
        raise SystemExit('v0.2.0 legacy recipe guard failed: ' + guard)
print('Darkroom v0.2.0 legacy recipe compatibility patch ready')
