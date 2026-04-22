#!/usr/bin/env python3
"""Convert BibTeX entries to Hugo Markdown posts (English and Japanese)."""

import re
import os
from pathlib import Path

BIBDIR = Path("/Users/shiro/Dropbox/アプリ/Overleaf/Publication list")
JABIBDIR = Path("/Users/shiro/Dropbox/アプリ/Overleaf/Publication list (in Japanese)")
BIBFILES = [
    BIBDIR / "abbreviation.bib",
    BIBDIR / "1990publications-e.bib",
    BIBDIR / "2000publications-e.bib",
    BIBDIR / "2010publications-e.bib",
    BIBDIR / "2020publications-e.bib",
    BIBDIR / "eht-collaboration.bib",
    BIBDIR / "eht-official.bib",
    JABIBDIR / "publications-j.bib",
]
OUTPUT_DIR = Path("/Users/shiro/github/ikeda46.github.io/content/posts")

# Tags for international (English) publications
TAG_EN = {
    "article":      "Journal Paper",
    "inproceedings":"Conference Paper",
    "patent":       "Patent",
    "techreport":   "Technical Report",
    "incollection": "Book Chapter",
    "thesis":       "Thesis",
    "misc":         "Misc",
}
TAG_JA = {
    "article":      "学術論文",
    "inproceedings":"国際会議",
    "patent":       "特許",
    "techreport":   "テクニカルレポート",
    "incollection": "書籍章",
    "thesis":       "学位論文",
    "misc":         "その他",
}
# Tags for Japanese domestic publications
TAG_EN_DOM = {
    "article":      "Journal Paper",
    "inproceedings":"Domestic Conference Paper",
    "patent":       "Patent",
    "techreport":   "Technical Report",
    "incollection": "Book Chapter",
    "thesis":       "Thesis",
    "misc":         "Misc",
}
TAG_JA_DOM = {
    "article":      "学術論文",
    "inproceedings":"国内会議",
    "patent":       "特許",
    "techreport":   "テクニカルレポート",
    "incollection": "書籍章",
    "thesis":       "学位論文",
    "misc":         "その他",
}
MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}

# ── LaTeX cleanup ────────────────────────────────────────────────────────────

# bib_defs.tex custom macros
BIB_DEFS_MAP = {
    r'\solarmassbib': '$M_{\\odot}$',
    r'\sgrabib':      'Sgr A*',
    r'\messierbib':   'M87*',
    r'\uasbib':       'µas',
}

# siunitx prefix symbols
SIUNITX_PREFIX_MAP = {
    'femto': 'f', 'pico': 'p', 'nano': 'n', 'micro': 'µ',
    'milli': 'm', 'centi': 'c', 'deci': 'd',
    'kilo': 'k', 'mega': 'M', 'giga': 'G', 'tera': 'T', 'peta': 'P',
}

# siunitx unit symbols
SIUNITX_UNIT_MAP = {
    'metre': 'm', 'meter': 'm', 'second': 's', 'gram': 'g',
    'hertz': 'Hz', 'kelvin': 'K', 'joule': 'J', 'watt': 'W',
    'electronvolt': 'eV', 'parsec': 'pc', 'jansky': 'Jy',
    'arcminute': 'arcmin', 'arcsecond': 'arcsec',
    'degree': '°', 'percent': '%',
    'as': 'as',
}

LATEX_ACCENTS = {
    r'\"a': 'ä', r'\"o': 'ö', r'\"u': 'ü',
    r'\"A': 'Ä', r'\"O': 'Ö', r'\"U': 'Ü',
    r"\'a": 'á', r"\'e": 'é', r"\'i": 'í', r"\'o": 'ó', r"\'u": 'ú',
    r"\'A": 'Á', r"\'E": 'É', r"\'I": 'Í', r"\'O": 'Ó', r"\'U": 'Ú',
    r'\`a': 'à', r'\`e': 'è', r'\`i': 'ì', r'\`o': 'ò', r'\`u': 'ù',
    r'\^a': 'â', r'\^e': 'ê', r'\^i': 'î', r'\^o': 'ô', r'\^u': 'û',
    r'\~n': 'ñ', r'\~N': 'Ñ', r'\c{c}': 'ç', r'\c{C}': 'Ç',
    r'\L': 'Ł', r'\l': 'ł', r'\o': 'ø', r'\O': 'Ø',
    r'\aa': 'å', r'\AA': 'Å', r'\ss': 'ß',
}

