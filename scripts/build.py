"""Build the public static reference site from explicit publication snapshots.

Requires the existing Python Markdown package. No raw research archives are inputs.
"""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

import markdown

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_KEYS = {'id', 'title', 'url', 'principles', 'identifiers', 'year', 'journal',
               'summary_he', 'relevance_he', 'limitation_he', 'kind', 'evidence_status'}
REPO_URL = 'https://github.com/aharonyaircohen/breath-and-silence-site'
SITE_ORIGIN = 'https://aharonyaircohen.github.io'
PRINCIPLES = {
    'P1': ('המוח מתמכר לרעש', 'תגמול, חזרתיות, חיפוש גירוי ואפשרות ללמידה מחדש.'),
    'P2': ('סטרס לא מודע כרוני', 'עומס פנימי והפעלה מתמשכת שאינם תמיד נוכחים בדיווח המודע.'),
    'P3': ('אנרגיה, קשב וחיוניות', 'המחיר המטבולי, היכולת לתפקד ותחושת האנרגיה - שלושה תחומים קשורים, לא מדד אחד.'),
    'P4': ('אימון לשקט ולעומק', 'מה מתרחש בחוויה, מעבר למספר הדקות, ומה ידוע על תפקיד העומק.'),
    'P5': ('שחרור מטען לא מודע', 'שינוי תגובות אוטומטיות ורגשיות בלי לחייב הבנה סיפורית או פורקן.'),
    'P6': ('מצב הבסיס והתגובה לסטרס', 'הבחנה בין הקלה בזמן תרגול, שינוי במנוחה ותגובה בזמן דרישה.'),
    'P7': ('שיפור, שימור ודעיכה', 'מה עשוי להשתנות, מה נשאר לאחר התרגול ומה הניסוי מבקש לברר.'),
    'B': ('רקע ובטיחות', 'מקורות רקע, לא הוכחה ליעילות.'),
}
KINDS = {'trial': 'ניסוי', 'observational': 'מחקר תצפיתי', 'review': 'סקירה',
         'theory': 'מודל תיאורטי', 'pilot': 'פיילוט', 'preprint': 'פרה־פרינט',
         'correction': 'תיקון מאמר', 'protocol': 'רישום או פרוטוקול',
         'report': 'דוח', 'background': 'מקור רקע'}
STATUSES = {'measured': 'ממצא מדוד', 'mixed': 'תוצאות מעורבות', 'indirect': 'תמיכה עקיפה',
            'theory': 'מסגרת תיאורטית', 'preliminary': 'ראשוני', 'background': 'רקע בלבד',
            'correction': 'תיקון', 'protocol': 'תכנון, לא תוצאה'}
NAV = [('home', '', 'התחלה'), ('model', 'model/', 'המודל המלא'),
       ('research', 'research/', 'המחקרים'), ('process', 'process/', 'התהליך'),
       ('experiment', 'experiment/', 'הניסוי'), ('about', 'about/', 'איך לקרוא')]


def public_model(text, base='/'):
    """Adapt publication links without changing the author's model principles."""
    text = text.split('\n## Sources')[0]
    text = text.replace('גרסת עבודה פנימית לעיון עם יאיר', 'גרסת עבודה מחקרית לעיון')
    text = text.replace('לא נוסח שיווקי למשתתפים', 'לא הבטחת תוצאה למשתתפים')
    for target in ['research/evidence-map.md', 'research/sources.md']:
        text = text.replace('](' + target + ')', '](' + base + 'research/)')
    text = text.replace('](research/library.json)', '](' + base + 'assets/research.json)')
    return re.sub(r'\[(\d+)\]', lambda m: '<a class="cite" href="' + base +
                  'research/s' + m[1].zfill(3) + '/" aria-label="מקור ' +
                  m[1] + '">[' + m[1] + ']</a>', text)


