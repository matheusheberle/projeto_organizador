"""Utilitários para formatação de texto e cálculo de hashes."""
import os
import hashlib

def formatar_segundos(segundos):
    segundos = int(segundos)
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    if horas > 0:
        return f"{horas:02d}h {minutos:02d}m {segs:02d}s"
    elif minutos > 0:
        return f"{minutos:02d}m {segs:02d}s"
    return f"{segs}s"


def formatar_bytes(tamanho_bytes):
    for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
        if tamanho_bytes < 1024.0:
            return f"{tamanho_bytes:.2f} {unidade}"
        tamanho_bytes /= 1024.0
    return f"{tamanho_bytes:.2f} PB"


def obter_tamanho(caminho_arquivo):
    try:
        return os.path.getsize(caminho_arquivo)
    except Exception:
        return -1


def calcular_hash_parcial(caminho_arquivo, tamanho_bloco=65536):
    hash_md5 = hashlib.md5()
    try:
        with open(caminho_arquivo, "rb") as f:
            bloco = f.read(tamanho_bloco)
            hash_md5.update(bloco)
        return hash_md5.hexdigest()
    except Exception:
        return None


def calcular_hash_completo(caminho_arquivo, tamanho_bloco=65536):
    hash_md5 = hashlib.md5()
    try:
        with open(caminho_arquivo, "rb") as f:
            for bloco in iter(lambda: f.read(tamanho_bloco), b""):
                hash_md5.update(bloco)
        return hash_md5.hexdigest()
    except Exception:
        return None