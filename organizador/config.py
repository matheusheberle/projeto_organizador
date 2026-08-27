"""Constantes, mapeamentos de extensões e expressões regulares."""
import re

EXTENSOES_FOTO = (
    ".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp", ".webp", ".gif",
    ".thm", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2",
)

EXTENSOES_VIDEO = (
    ".mp4", ".mov", ".avi", ".mkv", ".m4v", ".3gp",
    ".mpg", ".mpeg", ".wmv", ".mts", ".m2ts", ".vob",
    ".webm", ".flv", ".rmvb", ".ts", ".asf",
)

EXTENSOES_VALIDAS = EXTENSOES_FOTO + EXTENSOES_VIDEO

ARQUIVOS_IGNORADOS = (
    "thumbs.db", ".ds_store", "desktop.ini",
    ".sfap0", ".scc", ".tmp"
)

NOMES_MESES = {
    1: "01 - Janeiro", 2: "02 - Fevereiro", 3: "03 - Marco", 4: "04 - Abril",
    5: "05 - Maio", 6: "06 - Junho", 7: "07 - Julho", 8: "08 - Agosto",
    9: "09 - Setembro", 10: "10 - Outubro", 11: "11 - Novembro", 12: "12 - Dezembro",
}

PADROES_REGEX_DATA = [
    (re.compile(r'(?:IMG|VID|AUD|DOC)[-_](\d{4})(\d{2})(\d{2})[-_]WA', re.IGNORECASE), "%Y%m%d"),
    (re.compile(r'(?:IMG|VID|PANO|PHOTO|VIDE)?[_-]?(\d{4})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})', re.IGNORECASE), "%Y%m%d%H%M%S"),
    (re.compile(r'(?:Screenshot|Captura|Screen)[_-](\d{4})[-_](\d{2})[-_](\d{2})[-_ ](\d{2})[-_.]?(\d{2})[-_.]?(\d{2})', re.IGNORECASE), "%Y%m%d%H%M%S"),
    (re.compile(r'(\d{4})[-.](\d{2})[-.](\d{2})[_-](\d{2})[-.](\d{2})[-.](\d{2})'), "%Y%m%d%H%M%S"),
    (re.compile(r'(?:^|[_-])(\d{4})(\d{2})(\d{2})(?:[_-]|$)'), "%Y%m%d"),
    (re.compile(r'(\d{4})-(\d{2})-(\d{2})'), "%Y%m%d"),
]