def public_record(item, summary):
    """Export only explicit public fields, never archive or provenance data."""
    meta = (item.get('metadata') or [{}])[0]
    return {
        'id': item['id'], 'title': item['title'], 'url': item['url'],
        'principles': item.get('principles', []), 'identifiers': item.get('identifiers', {}),
        'year': str(meta.get('pubYear') or ''), 'journal': meta.get('journalTitle') or '',
        **{key: summary.get(key, '') for key in
           ['summary_he', 'relevance_he', 'limitation_he', 'kind', 'evidence_status']},
    }


def esc(value):
    return html.escape(str(value), quote=True)


def shell(title, body, base, active='home', route='', description='נשימה ושקט: המודל, המחקרים והתהליך. ממצאים, פרשנות והשערות - בנפרד.'):
    nav = ''.join(f'<a href="{base}{path}"' + (' aria-current="page"' if key == active else '') + f'>{label}</a>' for key, path, label in NAV)
    canonical = SITE_ORIGIN + base + route
    return f'''<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | נשימה ושקט</title><meta name="description" content="{esc(description)}">
<meta name="theme-color" content="#214d3d"><link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:locale" content="he_IL"><meta property="og:title" content="{esc(title)} | נשימה ושקט"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical)}">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'none'">
<link rel="stylesheet" href="{base}assets/site.css"><link rel="icon" href="{base}assets/favicon.svg" type="image/svg+xml"><script src="{base}assets/site.js" defer></script></head>
<body><a class="skip" href="#main">דילוג לתוכן</a><header class="topbar"><div class="wrap topbar-inner"><a class="brand" href="{base}">נשימה ושקט<span>המודל · המחקר · התהליך</span></a><nav class="nav" aria-label="ניווט ראשי">{nav}</nav><details class="mobile-nav"><summary>תפריט</summary><nav aria-label="ניווט בנייד">{nav}</nav></details></div></header>
<main id="main" class="wrap">{body}</main>
<footer class="site-footer"><div class="wrap footer-inner"><p>מודל עבודה ומאגר מחקר, לא הבטחת תוצאה או תחליף לטיפול. המקורות כוללים גם מגבלות, תוצאות אפס ומקורות רקע. אין חובה לחוות עומק, שחרור או רגש מסוים.</p><a href="{REPO_URL}" target="_blank" rel="noopener noreferrer">קוד האתר ותיעוד</a></div></footer></body></html>'''


def page_head(title, description, base, parent=None):
    crumb = f'<a href="{base}">התחלה</a>'
    if parent:
        crumb += f' / <a href="{base}research/">המחקרים</a>'
    return f'<header class="page-head"><div class="breadcrumbs">{crumb}</div><h1>{esc(title)}</h1><p class="lead">{description}</p></header>'


def render_reader(text, title, description, base, active, route):
    md = markdown.Markdown(extensions=['extra', 'toc'], extension_configs={'toc': {'toc_depth': '1-2', 'title': ''}})
    rendered = md.convert(public_model(text, base))
    toc = getattr(md, 'toc', '').replace('class="toc"', 'class="toc-links"')
    body = page_head(title, description, base) + '<div class="reader-layout">' + f'<aside class="toc"><details open><summary>במסמך הזה</summary><div>{toc}</div></details></aside><article class="article">{rendered}</article></div>'
    return shell(title, body, base, active, route)


