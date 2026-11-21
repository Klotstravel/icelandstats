#!/usr/bin/env python3
"""Собирает самостоятельную версию страницы «Исландия статистика» для GitHub Pages.

Использование: python3 build_site.py <page.html> <папка_с_csv> <выходная_папка>
page.html — код страницы (стили + разметка + скрипт), тот же, что в артефакте (files/index.html, поле text).
"""
import json, sys, pathlib, datetime

DATASETS = {
    'by_year': 'foreigners_by_year.csv',
    'by_month': 'foreigners_by_month.csv',
    'by_country': 'keflavik_by_country_year.csv',
    'cruise': 'cruise_reykjavik_by_year.csv',
    'immig': 'immigrants_by_country_year.csv',
    'pop': 'population_by_place_year.csv',
    'gdp': 'gdp_by_year.csv',
    'va': 'value_added_by_industry.csv',
    'exports': 'exports_by_year.csv',
    'pop_hist': 'population_history.csv',
}

THEME = """
:root{
  --font-anthropic-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-anthropic-serif: Georgia, "Times New Roman", serif;
  --color-bg:#faf9f5; --color-fg:#1f1e1d; --color-fg-muted:#6b6a66; --color-panel:#ffffff;
  --color-border-line:#e6e3da; --color-ok:#2e8540; --color-bad:#c4392f;
  --cds-gap-lg:24px; --cds-pad-md:12px; --cds-pad-lg:18px; --cds-radius:10px;
  --cds-font-size-title:30px; --cds-font-size-heading:17px; --cds-font-size-body:15px; --cds-font-size-caption:13px;
  --cds-font-weight-medium:600;
  --cds-chart-muted:#c9c6bd; --cds-chart-grid:#ecebe6; --cds-chart-axis:#bdbab2; --cds-text-secondary:#6b6a66;
  --cds-surface-popover:#ffffff; --cds-border:#e0ddd4; --cds-shadow-popover:0 4px 14px rgba(0,0,0,.10);
  --chart-1:#3b6fd4;
}
@media (prefers-color-scheme: dark){:root{
  --color-bg:#1f1e1d; --color-fg:#f1efe8; --color-fg-muted:#a3a19a; --color-panel:#2a2927;
  --color-border-line:#3d3b38; --color-ok:#5cc274; --color-bad:#ef6f63;
  --cds-chart-muted:#5a5853; --cds-chart-grid:#3a3936; --cds-chart-axis:#5c5a55; --cds-text-secondary:#a3a19a;
  --cds-surface-popover:#2f2e2b; --cds-border:#47453f; --cds-shadow-popover:0 4px 14px rgba(0,0,0,.4);
  --chart-1:#6f9bf0;
}}
html{background:var(--color-bg)}
body{margin:0;padding:20px 16px 40px;background:var(--color-bg)}
.is-wrap{max-width:980px;margin:0 auto}
.site-foot{max-width:980px;margin:24px auto 0;color:var(--color-fg-muted);font:13px var(--font-anthropic-sans)}
.site-foot a{color:inherit}
"""

SHIM = r"""
(function(){
  const raw = window.__DATA__, cache = {}, calcs = {}, draws = {};
  function data(id){
    if (cache[id]) return cache[id];
    if (raw[id] != null) return cache[id] = {status:'ok', data: d3.csvParse(raw[id])};
    const c = calcs[id];
    if (c) {
      const ins = c.inputs.map(data);
      if (ins.some(s => s.status !== 'ok')) return {status:'error'};
      return cache[id] = {status:'ok', data: c.fn(...ins.map(s => s.data))};
    }
    return {status:'error'};
  }
  function run(name){
    const fn = draws[name]; if (!fn) return;
    document.querySelectorAll('[data-draw="' + name + '"]').forEach(el => { try { fn(el); } catch(e){ console.error(name, e); } });
  }
  const color = getComputedStyle(document.documentElement).getPropertyValue('--chart-1').trim() || '#3b6fd4';
  window.dash = {
    colors: [color],
    data: data,
    calc: (name, spec) => { calcs[name] = spec; },
    draw: (name, fn) => { if (fn) { draws[name] = fn; if (window.__READY__) run(name); } else run(name); }
  };
  function runAll(root){
    Object.keys(draws).forEach(n => {
      if (!root || root.querySelector('[data-draw="' + n + '"]')) run(n);
    });
  }
  window.__runAll = runAll;
  document.addEventListener('toggle', e => { if (e.target.tagName === 'DETAILS' && e.target.open) runAll(e.target); }, true);
  let t; window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => runAll(), 200); });
})();
"""


def main(page_path, csv_dir, out_dir):
    page = pathlib.Path(page_path).read_text(encoding='utf-8')
    csv_dir = pathlib.Path(csv_dir)
    data = {k: (csv_dir / v).read_text(encoding='utf-8') for k, v in DATASETS.items()}
    here = pathlib.Path(__file__).resolve().parent
    d3js = (here / 'vendor' / 'd3.min.js').read_text(encoding='utf-8')
    page = page.replace('<meta name="dash-one-writer">', '')
    # скрипт страницы должен выполниться после shim; вынимаем его и вставляем в конец
    i = page.rindex('<script>'); j = page.rindex('</script>')
    page_js = page[i + 8:j]; page_body = page[:i] + page[j + 9:]
    today = datetime.date.today().strftime('%d.%m.%Y')
    data_js = 'window.__DATA__=' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + ';'
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Исландия статистика — Klots Travel</title>
<meta name="description" content="Статистика Исландии на русском: туристы через Кеблавик по годам, месяцам и странам, круизы, население, иммигранты, ВВП и экспорт. Данные Statistics Iceland.">
<style>{THEME}</style>
</head>
<body>
{page_body}
<footer class="site-foot">Данные: <a href="https://www.statice.is/">Statistics Iceland (Hagstofa Íslands)</a>. Страница обновлена {today}. <a href="https://klotstravel.com">Klots Travel</a> — авторские туры в Исландию малыми группами.</footer>
<script>{d3js}</script>
<script>{data_js}</script>
<script>{SHIM}</script>
<script>{page_js}
window.__READY__ = true; window.__runAll();
</script>
</body>
</html>
"""
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / 'index.html').write_text(html, encoding='utf-8')
    (out / 'CNAME').write_text('stats.klotstravel.com\n', encoding='utf-8')
    (out / '.nojekyll').write_text('', encoding='utf-8')
    print('ok', out / 'index.html', round(len(html.encode()) / 1024), 'KB')


if __name__ == '__main__':
    main(*sys.argv[1:4])