def _expand_siunitx_tokens(content):
    """Expand a sequence of siunitx prefix/unit tokens (space-separated) to a symbol string."""
    result = ''
    for tok in content.split():
        tok = tok.strip()
        if tok in SIUNITX_PREFIX_MAP:
            result += SIUNITX_PREFIX_MAP[tok]
        elif tok in SIUNITX_UNIT_MAP:
            result += SIUNITX_UNIT_MAP[tok]
        else:
            result += tok
    return result

def clean_latex(text):
    if not text:
        return ""
    # Collapse BibTeX multi-line whitespace (newline + indent spaces) into single space
    text = re.sub(r'\n[ \t]+', ' ', text)
    # Remove display math markers (keep inline $...$)
    text = re.sub(r'\$\$(.+?)\$\$', r'$\1$', text, flags=re.DOTALL)
    # \qty{val}{unit} -> val unit
    text = re.sub(r'\\qty\{([^}]+)\}\{([^}]+)\}', r'\1 \2', text)
    # \ang{value} -> value° (siunitx angle)
    text = re.sub(r'\\ang\{([^}]+)\}', r'\1°', text)
    # \unit{...} -> expand siunitx units
    text = re.sub(r'\\unit\{([^}]+)\}', lambda m: _expand_siunitx_tokens(m.group(1)), text)
    # \prefix\unit sequences e.g. \milli\metre -> mm
    prefix_pat = '|'.join(SIUNITX_PREFIX_MAP.keys())
    unit_pat = '|'.join(SIUNITX_UNIT_MAP.keys())
    text = re.sub(
        rf'\\({prefix_pat})\\({unit_pat})\b',
        lambda m: SIUNITX_PREFIX_MAP[m.group(1)] + SIUNITX_UNIT_MAP[m.group(2)],
        text,
    )
    # standalone siunitx unit/prefix commands
    for unit, sym in SIUNITX_UNIT_MAP.items():
        text = re.sub(rf'\\{unit}\b', sym, text)
    for prefix, sym in SIUNITX_PREFIX_MAP.items():
        text = re.sub(rf'\\{prefix}\b', sym, text)
    # \textit{...} -> *...*
    text = re.sub(r'\\textit\{([^}]*)\}', r'*\1*', text)
    # \textbf{...} -> **...**
    text = re.sub(r'\\textbf\{([^}]*)\}', r'**\1**', text)
    # \emph{...} -> *...*
    text = re.sub(r'\\emph\{([^}]*)\}', r'*\1*', text)
    # \url{...} -> ...
    text = re.sub(r'\\url\{([^}]+)\}', r'\1', text)
    # accent commands with braces: {\"a} or {\"{a}}
    text = re.sub(r'\{\\(["\'\`\^~])(\w)\}', lambda m: LATEX_ACCENTS.get('\\' + m.group(1) + m.group(2), m.group(0)), text)
    text = re.sub(r'\{\\(["\'\`\^~])\{(\w)\}\}', lambda m: LATEX_ACCENTS.get('\\' + m.group(1) + m.group(2), m.group(0)), text)
    # \c{c} style
    for pat, repl in LATEX_ACCENTS.items():
        text = text.replace(pat, repl)
    # Remove remaining braces used for capitalization protection
    text = re.sub(r'\{([^{}]*)\}', r'\1', text)
    # \mu -> {\mu} (protect as a unit in math contexts)
    text = re.sub(r'\\mu\b', r'{\\mu}', text)
    # \, (thin space) -> regular space
    text = text.replace('\\,', ' ')
    # -- -> en dash in running text (keep for math)
    text = text.replace('--', '–')
    # bib_defs.tex custom macros (applied last to avoid double-processing by accent/brace rules)
    for cmd, repl in BIB_DEFS_MAP.items():
        text = text.replace(cmd, repl)
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ── BibTeX parser ────────────────────────────────────────────────────────────