def render_home(records, base):
    principles = ''.join(f'<li><a href="{base}research/?p={pid}"><span class="principle-code" dir="ltr">{pid}</span><div><h3>{esc(title)}</h3><p>{esc(desc)}</p></div></a></li>' for pid, (title, desc) in PRINCIPLES.items() if pid != 'B')
    body = f'''<section class="hero"><div><div class="eyebrow">נשימה ושקט / מסמך יסוד ומפת מחקר</div><h1>להכיר שקט.<br>ללמוד לחזור אליו.</h1><p class="lead">אימון חוזר במפגש עם שקט עמוק - לא רק כדי להירגע באותו ערב, אלא כדי לבדוק אפשרות לשינוי בנקודת המוצא, בתגובה לדרישות ובחיוניות.</p><div class="actions"><a class="button" href="{base}model/">לקריאת המודל</a><a class="button secondary" href="{base}research/">למאגר המחקרים</a></div></div><aside class="hero-aside"><h2>שלוש שכבות, בלי לערבב ביניהן</h2><p><strong>המודל מציע.</strong> הסבר מחבר במילים של יאיר.</p><p><strong>המחקר מודד.</strong> ממצאים, שיטות ומגבלות.</p><p><strong>הניסוי בודק.</strong> מה יקרה בתהליך המסוים.</p></aside></section>
<section class="section-rail"><div><div class="eyebrow">העקרונות</div><h2>מה מחבר<br>את התהליך?</h2><p class="muted">הכותרות הן שפת המודל. כל עיקרון מקושר למקורות הרלוונטיים, בלי להציג את כל שרשרת ההסבר כמנגנון שכבר הוכח.</p></div><ol class="principles">{principles}</ol></section>
<section class="section-rail"><div><div class="eyebrow">מפת הקריאה</div><h2>מהרעיון<br>אל הבדיקה</h2></div><div class="path-list"><a href="{base}model/"><div><strong>מסמך היסוד המלא</strong><span>ההסבר המחבר, הביסוס לכל עיקרון והתחזיות לבדיקה.</span></div><span aria-hidden="true">←</span></a><a href="{base}research/"><div><strong>מאגר המחקרים</strong><span>{len(records)} פריטים ביבליוגרפיים עם סוג מקור, סיכום ומגבלה. לא כולם ניסויים או ממצאים חיוביים.</span></div><span aria-hidden="true">←</span></a><a href="{base}process/"><div><strong>התהליך והבחירה בו</strong><span>נשימה, דמיון, חיבור לילד בלב, דממה וחזרה לשגרה.</span></div><span aria-hidden="true">←</span></a><a href="{base}experiment/"><div><strong>הניסוי והמדידה</strong><span>מה נבדוק לפני, במהלך ואחרי, וכיצד נבחין בין רוגע מיידי לשינוי ביומיום.</span></div><span aria-hidden="true">←</span></a></div></section>
<section class="section-rail"><div><div class="eyebrow">גבולות ההסבר</div><h2>תמיכה אינה<br>הבטחה</h2></div><div><p class="lead">אין צורך שכל רכיבי המודל ייבדקו באותו מחקר כדי שיהיה להם ביסוס. באותה מידה, חיבור כמה ממצאים אינו מוכיח אוטומטית את כל המעברים ביניהם.</p><p>עומק, קוהרנטיות לבבית, דפוסי מוח, חיוניות והוצאה אנרגטית הם מדדים שונים. המונח ״שחרור מטען״ אינו מדידה של חומר שמשתחרר, ודימוי אינו הוכחה לאירועי עבר.</p><a href="{base}about/">איך לקרוא את רמות התמיכה והמקורות ←</a></div></section>'''
    return shell('להכיר שקט. ללמוד לחזור אליו.', body, base)


def tags(record):
    status = STATUSES.get(record['evidence_status'], '')
    kind = KINDS.get(record['kind'], '')
    return f'<span class="source-id" dir="ltr">S{record["id"]:03d}</span>' + (f'<span class="tag">{esc(kind)}</span>' if kind else '') + (f'<span class="tag neutral">{esc(status)}</span>' if status else '') + (f'<span class="muted">{esc(record["year"])}</span>' if record['year'] else '')


