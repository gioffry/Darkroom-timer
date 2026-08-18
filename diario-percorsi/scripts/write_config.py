from pathlib import Path
import json, os

cfg = {
    "MAPS_API_KEY": os.getenv("MAPS_API_KEY", ""),
    "BACKEND_URL": os.getenv("BACKEND_URL", ""),
}
out = "window.APP_CONFIG = " + json.dumps(cfg, ensure_ascii=False) + ";\n"
out += "window.addEventListener('load',function(){var s=document.createElement('script');s.src='map-search-v2.js';document.body.appendChild(s);});\n"
Path("app/src/main/assets/config.js").write_text(out, encoding="utf-8")
