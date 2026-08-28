"""Motor de varredura, deduplicação, organização e geração de relatórios."""
import os
import time
import shutil
from datetime import datetime

from organizador.config import EXTENSOES_FOTO, EXTENSOES_VALIDAS, ARQUIVOS_IGNORADOS, NOMES_MESES
from organizador.utils import (
    obter_tamanho, calcular_hash_parcial, calcular_hash_completo,
    formatar_bytes, formatar_segundos
)
from organizador.metadata import extrair_data_inteligente


def construir_indice_existentes(pasta_destino):
    indice = {}
    if not os.path.isdir(pasta_destino):
        return indice

    for pasta_atual, _subpastas, arquivos in os.walk(pasta_destino):
        if "_Duplicatas" in pasta_atual:
            continue
        for nome_arquivo in arquivos:
            caminho_completo = os.path.join(pasta_atual, nome_arquivo)
            tamanho = obter_tamanho(caminho_completo)
            if tamanho <= 0:
                continue

            if tamanho not in indice:
                indice[tamanho] = []

            indice[tamanho].append({
                "caminho": caminho_completo,
                "hash_parcial": None,
                "hash_completo": None
            })
    return indice


def eh_duplicado(caminho_origem, indice_destino):
    tamanho = obter_tamanho(caminho_origem)
    if tamanho <= 0 or tamanho not in indice_destino:
        return False, None

    candidatos = indice_destino[tamanho]
    hash_parcial_origem = calcular_hash_parcial(caminho_origem)
    if not hash_parcial_origem:
        return False, None

    hash_comp_origem = None

    for item in candidatos:
        if item["hash_parcial"] is None:
            item["hash_parcial"] = calcular_hash_parcial(item["caminho"])

        if item["hash_parcial"] == hash_parcial_origem:
            if hash_comp_origem is None:
                hash_comp_origem = calcular_hash_completo(caminho_origem)

            if item["hash_completo"] is None:
                item["hash_completo"] = calcular_hash_completo(item["caminho"])

            if item["hash_completo"] == hash_comp_origem:
                return True, item["caminho"]

    return False, None


def analisar_pasta_origem(pasta_origem, pasta_destino):
    total_arquivos = 0
    total_bytes = 0
    pastas_vistas = set()

    for pasta_atual, _subpastas, arquivos in os.walk(pasta_origem):
        if os.path.abspath(pasta_atual).startswith(os.path.abspath(pasta_destino)):
            continue
        pastas_vistas.add(pasta_atual)
        for nome_arquivo in arquivos:
            if nome_arquivo.lower() in ARQUIVOS_IGNORADOS:
                continue
            if nome_arquivo.lower().endswith(EXTENSOES_VALIDAS):
                total_arquivos += 1
                caminho = os.path.join(pasta_atual, nome_arquivo)
                tamanho = obter_tamanho(caminho)
                if tamanho > 0:
                    total_bytes += tamanho

    return total_arquivos, total_bytes, len(pastas_vistas)


