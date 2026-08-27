"""Extração de datas via EXIF, Hachoir, Regex e Sistema de Arquivos."""
import os
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

from organizador.config import PADROES_REGEX_DATA

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_DISPONIVEL = True
except ImportError:
    HEIF_DISPONIVEL = False

try:
    import hachoir.core.log
    hachoir.core.log.log.use_print = False
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_DISPONIVEL = True
except ImportError:
    HACHOIR_DISPONIVEL = False


def extrair_data_do_nome(nome_arquivo):
    ano_atual = datetime.now().year
    nome_base, _ = os.path.splitext(nome_arquivo)

    for regex, fmt in PADROES_REGEX_DATA:
        match = regex.search(nome_base)
        if match:
            texto_data = "".join(match.groups())
            try:
                dt = datetime.strptime(texto_data, fmt)
                if 1990 <= dt.year <= ano_atual:
                    return dt
            except ValueError:
                continue
    return None


def obter_data_exif(caminho_arquivo):
    try:
        imagem = Image.open(caminho_arquivo)
        dados_exif = imagem._getexif()
        if not dados_exif:
            return None
        for tag_id, valor in dados_exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag in ("DateTimeOriginal", "DateTimeDigitized"):
                if isinstance(valor, str):
                    try:
                        return datetime.strptime(valor.strip(), "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        continue
    except Exception:
        return None
    return None


def obter_data_video(caminho_arquivo):
    if not HACHOIR_DISPONIVEL:
        return None
    try:
        parser = createParser(caminho_arquivo)
        if not parser:
            return None
        with parser:
            metadados = extractMetadata(parser)
        if not metadados:
            return None
        if metadados.has("creation_date"):
            valor = metadados.get("creation_date")
            if isinstance(valor, datetime):
                return valor
    except Exception:
        return None
    return None


def obter_data_arquivo(caminho_arquivo):
    timestamp = os.path.getmtime(caminho_arquivo)
    return datetime.fromtimestamp(timestamp)


def extrair_data_inteligente(caminho_arquivo, eh_foto):
    nome_arquivo = os.path.basename(caminho_arquivo)

    if eh_foto:
        data = obter_data_exif(caminho_arquivo)
        if data:
            return data, "EXIF"
    else:
        data = obter_data_video(caminho_arquivo)
        if data:
            return data, "Metadados de Vídeo"

    data_nome = extrair_data_do_nome(nome_arquivo)
    if data_nome:
        return data_nome, "Nome do Arquivo (Regex)"

    return obter_data_arquivo(caminho_arquivo), "Data do Arquivo (SO)"