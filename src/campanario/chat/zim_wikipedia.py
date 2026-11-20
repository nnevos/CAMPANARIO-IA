"""Read-only, loopback-only Wikipedia ZIM evidence via an existing kiwix-serve.

A ZIM file is never opened or indexed by Campanario itself.  `kiwix-serve`
serves it on 127.0.0.1; we use title suggestions and the official /raw API to
obtain the actual article, not a search snippet.  This adapter never touches
personal memories, calls the internet, or executes content from the archive.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
import logging
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit

import httpx

from campanario.chat.evidence_gate import assess_explicit_answer
from campanario.chat.local_library import _fold, _normal

logger = logging.getLogger(__name__)
_BOOK = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,160}$')
_BLOCKED_TAGS = frozenset({
    'script', 'style', 'noscript', 'template', 'nav', 'footer', 'header',
    'aside', 'figure', 'figcaption', 'table', 'form', 'svg', 'math',
})
# Registered agent names can be vocatives with or without punctuation.
# Both forms ("Todd, quem é X?" and "todd quem é X?") must preserve
# the SAME offline evidence requirements. Do not accept arbitrary names here.
_VOCATIVE = r'(?:(?:morgana|todd|campan[aá]rio)(?:\s*[,!:]\s*|\s+))?'
_SUBJECT = re.compile(
    r'^\s*' + _VOCATIVE +
    r'(?:quem\s+(?:[eé]|foi|era)\s+|o\s+que\s+(?:[eé]|foi)\s+|'
    r'me\s+(?:fale|cont[ae]|explique)\s+sobre\s+)(.{2,100})[?!. ]*$',
    re.IGNORECASE,
)


class _ArticleParagraphs(HTMLParser):
    """Bounded extraction of visible article paragraphs, ignoring UI/JS/CSS."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._ignored: list[str] = []
        self._in_p = False
        self._in_h1 = False
        self._p: list[str] = []
        self._h1: list[str] = []
        self.paragraphs: list[str] = []
        self.heading = ''

    def handle_starttag(self, tag, attrs):
        if tag in _BLOCKED_TAGS:
            self._ignored.append(tag)
        elif not self._ignored:
            if tag == 'p' and not self._in_p:
                self._p, self._in_p = [], True
            elif tag == 'h1' and not self._in_h1:
                self._h1, self._in_h1 = [], True

    def handle_endtag(self, tag):
        if self._ignored:
            if tag == self._ignored[-1]:
                self._ignored.pop()
            return
        if tag == 'p' and self._in_p:
            sentence = ' '.join(' '.join(self._p).split())
            if 45 <= len(sentence) <= 5000 and len(self.paragraphs) < 30:
                self.paragraphs.append(sentence)
            self._p, self._in_p = [], False
        elif tag == 'h1' and self._in_h1:
            self.heading = ' '.join(' '.join(self._h1).split())[:180]
            self._in_h1 = False

    def handle_data(self, data):
        if self._ignored:
            return
        if self._in_p:
            self._p.append(data)
        if self._in_h1:
            self._h1.append(data)


@dataclass(frozen=True, slots=True)
class ZimFactSheet:
    subject: str
    query: str
    title: str
    book: str
    file_name: str
    locator: str
    excerpt: str
    excerpt_sha256: str
    status: str = 'grounded'
    source_kind: str = 'zim'
    searches: int = 1
    read_count: int = 1
    candidates: tuple[str, ...] = ()

    @property
    def requires_abstention(self) -> bool:
        return False

    @property
    def note(self) -> str:
        # Source quotations are not prompt instructions; the neutral fact sheet
        # gives only provenance to agents, never raw page text as instructions.
        return (f'WIKIPEDIA OFFLINE: leitura do artigo {self.title!r} '
                f'no ZIM {self.file_name!r}; apenas fonte local, '
                'nao uma verificacao independente de verdade.')

    @property
    def verified_answer(self) -> str:
        return (f'Segundo a Wikipédia offline, no artigo “{self.title}”:\n\n'
                f'“{self.excerpt}”\n\n'
                f'Fonte: {self.file_name} — {self.locator}\n'
                'Este trecho é uma citação do arquivo local, não uma verificação independente.')


def _article_path(raw: str) -> str | None:
    if not isinstance(raw, str) or not (1 <= len(raw) <= 260):
        return None
    decoded = unquote(raw)
    if any(c in decoded for c in ('\\', '?', '#', '\x00', '\r', '\n')):
        return None
    parts = decoded.split('/')
    if any(part in ('', '.', '..') or ':' in part for part in parts):
        return None
    return '/'.join(quote(part, safe='-_().~') for part in parts)


def _requested_subject(question: str, subject: str) -> str:
    explicit = subject.strip(' \t\r\n?!.,;:')
    if explicit and len(explicit) <= 100:
        return explicit
    match = _SUBJECT.fullmatch(question.strip())
    return match.group(1).strip(' \t\r\n?!.,;:') if match else ''


