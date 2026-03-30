"""
Steg Analyzer - Report renderer (text / JSON / HTML).
"""

import json
from pathlib import Path
from datetime import datetime
from .utils import print_section, print_result, print_found, print_warning


class Reporter:
    def __init__(self, output_dir: Path, fmt: str = "text"):
        self.output_dir = output_dir
        self.fmt = fmt

    def render(self, results: dict, image_path: Path):
        if self.fmt == "json":
            self._render_json(results, image_path)
        elif self.fmt == "html":
            self._render_html(results, image_path)
        else:
            self._render_text(results, image_path)

    # ── text ──────────────────────────────────────────────────────────────────

    def _render_text(self, results: dict, image_path: Path):
        for module_name, data in results.items():
            if not data:
                continue
            print_section(module_name.upper().replace("_", " "))

            if isinstance(data, dict):
                for key, val in data.items():
                    if key == "flags" and val:
                        for f in val:
                            print_found("FLAG", f)
                    elif key == "strings" and val:
                        print_result("Printable strings", f"{len(val)} found")
                        for s in val[:10]:
                            print(f"      → {s[:120]}")
                        if len(val) > 10:
                            print(f"      ... and {len(val)-10} more")
                    elif isinstance(val, list):
                        print_result(key, ", ".join(str(v) for v in val[:5]))
                    elif isinstance(val, bool):
                        print_result(key, "Yes" if val else "No")
                    else:
                        print_result(key, str(val))
            elif isinstance(data, str):
                print(f"  {data}")

    # ── json ──────────────────────────────────────────────────────────────────

    def _render_json(self, results: dict, image_path: Path):
        report = {
            "tool": "Steg Analyzer",
            "timestamp": datetime.utcnow().isoformat(),
            "image": str(image_path.resolve()),
            "results": results,
        }
        out = self.output_dir / "report.json"
        out.write_text(json.dumps(report, indent=2, default=str))
        print(f"  JSON report → {out}")

    # ── html ──────────────────────────────────────────────────────────────────

    def _render_html(self, results: dict, image_path: Path):
        rows = ""
        for module, data in results.items():
            if not data:
                continue
            rows += f'<tr><td colspan="2" class="section">{module.upper()}</td></tr>\n'
            if isinstance(data, dict):
                for k, v in data.items():
                    css = ' class="flag"' if k == "flags" and v else ""
                    val_html = (
                        "<br>".join(str(x) for x in v)
                        if isinstance(v, list)
                        else str(v)
                    )
                    rows += f"<tr{css}><td>{k}</td><td>{val_html}</td></tr>\n"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Steg Analyzer Report – {image_path.name}</title>
<style>
  body {{ font-family: 'Courier New', monospace; background:#0d0d0d; color:#e0e0e0; padding:2rem; }}
  h1 {{ color:#00e5ff; }} h2 {{ color:#888; font-size:.9rem; }}
  table {{ border-collapse:collapse; width:100%; margin-top:1rem; }}
  td {{ padding:.4rem .8rem; border-bottom:1px solid #222; vertical-align:top; }}
  td:first-child {{ color:#aaa; width:220px; white-space:nowrap; }}
  tr.section td {{ background:#1a1a2e; color:#00e5ff; font-weight:bold; padding:.6rem .8rem; }}
  tr.flag td {{ background:#0d2d0d; color:#00ff88; font-weight:bold; }}
  a {{ color:#00e5ff; }}
</style>
</head>
<body>
<h1>🔍 Steg Analyzer Report</h1>
<h2>File: {image_path.name} &nbsp;|&nbsp; Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</h2>
<table>
{rows}
</table>
</body>
</html>"""

        out = self.output_dir / "report.html"
        out.write_text(html)
        print(f"  HTML report → {out}")