def gerar_texto_relatorio(stats):
    origem_exif = stats.get("fontes_data", {}).get("EXIF", 0)
    origem_video = stats.get("fontes_data", {}).get("Metadados de Vídeo", 0)
    origem_regex = stats.get("fontes_data", {}).get("Nome do Arquivo (Regex)", 0)
    origem_fs = stats.get("fontes_data", {}).get("Data do Arquivo (SO)", 0)
    total_org = stats.get("organizados", 0)

    p_exif = (origem_exif / total_org * 100) if total_org > 0 else 0
    p_vid = (origem_video / total_org * 100) if total_org > 0 else 0
    p_reg = (origem_regex / total_org * 100) if total_org > 0 else 0
    p_fs = (origem_fs / total_org * 100) if total_org > 0 else 0

    dist_linhas = []
    for ano in sorted(stats.get("distribuicao_anos", {}).keys()):
        item = stats["distribuicao_anos"][ano]
        dist_linhas.append(f"  {ano}: {item['qtd']} arquivos ({formatar_bytes(item['bytes'])})")
    dist_txt = "\n".join(dist_linhas) if dist_linhas else "  Nenhum dado distribuído."
    simulacao = stats.get("simulacao", False)
    titulo_status = "PREVISÃO — NENHUMA ALTERAÇÃO FOI FEITA" if simulacao else "EXECUÇÃO REAL"
    rotulo_organizados = "Arquivos que seriam organizados" if simulacao else "Arquivos organizados com sucesso"
    rotulo_espaco = "Espaço previsto no destino" if simulacao else "Espaço ocupado no destino"
    rotulo_distribuicao = "DISTRIBUIÇÃO PREVISTA POR ANO" if simulacao else "DISTRIBUIÇÃO POR ANO NO DESTINO"

    return f"""======================================================================
RELATÓRIO DE ORGANIZAÇÃO — ANTES & DEPOIS
Data da Execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Tempo Total: {formatar_segundos(stats.get('tempo_total', 0))} | Modo: {stats.get('modo', '').upper()}
STATUS: {titulo_status}
======================================================================

[1] COMPARAÇÃO ANTES vs. DEPOIS
----------------------------------------------------------------------
Métrica                 | Antes (Origem)       | Depois (Destino)
----------------------------------------------------------------------
Total de Arquivos       | {stats.get('origem_total_arq', 0):<20} | {stats.get('organizados', 0)}
{rotulo_espaco:<24} | {formatar_bytes(stats.get('origem_total_bytes', 0)):<20} | {formatar_bytes(stats.get('espaco_destino_necessario', 0))}
Espaço Economizado      | —                    | {formatar_bytes(stats.get('bytes_economizados', 0))} (duplicatas)
Pastas Mapeadas         | {stats.get('origem_qtd_pastas', 0):<20} | {len(stats.get('distribuicao_anos', {}))} anos organizados
Conflitos de destino    | —                    | {len(stats.get('conflitos', []))}

[2] STATUS DO PROCESSAMENTO
----------------------------------------------------------------------
* {rotulo_organizados}: {stats.get('organizados', 0)}
  - Fotos: {stats.get('fotos', 0)}
  - Vídeos: {stats.get('videos', 0)}
* Duplicatas identificadas: {stats.get('duplicados', 0)} (Ação: {stats.get('acao_duplicata', '')})
* Erros encontrados: {stats.get('erros', 0)}
* Espaço estimado necessário: {formatar_bytes(stats.get('espaco_destino_necessario', 0))}

[3] PRECISÃO E ORIGEM DA DATA DETECTADA
----------------------------------------------------------------------
* Metadados Reais de Foto (EXIF): {origem_exif} ({p_exif:.1f}%)
* Metadados de Vídeo: {origem_video} ({p_vid:.1f}%)
* Nome do Arquivo (Regex / WhatsApp / etc.): {origem_regex} ({p_reg:.1f}%)
* Data do Sistema de Arquivos (Fallback SO): {origem_fs} ({p_fs:.1f}%)

[4] {rotulo_distribuicao}
----------------------------------------------------------------------
{dist_txt}
======================================================================
"""