class OfflineWikipediaZim:
    """Only responds from an exact-title, actually retrieved local ZIM article.

    Title suggestions are used for discovery only.  An exact article is fetched
    via /raw, its heading is checked and a paragraph must satisfy the existing
    deterministic evidence gate.  Otherwise this reader returns None.
    """

    def __init__(self, zim_dir: Path, *, base_url: str = 'http://127.0.0.1:8181',
                 book_name: str = '', timeout_seconds: float = 3.0,
                 transport: httpx.BaseTransport | None = None):
        url = urlsplit(base_url)
        if (url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost')
                or url.username or url.password or url.path not in ('', '/')
                or url.query or url.fragment or url.port is None):
            raise ValueError('Kiwix deve usar HTTP local em 127.0.0.1/localhost com porta explicita')
        if book_name and not _BOOK.fullmatch(book_name):
            raise ValueError('nome do ZIM invalido')
        self.zim_dir = Path(zim_dir)
        self.base_url = f'http://127.0.0.1:{url.port}'  # no DNS, proxy, or remote host
        self.book_name = book_name
        self.timeout_seconds = max(0.5, min(float(timeout_seconds), 8.0))
        self.transport = transport
        self.last_status = 'not_started'

    def _book(self) -> tuple[str, str] | None:
        if not self.zim_dir.is_dir():
            self.last_status = 'no_zim_directory'
            return None
        zims = sorted((path for path in self.zim_dir.glob('wikipedia_pt*.zim')
                       if path.is_file()), reverse=True)
        if not zims:
            self.last_status = 'no_wikipedia_pt_zim'
            return None
        archive = zims[0]
        book = self.book_name or archive.stem
        if not _BOOK.fullmatch(book):
            self.last_status = 'bad_zim_name'
            return None
        return book, archive.name

    @staticmethod
    def _fetch(client: httpx.Client, path: str, *, params=None,
               max_bytes: int = 256_000) -> httpx.Response | None:
        # Disable redirects and stream bounded content (a multi-GB ZIM article
        # must not cause unbounded reading). Client is locked to loopback.
        with client.stream('GET', path, params=params) as response:
            if response.status_code != 200:
                return None
            length = response.headers.get('content-length', '')
            if length.isdigit() and int(length) > max_bytes:
                return None
            data = bytearray()
            for block in response.iter_bytes():
                data.extend(block)
                if len(data) > max_bytes:
                    return None
            # iter_bytes() already applies HTTP Content-Encoding decompression.
            # Reusing the original Content-Encoding header here would make
            # httpx try to decompress the same bytes a SECOND time, raising
            # DecodingError for legitimate gzip/deflate replies from Kiwix.
            # Content-Length likewise describes the old *encoded* body.
            content_type = response.headers.get('content-type')
            safe_headers = {'content-type': content_type} if content_type else {}
            return httpx.Response(200, content=bytes(data), headers=safe_headers)

    def search(self, question: str, *, subject: str = '') -> ZimFactSheet | None:
        target = _requested_subject(question, subject)
        if not (3 <= len(target) <= 100) or not re.search(r'\w', target):
            self.last_status = 'question_without_specific_title'
            return None
        # Do not send private user messages or arbitrary complete prompts to
        # the Kiwix process; only the public article subject is sent.
        selection = self._book()
        if selection is None:
            return None
        book, file_name = selection
        try:
            with httpx.Client(base_url=self.base_url, follow_redirects=False,
                              trust_env=False, timeout=self.timeout_seconds,
                              transport=self.transport) as client:
                response = self._fetch(client, '/suggest',
                                       params={'content': book, 'term': target, 'count': 8})
                if response is None:
                    self.last_status = 'suggest_unavailable'
                    return None
                suggestions = response.json()
                if not isinstance(suggestions, list):
                    self.last_status = 'invalid_suggestions'
                    return None
                matches = [item for item in suggestions[:20]
                           if (isinstance(item, dict) and item.get('kind') == 'path'
                               and isinstance(item.get('value'), str)
                               and _normal(item['value']) == _normal(target)
                               and _article_path(item.get('path')) is not None)]
                if len(matches) != 1:
                    self.last_status = 'no_unique_exact_title'
                    return None
                title = matches[0]['value'].strip()
                path = _article_path(matches[0]['path'])
                assert path is not None
                locator = f'{self.base_url}/raw/{quote(book, safe="")}/content/{path}'
                page = self._fetch(client, f'/raw/{quote(book, safe="")}/content/{path}')
                if page is None or 'html' not in page.headers.get('content-type', '').lower():
                    self.last_status = 'article_unavailable'
                    return None
                parser = _ArticleParagraphs()
                parser.feed(page.text)
                if parser.heading and _normal(parser.heading) != _normal(target):
                    self.last_status = 'article_heading_mismatch'
                    return None
                # A pure identity question ('Quem foi Ada Lovelace?') has no
                # attribute after the title is removed by the general gate.
                # Such questions require an exact-title page AND a literal
                # identity predicate next to the person's full name.
                identity_question = bool(re.match(
                    r'^\s*' + _VOCATIVE +
                    r'(?:quem\s+(?:[eé]|foi|era)|o\s+que\s+(?:[eé]|foi))\s+',
                    question, re.I))
                for paragraph in parser.paragraphs:
                    excerpt = paragraph[:1050].strip()
                    identity_supported = (
                        identity_question and _normal(target) in _normal(excerpt[:450])
                        and bool(re.search(r'\b(?:foi|era|[eé]|nasceu)\b',
                                           _fold(excerpt[:450]))))
                    if (identity_supported or assess_explicit_answer(
                            question, target, excerpt, title).sufficient):
                        self.last_status = 'grounded_local_zim'
                        return ZimFactSheet(
                            subject=target, query=question, title=title,
                            book=book, file_name=file_name, locator=locator,
                            excerpt=excerpt,
                            excerpt_sha256=sha256(excerpt.encode('utf-8')).hexdigest(),
                        )
                self.last_status = 'no_explicit_evidence'
                return None
        except (httpx.HTTPError, ValueError, TypeError, OSError, UnicodeError) as exc:
            logger.warning('wikipedia_zim_unavailable error_type=%s', type(exc).__name__)
            self.last_status = 'local_kiwix_error'
            return None
