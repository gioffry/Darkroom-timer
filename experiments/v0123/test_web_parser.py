#!/usr/bin/env python3
from pathlib import Path
import subprocess, tempfile

here=Path(__file__).parent
parser=here/'src/it/darkroom/timer/assistant/search/WebSearchParser.java'
with tempfile.TemporaryDirectory() as d:
    d=Path(d)
    dst=d/'it/darkroom/timer/assistant/search'; dst.mkdir(parents=True)
    (dst/'WebSearchParser.java').write_text(parser.read_text())
    test=d/'TestWeb.java'
    test.write_text(r'''
import java.util.*;
import it.darkroom.timer.assistant.search.WebSearchParser;
public class TestWeb {
  public static void main(String[] args) throws Exception {
    String html="<div class=\"result\"><a class=\"result__a\" href=\"https://www.analogica.it/bellini-hydrofen-t15999.html\">Bellini Hydrofen forum</a><a class=\"result__snippet\">Discussione Hydrofen 1 + 39</a></div>"+
      "<div class=\"result\"><a class=\"result__a\" href=\"https://www.bellinifoto.it/prodotto/hydrofen-sviluppo-pellicola-concentrato-dil-115-131/\">HYDROFEN Sviluppo Pellicola - Bellini Foto</a><a class=\"result__snippet\">Sviluppo pellicola. Diluizione 1 + 15 oppure 1 + 31</a></div>";
    List<WebSearchParser.Hit> hits=WebSearchParser.parseDuckHtml(html);
    if(hits.size()!=2) throw new RuntimeException("hits="+hits.size());
    WebSearchParser.Hit best=WebSearchParser.bestHit(hits,"Bellini Hydrofen");
    if(best==null || !best.url.contains("bellinifoto.it")) throw new RuntimeException("official source not ranked first: "+(best==null?"null":best.url));
    List<String> dils=WebSearchParser.extractDilutions(best.title+" "+best.snippet);
    if(!dils.contains("1+15") || !dils.contains("1+31")) throw new RuntimeException("dilutions="+dils);
    System.out.println("PASS Bellini Hydrofen -> official Bellini source -> 1+15, 1+31");
  }
}
''')
    subprocess.run(['javac',str(dst/'WebSearchParser.java'),str(test)],cwd=d,check=True)
    out=subprocess.check_output(['java','-cp',str(d),'TestWeb'],cwd=d,text=True)
    print(out.strip())
