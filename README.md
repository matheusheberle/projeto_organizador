# Organizador de Fotos e Vídeos 📸🎬

Aplicação desktop em Python com interface gráfica (Tkinter) para organização cronológica inteligente de arquivos de mídia (fotos e vídeos) e eliminação/isolamento de duplicatas binárias.

---

## 🚀 Funcionalidades

- **Motor em Cascata de Detecção de Datas:**
  1. **Metadados Nativos:** Extração de data EXIF para imagens e metadados de contêiner para vídeos via `hachoir`.
  2. **Regex no Nome do Arquivo:** Reconhecimento de padrões de mensageiros (WhatsApp, Telegram), capturas de tela e câmeras Android.
  3. **Sistema de Arquivos:** Fallback seguro para data de modificação (`mtime`).
- **Deduplicação Binária Rápida em 3 Camadas:**
  - Verificação por tamanho exato em bytes.
  - Hash MD5 parcial (primeiros 64 KB).
  - Hash MD5 completo para confirmação de duplicatas idênticas.
- **Opções Flexíveis de Organização:**
  - Organização por Ano e Mês (`YYYY/MM - NomeDoMes/`).
  - Separação opcional em subpastas `Fotos/` e `Videos/`.
  - Padronização de nomes (`IMG_YYYYMMDD_HHMMSS` / `VID_YYYYMMDD_HHMMSS`).
  - Modos de operação: **Copiar** ou **Mover**.
- **Gestão de Duplicatas:** Ignorar, isolar em pasta dedicada (`_Duplicatas/`) ou exportar para log (`duplicatas_encontradas.txt`).
- **Auditoria "Antes & Depois":** Relatório visual completo com métricas de espaço economizado, fontes de metadados e distribuição temporal.

---

## 🛠️ Tecnologias e Dependências

- Python 3.10+
- `Pillow` (Processamento de imagens e EXIF)
- `pillow-heif` (Suporte a imagens HEIC/HEIF da Apple)
- `hachoir` (Extração de metadados de arquivos de vídeo)
- `Tkinter` (Interface gráfica nativa)

---

## 📦 Como Instalar e Rodar

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
   cd projeto_organizador
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação:**
   ```bash
   python main.py
   ```