def render_catalog(records, base):
    cards = []
    for r in records:
        search = ' '.join(str(r.get(k, '')) for k in ['title', 'summary_he', 'relevance_he', 'limitation_he', 'year', 'journal'])
        search += ' ' + ' '.join(PRINCIPLES.get(p, ('', ''))[0] for p in r['principles'])
        cards.append(f'''<article class="source-card" data-search="{esc(search)}" data-principles="{esc(' '.join(r['principles']))}" data-kind="{esc(r['kind'])}"><div class="source-meta">{tags(r)}</div><h2><a href="{base}research/s{r['id']:03d}/"><bdi>{esc(r['title'])}</bdi></a></h2>''' + (f'<p>{esc(r["summary_he"])}</p>' if r['summary_he'] else '') + (f'<p class="muted"><strong>גבול הממצא:</strong> {esc(r["limitation_he"])}</p>' if r['limitation_he'] else '') + f'<a class="more" href="{base}research/s{r["id"]:03d}/">פרטי המקור והקשר למודל ←</a></article>')
    poptions = ''.join(f'<option value="{p}">{p} - {esc(t)}</option>' for p, (t, _) in PRINCIPLES.items())
    kop = ''.join(f'<option value="{k}">{esc(v)}</option>' for k, v in KINDS.items())
    body = page_head('המחקרים ומפת הראיות', 'המקורות מאורגנים לפי העקרונות שהם עוזרים לבחון. שיוך לעיקרון מציין רלוונטיות - לא בהכרח תמיכה חיובית או הוכחה סיבתית.', base) + f'''<div class="research-layout"><p class="legend">״ממצא מדוד״ מתאר מדידה שדווחה, לא דירוג איכות גבוה. ״תוצאות מעורבות״ שומר גם תוצאות אפס. פרוטוקול אינו תוצאה, תיקון אינו ניסוי נוסף ומקור רקע אינו ביסוס ראשי.</p><form id="source-filter" class="filters" role="search"><label for="search">חיפוש במקורות<input id="search" type="search" placeholder="למשל: עומק, חיוניות, קבלה, Dispenza" autocomplete="off"></label><label for="principle">עיקרון במודל<select id="principle"><option value="">כל העקרונות</option>{poptions}</select></label><label for="kind">סוג המקור<select id="kind"><option value="">כל הסוגים</option>{kop}</select></label><button type="reset" class="reset">איפוס</button></form><div class="results-line"><span id="result-count" role="status" aria-live="polite">{len(records)} מתוך {len(records)} מקורות</span><a href="{base}assets/research.json" download>נתוני המאגר</a></div><noscript><p class="noscript">המקורות זמינים במלואם גם בלי JavaScript; החיפוש והסינון דורשים הפעלתו.</p></noscript><p id="empty-results" class="empty" hidden>לא נמצאו מקורות התואמים לחיפוש. אפשר לנסות מונח אחר או לאפס את המסננים.</p><div id="sources">{''.join(cards)}</div></div>'''
    return shell('המחקרים ומפת הראיות', body, base, 'research', 'research/')


def render_source(r, base):
    sid = f'S{r["id"]:03d}'
    links = ''.join(f'<a href="{base}research/?p={esc(p)}">{esc(p)} - {esc(PRINCIPLES.get(p, (p, ""))[0])}</a>' for p in r['principles'])
    ids = []
    for kind, values in r['identifiers'].items():
        if values:
            ids.append(f'<dt>{esc(kind.upper())}</dt><dd dir="ltr">{esc(" ; ".join(values))}</dd>')
    content = f'''<div class="source-detail"><header class="page-head"><div class="breadcrumbs"><a href="{base}">התחלה</a> / <a href="{base}research/">המחקרים</a> / <span dir="ltr">{sid}</span></div><div class="source-meta">{tags(r)}</div><h1><bdi>{esc(r['title'])}</bdi></h1><p><a href="{esc(r['url'])}" target="_blank" rel="noopener noreferrer">פתיחת המקור המקורי ↗</a></p></header><section><h2>מה מתועד במקור?</h2><p>{esc(r['summary_he'])}</p></section><section><h2>הקשר למודל</h2><p>{esc(r['relevance_he'])}</p><div class="principle-links">{links}</div></section><section><h2>המגבלה שחשוב לשמור</h2><p>{esc(r['limitation_he'])}</p></section><section><h2>זיהוי ביבליוגרפי</h2><dl><dt>מספר מקור</dt><dd dir="ltr">{sid}</dd><dt>שנה</dt><dd>{esc(r['year'] or 'לא צוינה ברשומה')}</dd><dt>פרסום</dt><dd><bdi>{esc(r['journal'] or 'ראו בקישור למקור')}</bdi></dd>{''.join(ids)}</dl></section><div class="note"><p>הסיכום מציג מה שנמדד ואת הרלוונטיות האפשרית. הוא אינו אישור לכל טענות המחברים, הוכחה לכל המודל או הנחיה לאמץ פרוטוקול מחקרי.</p></div><a href="{base}research/">← חזרה לכל המקורות</a></div>'''
    return shell(sid + ' - ' + r['title'], content, base, 'research', f'research/s{r["id"]:03d}/')