def _find_matching_brace(text, start):
    """Return index just after the matching closing brace."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)

def _parse_value(text, pos, strings):
    """Parse one BibTeX field value starting at pos; return (value_str, new_pos)."""
    parts = []
    while pos < len(text):
        # skip whitespace before each part
        while pos < len(text) and text[pos] in ' \t\n\r':
            pos += 1
        if pos >= len(text):
            break
        ch = text[pos]
        if ch == '{':
            end = _find_matching_brace(text, pos)
            parts.append(text[pos+1:end-1])
            pos = end
        elif ch == '"':
            end = pos + 1
            while end < len(text) and text[end] != '"':
                if text[end] == '\\':
                    end += 1
                end += 1
            parts.append(text[pos+1:end])
            pos = end + 1
        elif ch.isdigit():
            end = pos
            while end < len(text) and text[end].isdigit():
                end += 1
            parts.append(text[pos:end])
            pos = end
        elif ch.isalpha() or ch == '_':
            end = pos
            while end < len(text) and (text[end].isalnum() or text[end] == '_' or text[end] == '-'):
                end += 1
            macro = text[pos:end]
            parts.append(strings.get(macro, macro))
            pos = end
        else:
            break
        # skip whitespace
        while pos < len(text) and text[pos] in ' \t\n\r':
            pos += 1
        if pos < len(text) and text[pos] == '#':
            pos += 1  # concatenation
        else:
            break
    return ' '.join(parts), pos

def _parse_fields(body, strings):
    """Parse the field=value pairs from a bib entry body."""
    fields = {}
    pos = 0
    while pos < len(body):
        # skip whitespace / commas
        while pos < len(body) and body[pos] in ' \t\n\r,':
            pos += 1
        if pos >= len(body):
            break
        # field name
        if not (body[pos].isalpha() or body[pos] == '_'):
            pos += 1
            continue
        end = pos
        while end < len(body) and (body[end].isalnum() or body[end] == '_'):
            end += 1
        fname = body[pos:end].lower()
        pos = end
        # skip whitespace and '='
        while pos < len(body) and body[pos] in ' \t\n\r':
            pos += 1
        if pos >= len(body) or body[pos] != '=':
            continue
        pos += 1
        val, pos = _parse_value(body, pos, strings)
        fields[fname] = val
    return fields

def parse_bib_files(paths):
    """Parse a list of BibTeX files; return (list_of_entries, strings_dict)."""
    strings = {}
    entries = []

    for path in paths:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
        # remove line comments
        text = re.sub(r'(?m)^%.*$', '', text)

        i = 0
        while i < len(text):
            at = text.find('@', i)
            if at == -1:
                break
            # entry type
            m = re.match(r'@(\w+)\s*[{(]', text[at:], re.IGNORECASE)
            if not m:
                i = at + 1
                continue
            entry_type = m.group(1).lower()
            open_pos = at + m.end() - 1  # position of '{' or '('
            close_char = ')' if text[open_pos] == '(' else '}'
            # find matching close
            depth = 0
            j = open_pos
            while j < len(text):
                c = text[j]
                if c == '{' or c == '(':
                    depth += 1
                elif c == '}' or c == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            body = text[open_pos+1:j]
            i = j + 1

            if entry_type == 'string':
                # key = {value}
                sm = re.match(r'\s*(\w+)\s*=\s*', body)
                if sm:
                    skey = sm.group(1)
                    sval, _ = _parse_value(body, sm.end(), strings)
                    strings[skey] = sval
                continue
            if entry_type in ('comment', 'preamble'):
                continue

            # regular entry: first token before comma is the key
            cm = re.match(r'\s*([^,\s]+)\s*,', body)
            if not cm:
                continue
            ekey = cm.group(1)
            fields = _parse_fields(body[cm.end():], strings)
            entries.append({'_type': entry_type, '_key': ekey, **fields})

    return entries, strings

# ── Author formatting ────────────────────────────────────────────────────────

def format_authors(author_str, japanese=False):
    """Split 'Last, First and Last, First ...' into name list.
    Western order: 'First Last'; Japanese order: 'Last First' (no swap)."""
    if not author_str:
        return []
    raw = re.split(r'\s+and\s+', author_str, flags=re.IGNORECASE)
    result = []
    for a in raw:
        a = clean_latex(a.strip())
        if ',' in a:
            parts = [p.strip() for p in a.split(',', 1)]
            if japanese:
                result.append(f"{parts[0]} {parts[1]}")
            else:
                result.append(f"{parts[1]} {parts[0]}")
        else:
            result.append(a)
    return result

# ── Date helpers ─────────────────────────────────────────────────────────────

def entry_date(entry):
    year = entry.get('year', '').strip()
    month_raw = entry.get('month', '').strip().lower()
    month = MONTH_MAP.get(month_raw, None)
    if month is None:
        try:
            month = int(month_raw)
        except ValueError:
            month = 1
    if not year:
        # try extracting from key: YYYY.MM.*
        m = re.match(r'(\d{4})\.(\d{2})', entry.get('_key', ''))
        if m:
            year, month = m.group(1), int(m.group(2))
    year = int(year) if year else 2000
    return f"{year:04d}-{month:02d}-01"

# ── Venue description ────────────────────────────────────────────────────────

def venue_line(entry):
    t = entry['_type']
    parts = []
    if t == 'article':
        j = clean_latex(entry.get('journal', ''))
        vol = entry.get('volume', '')
        num = entry.get('number', '')
        pages = entry.get('pages', '')
        if j:
            parts.append(f"*{j}*")
        if vol:
            parts.append(f"vol. {vol}")
        if num:
            parts.append(f"no. {num}")
        if pages:
            parts.append(f"pp. {pages}")
    elif t == 'inproceedings':
        b = clean_latex(entry.get('booktitle', ''))
        pages = entry.get('pages', '')
        if b:
            parts.append(f"*{b}*")
        if pages:
            parts.append(f"pp. {pages}")
    elif t == 'techreport':
        inst = clean_latex(entry.get('institution', ''))
        num = entry.get('number', '')
        if inst:
            parts.append(inst)
        if num:
            parts.append(f"no. {num}")
    elif t == 'patent':
        num = entry.get('number', '')
        if num:
            parts.append(num)
    elif t in ('incollection', 'misc'):
        b = clean_latex(entry.get('booktitle', '') or entry.get('howpublished', ''))
        if b:
            parts.append(f"*{b}*")
    elif t == 'thesis':
        type_ = clean_latex(entry.get('type', ''))
        inst = clean_latex(entry.get('institution', ''))
        if type_:
            parts.append(type_)
        if inst:
            parts.append(inst)
    return ', '.join(parts)

# ── URL list ─────────────────────────────────────────────────────────────────

def url_links(entry):
    links = []
    doi = entry.get('doi', '').strip()
    if doi:
        links.append(f'<a href="https://doi.org/{doi}" target="_blank" rel="noopener">DOI</a>')
    url = entry.get('url', '').strip()
    if url and 'doi.org' not in url:
        links.append(f'<a href="{url}" target="_blank" rel="noopener">Link</a>')
    eprint = entry.get('eprint', '').strip()
    eprinttype = entry.get('eprinttype', '').strip().lower()
    if eprint and eprinttype == 'arxiv':
        links.append(f'<a href="https://arxiv.org/abs/{eprint}" target="_blank" rel="noopener">arXiv</a>')
    return links

# ── Post generators ──────────────────────────────────────────────────────────

def make_post(entry, lang):
    etype = entry['_type']
    is_japanese = entry.get('langid', '').lower() == 'japanese'
    if is_japanese:
        tag = (TAG_EN_DOM if lang == 'en' else TAG_JA_DOM).get(etype, etype)
    else:
        tag = (TAG_EN if lang == 'en' else TAG_JA).get(etype, etype)
    title = clean_latex(entry.get('title', '(no title)'))
    # Escape backslashes then quotes for YAML double-quoted strings
    title_yaml = title.replace('\\', '\\\\').replace('"', '\\"')
    date_str = entry_date(entry)
    authors = format_authors(entry.get('author', ''), japanese=is_japanese)
    keywords = [k.strip() for k in entry.get('keywords', '').split(',') if k.strip()]
    abstract = clean_latex(entry.get('abstract', ''))
    venue = venue_line(entry)
    links = url_links(entry)

    if lang == 'en':
        lines = [
            '---',
            f'date: {date_str}',
            f'publishDate: {date_str}',
            f'title: "{title_yaml}"',
            f'tags: ["{tag}"]',
            'math: true',
            'draft: false',
            '---',
            '',
        ]
        if venue:
            lines += [venue, '']
        if authors:
            lines += ['### Authors:', '']
            lines += [f'- {a}' for a in authors]
            lines += ['']
        if keywords:
            lines += ['### Keywords:', '']
            lines += [f'- {k}' for k in keywords]
            lines += ['']
        if links:
            lines += ['### URL:', '']
            lines += [f'- {l}' for l in links]
            lines += ['']
        if abstract:
            lines += ['---', '', '### Abstract:', '', abstract, '']
    else:  # ja
        lines = [
            '---',
            f'date: {date_str}',
            f'publishDate: {date_str}',
            f'title: "{title_yaml}"',
            f'tags: ["{tag}"]',
            'math: true',
            'draft: false',
            '---',
            '',
        ]
        if venue:
            lines += [venue, '']
        if authors:
            lines += ['### 著者:', '']
            lines += [f'- {a}' for a in authors]
            lines += ['']
        if keywords:
            lines += ['### キーワード:', '']
            lines += [f'- {k}' for k in keywords]
            lines += ['']
        if links:
            lines += ['### URL:', '']
            lines += [f'- {l}' for l in links]
            lines += ['']
        if abstract:
            lines += ['---', '', '### Abstract:', '', abstract, '']

    return '\n'.join(lines)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Parsing BibTeX files…")
    entries, _ = parse_bib_files(BIBFILES)
    print(f"  Found {len(entries)} entries")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_tags = TAG_EN | TAG_EN_DOM
    created = skipped = 0
    for entry in entries:
        key = entry['_key']
        etype = entry['_type']
        if etype not in all_tags:
            print(f"  [skip unknown type] {etype}: {key}")
            continue

        is_japanese = entry.get('langid', '').lower() == 'japanese'
        en_path = OUTPUT_DIR / f"{key}.md"
        ja_path = OUTPUT_DIR / f"{key}.ja.md"

        if is_japanese:
            if ja_path.exists():
                skipped += 1
                continue
            ja_path.write_text(make_post(entry, 'ja'), encoding='utf-8')
        else:
            if en_path.exists() or ja_path.exists():
                skipped += 1
                continue
            en_path.write_text(make_post(entry, 'en'), encoding='utf-8')
            ja_path.write_text(make_post(entry, 'ja'), encoding='utf-8')

        print(f"  [created] {key}")
        created += 1

    print(f"\nDone: {created} entries created, {skipped} skipped (already exist).")

if __name__ == '__main__':
    main()