def processar_organizacao(pasta_origem, pasta_destino, organizar_por_mes, separar_por_tipo,
                          renomear_arquivos, modo, verificar_duplicatas, acao_duplicata,
                          callback_log, callback_progresso, callback_concluido, deve_parar,
                          simulacao=False):
    if simulacao:
        callback_log("MODO SIMULAÇÃO: nenhum arquivo ou relatório será alterado.")
    else:
        os.makedirs(pasta_destino, exist_ok=True)
    callback_log("Mapeando arquivos e estrutura da pasta de origem...")
    total_esperado, origem_bytes, origem_pastas = analisar_pasta_origem(pasta_origem, pasta_destino)

    tempo_inicio = time.time()
    total = 0
    organizados = 0
    duplicados = 0
    erros = 0
    fotos = 0
    videos = 0
    bytes_organizados = 0
    bytes_economizados = 0
    espaco_destino_necessario = 0

    fontes_data = {
        "EXIF": 0, "Metadados de Vídeo": 0,
        "Nome do Arquivo (Regex)": 0, "Data do Arquivo (SO)": 0
    }
    distribuicao_anos = {}
    registro_duplicatas = []
    destinos_simulados = set()
    plano_operacoes = []
    conflitos = []

    pasta_duplicatas = os.path.join(pasta_destino, "_Duplicatas")
    if verificar_duplicatas and acao_duplicata == "Isolar na pasta '_Duplicatas'" and not simulacao:
        os.makedirs(pasta_duplicatas, exist_ok=True)

    indice_vistos = {}
    if verificar_duplicatas:
        callback_log("Construindo índice de arquivos existentes no destino...")
        indice_vistos = construir_indice_existentes(pasta_destino)

    for pasta_atual, _subpastas, arquivos in os.walk(pasta_origem):
        if os.path.abspath(pasta_atual).startswith(os.path.abspath(pasta_destino)):
            continue

        for nome_arquivo in arquivos:
            if deve_parar():
                tempo_decorrido = time.time() - tempo_inicio
                callback_log(f"\nProcesso interrompido pelo usuário. Tempo decorrido: {formatar_segundos(tempo_decorrido)}")
                return

            if nome_arquivo.lower() in ARQUIVOS_IGNORADOS:
                continue

            caminho_completo = os.path.join(pasta_atual, nome_arquivo)
            if not nome_arquivo.lower().endswith(EXTENSOES_VALIDAS):
                continue

            total += 1
            tamanho_atual = obter_tamanho(caminho_completo)

            tempo_passado = time.time() - tempo_inicio
            velocidade = total / tempo_passado if tempo_passado > 0 else 0
            tempo_restante = (total_esperado - total) / velocidade if velocidade > 0 else 0
            callback_progresso(total, total_esperado, tempo_restante)

            if verificar_duplicatas:
                duplicado, caminho_existente = eh_duplicado(caminho_completo, indice_vistos)
                if duplicado:
                    duplicados += 1
                    if tamanho_atual > 0:
                        bytes_economizados += tamanho_atual
                    caminho_relativo = os.path.relpath(caminho_completo, pasta_origem)

                    if acao_duplicata == "Isolar na pasta '_Duplicatas'":
                        dest_dup = os.path.join(pasta_duplicatas, nome_arquivo)
                        cnt = 1
                        base_d, ext_d = os.path.splitext(nome_arquivo)
                        while os.path.exists(dest_dup) or dest_dup in destinos_simulados:
                            dest_dup = os.path.join(pasta_duplicatas, f"{base_d}_{cnt}{ext_d}")
                            cnt += 1
                        try:
                            if simulacao:
                                callback_log(f"[SIMULAÇÃO: duplicado -> _Duplicatas] {caminho_relativo}")
                                destinos_simulados.add(dest_dup)
                                espaco_destino_necessario += tamanho_atual
                                plano_operacoes.append({
                                    "acao": f"{modo} duplicado",
                                    "origem": caminho_completo,
                                    "destino": dest_dup,
                                    "status": "simulado"
                                })
                            elif modo == "mover":
                                shutil.move(caminho_completo, dest_dup)
                                espaco_destino_necessario += tamanho_atual
                                plano_operacoes.append({
                                    "acao": "mover duplicado",
                                    "origem": caminho_completo,
                                    "destino": dest_dup,
                                    "status": "executado"
                                })
                                callback_log(f"[duplicado -> _Duplicatas] {caminho_relativo}")
                            else:
                                shutil.copy2(caminho_completo, dest_dup)
                                espaco_destino_necessario += tamanho_atual
                                plano_operacoes.append({
                                    "acao": "copiar duplicado",
                                    "origem": caminho_completo,
                                    "destino": dest_dup,
                                    "status": "executado"
                                })
                                callback_log(f"[duplicado -> _Duplicatas] {caminho_relativo}")
                        except Exception as e:
                            callback_log(f"Erro ao isolar duplicata {nome_arquivo}: {e}")

                    elif acao_duplicata == "Registrar em 'duplicatas.txt'":
                        registro_duplicatas.append(f"ORIGEM: {caminho_completo}\nIDÊNTICO A: {caminho_existente}\n" + "-"*40)
                        plano_operacoes.append({
                            "acao": "registrar duplicado",
                            "origem": caminho_completo,
                            "destino": os.path.join(pasta_destino, "duplicatas_encontradas.txt"),
                            "status": "simulado" if simulacao else "executado"
                        })
                        callback_log(f"[duplicado registrado] {caminho_relativo}")
                    else:
                        plano_operacoes.append({
                            "acao": "ignorar duplicado",
                            "origem": caminho_completo,
                            "destino": caminho_existente,
                            "status": "simulado" if simulacao else "executado"
                        })
                        callback_log(f"[duplicado ignorado] {caminho_relativo}")
                    continue

            extensao_lower = os.path.splitext(nome_arquivo)[1].lower()
            eh_foto = extensao_lower in EXTENSOES_FOTO

            data_arquivo, origem_data = extrair_data_inteligente(caminho_completo, eh_foto)
            fontes_data[origem_data] = fontes_data.get(origem_data, 0) + 1

            ano = str(data_arquivo.year)
            partes_pasta = [pasta_destino, ano]
            if organizar_por_mes:
                partes_pasta.append(NOMES_MESES[data_arquivo.month])
            if separar_por_tipo:
                partes_pasta.append("Fotos" if eh_foto else "Videos")

            pasta_final = os.path.join(*partes_pasta)
            rotulo_pasta = os.path.relpath(pasta_final, pasta_destino)

            if renomear_arquivos:
                prefixo = "IMG" if eh_foto else "VID"
                timestamp_str = data_arquivo.strftime("%Y%m%d_%H%M%S")
                nome_base = f"{prefixo}_{timestamp_str}"
            else:
                nome_base, _ = os.path.splitext(nome_arquivo)

            if not simulacao:
                os.makedirs(pasta_final, exist_ok=True)
            destino_final = os.path.join(pasta_final, f"{nome_base}{extensao_lower}")
            destino_inicial = destino_final

            contador = 1
            while os.path.exists(destino_final) or destino_final in destinos_simulados:
                destino_final = os.path.join(pasta_final, f"{nome_base}_{contador}{extensao_lower}")
                contador += 1

            caminho_relativo = os.path.relpath(caminho_completo, pasta_origem)
            conflito_destino = destino_final != destino_inicial
            if conflito_destino:
                conflito = {
                    "origem": caminho_completo,
                    "destino_original": destino_inicial,
                    "destino_final": destino_final,
                    "motivo": "Nome já existente"
                }
                conflitos.append(conflito)
                callback_log(
                    f"[CONFLITO] {os.path.basename(destino_inicial)} já existe; "
                    f"será usado {os.path.basename(destino_final)}"
                )
            plano_operacoes.append({
                "acao": modo,
                "origem": caminho_completo,
                "destino": destino_final,
                "status": "simulado" if simulacao else "executado",
                "conflito": "sim" if conflito_destino else "não"
            })
            try:
                if simulacao:
                    callback_log(f"[SIMULAÇÃO: {modo}] {rotulo_pasta} <- {caminho_relativo}")
                    destinos_simulados.add(destino_final)
                elif modo == "mover":
                    shutil.move(caminho_completo, destino_final)
                else:
                    shutil.copy2(caminho_completo, destino_final)

                organizados += 1
                if eh_foto:
                    fotos += 1
                else:
                    videos += 1

                if tamanho_atual > 0:
                    bytes_organizados += tamanho_atual
                    espaco_destino_necessario += tamanho_atual

                if ano not in distribuicao_anos:
                    distribuicao_anos[ano] = {"qtd": 0, "bytes": 0}
                distribuicao_anos[ano]["qtd"] += 1
                if tamanho_atual > 0:
                    distribuicao_anos[ano]["bytes"] += tamanho_atual

                if verificar_duplicatas:
                    tam_final = tamanho_atual if simulacao else obter_tamanho(destino_final)
                    if tam_final > 0:
                        if tam_final not in indice_vistos:
                            indice_vistos[tam_final] = []
                        indice_vistos[tam_final].append({
                            "caminho": caminho_completo if simulacao else destino_final,
                            "hash_parcial": None,
                            "hash_completo": None
                        })

                nome_salvo = os.path.basename(destino_final)
                callback_log(f"[{rotulo_pasta}] {caminho_relativo} -> {nome_salvo} ({origem_data})")
            except Exception as e:
                erros += 1
                callback_log(f"ERRO ao processar {nome_arquivo}: {e}")

    tempo_total = time.time() - tempo_inicio

    stats = {
        "origem_total_arq": total_esperado,
        "origem_total_bytes": origem_bytes,
        "origem_qtd_pastas": origem_pastas,
        "organizados": organizados,
        "duplicados": duplicados,
        "acao_duplicata": acao_duplicata if verificar_duplicatas else "Desativada",
        "erros": erros,
        "fotos": fotos,
        "videos": videos,
        "bytes_organizados": bytes_organizados,
        "bytes_economizados": bytes_economizados,
        "espaco_destino_necessario": espaco_destino_necessario,
        "fontes_data": fontes_data,
        "distribuicao_anos": distribuicao_anos,
        "plano_operacoes": plano_operacoes,
        "conflitos": conflitos,
        "tempo_total": tempo_total,
        "modo": f"{modo} (simulação)" if simulacao else modo,
        "simulacao": simulacao,
        "separar_por_tipo": separar_por_tipo,
        "pasta_destino": pasta_destino
    }

    relatorio_texto = gerar_texto_relatorio(stats)

    try:
        if simulacao:
            callback_log("\nRelatório não salvo: execução em modo simulação.")
        else:
            caminho_relatorio = os.path.join(pasta_destino, "relatorio_organizacao.txt")
            with open(caminho_relatorio, "w", encoding="utf-8") as f:
                f.write(relatorio_texto)
            callback_log(f"\nRelatório geral salvo em: {caminho_relatorio}")
    except Exception as e:
        callback_log(f"\nErro ao salvar relatório geral: {e}")

    if not simulacao and registro_duplicatas:
        try:
            caminho_txt_dup = os.path.join(pasta_destino, "duplicatas_encontradas.txt")
            with open(caminho_txt_dup, "w", encoding="utf-8") as f:
                f.write(f"RELATÓRIO DE ARQUIVOS DUPLICADOS ({len(registro_duplicatas)} encontrados)\n")
                f.write("="*60 + "\n\n")
                f.write("\n".join(registro_duplicatas))
            callback_log(f"Lista de duplicatas salva em: {caminho_txt_dup}")
        except Exception as e:
            callback_log(f"Erro ao salvar lista de duplicatas: {e}")

    callback_log(relatorio_texto)
    callback_concluido(stats)