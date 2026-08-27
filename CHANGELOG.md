# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.
O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2026-08-27

### Adicionado
- **Arquitetura Modular:** Separação do código em pacote `organizador/` (`config`, `utils`, `metadata`, `engine`, `gui`).
- **Motor de Data em Cascata:**
  1. Metadados Nativos (EXIF para fotos e Hachoir para vídeos).
  2. Extração via Regex no nome do arquivo (WhatsApp, Telegram, Screenshots, Câmeras).
  3. Fallback seguro para data de modificação do sistema operacional.
- **Suporte Expandido de Mídia:** Suporte a dezenas de formatos de imagem (incluindo RAWs), suporte opcional a `.heic` via `pillow-heif`, e formatos de vídeo legados (`.mpg`, `.wmv`, `.vob`, `.mts`).
- **Deduplicação Binária em 3 Camadas:** Verificação por tamanho exato, hash parcial (64 KB) e hash completo MD5.
- **Ações para Duplicatas:** Opções de ignorar, isolar na pasta `_Duplicatas` ou exportar para `duplicatas_encontradas.txt`.
- **Interface Gráfica Tkinter:** Aba de execução com barra de progresso, cálculo de velocidade, estimativa de tempo (ETA) e aba dedicada para relatório "Antes & Depois".

## [1.1.0] - 2026-08-27

### Adicionado
- **Destino sugerido:** ao informar a pasta de origem, a aplicação sugere uma pasta vizinha com o sufixo `_Organizado`.
- A sugestão é preservada enquanto o usuário não definir um destino manualmente.