def render_about(base):
    body = page_head('איך לקרוא את המידע', 'ממצאים, פרשנות והשערות - באותו מרחב, אך לא באותה רמת ודאות.', base) + '''<article class="about-content"><h2>שלוש שכבות של טענה</h2><p><strong>ממצא:</strong> מה שהמחקר מדד ומצא באוכלוסייה, בהשוואה ובזמן המסוימים. <strong>פרשנות:</strong> הדרך שבה הממצא עשוי להתחבר לעיקרון במודל. <strong>השערה:</strong> קשר מוצע שנותר לבדיקה, כגון תפקידו הסיבתי הייחודי של עומק השקט.</p><h2>איכות המחקר וישירותו אינן אותו דבר</h2><p>ניסוי מבוקר יכול לבדוק רכיב רחוק מהתהליך שלנו, ופיילוט קטן יכול להיות קרוב מאוד לחוויה המדוברת. לכן אין ציון יחיד שמחליף קריאת שיטה, תוצאה ומגבלה. פרסום בכתב עת אינו אישור לכל פרשנות; זיקה מסחרית אינה פסילה אוטומטית, אך היא מידע רלוונטי.</p><h2>מה נכלל במאגר?</h2><p>ניסויים, מחקרים תצפיתיים, סקירות, מודלים תיאורטיים, פיילוטים, פרה־פרינטים, דיווחים חווייתיים, תיקוני מאמרים ופרוטוקולים. פריטים מהסבבים השונים אוחדו לפי מזהים וכותרות; מקורות רקע נשמרו אך מסומנים ואינם מוצגים כניסויים תומכים.</p><h2>מה נשמר במילים המקוריות?</h2><p>״המוח מתמכר לרעש״, ״סטרס לא מודע כרוני״ ו״שחרור מטען לא מודע״ הם מונחי המודל של יאיר. השימוש בהם אינו אבחנה קלינית של כל אדם. ״המון אנרגיה״ הוא ניסוח איכותני, ולא מדידה של רוב תקציב האנרגיה.</p><h2>בחירה ובטיחות</h2><p>המידע אינו תחליף לייעוץ או לטיפול, ואינו פרוטוקול נשימה. אין חובה לעצום עיניים, לחוות עומק, לשתף, לקבל מגע או להגיע לפורקן. דימוי של הילד הפנימי אינו ראיה לזיכרון היסטורי. במצוקה יש לפנות לתמיכה אנושית מתאימה, לא להעמיק תרגיל כדי ״להצליח״.</p><h2>פרטיות</h2><p>האתר אינו מכיל נתוני משתתפים ואינו אוסף תשובות לסקר או פרטים אישיים. החיפוש מתבצע בדפדפן ללא שליחת מונחי החיפוש לשירות חיפוש. אין בו כלי אנליטיקה חיצוני. GitHub עשויה לתעד בקשות אירוח בהתאם למדיניותה.</p><h2>מקור ושינויים</h2><p>האתר הוא תוצר פרסום נבחר של חומרי הקורס. הוא כולל סיכומים וקישורים למאמרים המקוריים, לא הפצה של ארכיון הטקסטים המלאים. שינוי במסקנה אמור לשמור גם את הממצא המגביל ולא להחליף בשקט את המודל או להבטיח תוצאה.</p></article>'''
    return shell('איך לקרוא את המידע', body, base, 'about', 'about/')


