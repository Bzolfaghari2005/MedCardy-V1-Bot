"""Analyze uploaded order files for page counts based on file structure."""
import logging
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DOCX_PAGES_NS = '{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}'


@dataclass
class FileAnalysisResult:
    page_count: int
    analysis_method: str  # pdf | docx | image | fallback


def analyze_file(file_path: str | Path, file_name: str = '') -> FileAnalysisResult:
    path = Path(file_path)
    name = (file_name or path.name).lower()

    if name.endswith('.pdf'):
        return _analyze_pdf(path)
    if name.endswith('.docx'):
        return _analyze_docx(path)
    if _is_image(name):
        return FileAnalysisResult(page_count=1, analysis_method='image')
    return FileAnalysisResult(page_count=0, analysis_method='fallback')


def _is_image(name: str) -> bool:
    return any(name.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'))


def _analyze_pdf(path: Path) -> FileAnalysisResult:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        page_count = len(reader.pages) or 1
        return FileAnalysisResult(page_count=page_count, analysis_method='pdf')
    except Exception:
        logger.exception('PDF analysis failed for %s', path)
        return FileAnalysisResult(page_count=0, analysis_method='fallback')


def _read_docx_pages_from_metadata(path: Path) -> int | None:
    try:
        with zipfile.ZipFile(path) as archive:
            if 'docProps/app.xml' not in archive.namelist():
                return None
            root = ET.fromstring(archive.read('docProps/app.xml'))
            pages_elem = root.find(f'.//{DOCX_PAGES_NS}Pages')
            if pages_elem is not None and pages_elem.text and pages_elem.text.isdigit():
                count = int(pages_elem.text)
                return count if count > 0 else None
    except Exception:
        logger.debug('Could not read DOCX page metadata from %s', path, exc_info=True)
    return None


def _count_docx_page_breaks(path: Path) -> int:
    from docx import Document
    from docx.oxml.ns import qn

    doc = Document(str(path))
    page_breaks = 0
    for br in doc.element.body.iter(qn('w:br')):
        if br.get(qn('w:type')) == 'page':
            page_breaks += 1
    return max(1, page_breaks + 1)


def _analyze_docx(path: Path) -> FileAnalysisResult:
    try:
        page_count = _read_docx_pages_from_metadata(path)
        if page_count is None:
            page_count = _count_docx_page_breaks(path)
        return FileAnalysisResult(page_count=page_count, analysis_method='docx')
    except Exception:
        logger.exception('DOCX analysis failed for %s', path)
        return FileAnalysisResult(page_count=0, analysis_method='fallback')