def build_site(content_dir, output, base='/'):
    content_dir, output = Path(content_dir), Path(output)
    base = '/' + base.strip('/') + '/' if base.strip('/') else '/'
    if not re.fullmatch(r'/[A-Za-z0-9/_-]*', base):
        raise ValueError('Invalid site base path')
    records = json.loads((content_dir / 'research.json').read_text(encoding='utf-8'))
    if not isinstance(records, list) or any(not isinstance(r, dict) or set(r) != PUBLIC_KEYS for r in records):
        raise ValueError('Research input must contain only the complete public field allowlist')
    ids = [r['id'] for r in records]
    if any(type(i) is not int or i < 1 for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('Research IDs must be unique positive integers')
    for r in records:
        source = urlsplit(r['url'])
        if source.scheme not in ['http', 'https'] or not source.hostname:
            raise ValueError('Research source URL must use http or https and have a hostname')
    model = (content_dir / 'model.md').read_text(encoding='utf-8')
    manifest = output / 'site-manifest.json'
    old_generated = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    if not isinstance(old_generated, list) or any(not isinstance(p, str) for p in old_generated):
        raise ValueError('Invalid generated-file manifest')
    for name in old_generated:
        if Path(name).is_absolute() or '..' in Path(name).parts or not (output / name).resolve().is_relative_to(output.resolve()):
            raise ValueError('Generated-file manifest must remain inside the output directory')
    output.mkdir(parents=True, exist_ok=True)
    assets = output / 'assets'
    assets.mkdir(exist_ok=True)
    for name in ['site.css', 'site.js', 'favicon.svg']:
        shutil.copyfile(ROOT / 'assets' / name, assets / name)
    (assets / 'research.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    pages = {
        'index.html': render_home(records, base),
        'model/index.html': render_reader(model, 'מסמך היסוד המלא', 'המודל, הביסוס המחקרי והניסוי - לפי שבעת העקרונות.', base, 'model', 'model/'),
        'research/index.html': render_catalog(records, base),
        'about/index.html': render_about(base),
    }
    layer = model.split('<a id="experiment"></a>')[-1].split('<a id="conclusion"></a>')[0]
    process = layer.split('## 15.')[0]
    experiment = layer[layer.find('## 15.'):] if '## 15.' in layer else layer
    pages['process/index.html'] = render_reader(process, 'התהליך והבחירה בו', 'מסגרת העבודה המוצעת - לא פרוטוקול נשימה מאושר או הבטחת חוויה.', base, 'process', 'process/')
    pages['experiment/index.html'] = render_reader(experiment, 'הניסוי והמדידה', 'שאלות, תחזיות ומדדים מוצעים. אין כאן איסוף פעיל של נתוני משתתפים.', base, 'experiment', 'experiment/')
    pages['404.html'] = shell('העמוד לא נמצא', page_head('העמוד לא נמצא', 'אפשר לחזור למסמך המודל או לחפש במאגר המחקרים.', base) + f'<div class="actions"><a class="button" href="{base}">חזרה להתחלה</a><a class="button secondary" href="{base}research/">חיפוש במחקרים</a></div>', base)
    for r in records:
        pages[f'research/s{r["id"]:03d}/index.html'] = render_source(r, base)
    for route, content in pages.items():
        target = output / route
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    (output / '.nojekyll').write_text('', encoding='utf-8')
    urls = [SITE_ORIGIN + base + (p[:-10] if p.endswith('index.html') else p) for p in pages if p != '404.html']
    (output / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + esc(u) + '</loc></url>' for u in urls) + '</urlset>', encoding='utf-8')
    (output / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + SITE_ORIGIN + base + 'sitemap.xml\n', encoding='utf-8')
    generated = set(pages) | {'.nojekyll', 'sitemap.xml', 'robots.txt', 'assets/site.css',
                              'assets/site.js', 'assets/favicon.svg', 'assets/research.json'}
    for name in set(old_generated) - generated:
        stale = output / name
        if stale.is_file():
            stale.unlink()
            folder = stale.parent
            while folder != output and folder.is_relative_to(output):
                try:
                    folder.rmdir()
                except OSError:
                    break
                folder = folder.parent
    manifest.write_text(json.dumps(sorted(generated), ensure_ascii=False, indent=2), encoding='utf-8')
    return {'pages': len(pages), 'sources': len(records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--content', type=Path, default=ROOT / 'content')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs')
    parser.add_argument('--base', default='/breath-and-silence-site/')
    args = parser.parse_args()
    print(json.dumps(build_site(args.content, args.output, args.base), ensure_ascii=False))


if __name__ == '__main__':
    main()
