"""Interface Gráfica com Tkinter e visualização de Antes e Depois."""
import csv
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from organizador import __version__
from organizador.utils import formatar_segundos, formatar_bytes
from organizador.metadata import HACHOIR_DISPONIVEL, HEIF_DISPONIVEL
from organizador.engine import processar_organizacao, gerar_texto_relatorio


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"Organizador de Fotos e Vídeos v{__version__}")
        self.geometry("740x720")
        self.resizable(True, True)

        self.pasta_origem = tk.StringVar()
        self.pasta_destino = tk.StringVar()
        self.organizar_por_mes = tk.BooleanVar(value=True)
        self.separar_por_tipo = tk.BooleanVar(value=False)
        self.renomear_arquivos = tk.BooleanVar(value=False)
        self.modo_mover = tk.BooleanVar(value=False)
        self.verificar_duplicatas = tk.BooleanVar(value=True)
        self.acao_duplicata = tk.StringVar(value="Ignorar (Apenas pular)")

        self._parar_flag = False
        self._thread_em_execucao = None
        self._historico_log = []
        self._stats_ultimo_relatorio = None
        self.filtro_log = tk.StringVar(value="Todos")

        self._montar_interface()

    def _montar_interface(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.aba_execucao = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_execucao, text=" Organização ")

        self.aba_relatorio = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_relatorio, text=" Relatório Antes & Depois ")

        self._montar_aba_execucao()
        self._montar_aba_relatorio()

    def _montar_aba_execucao(self):
        padding = {"padx": 10, "pady": 4}

        frame_origem = tk.Frame(self.aba_execucao)
        frame_origem.pack(fill="x", **padding)
        tk.Label(frame_origem, text="Pasta de origem:", width=16, anchor="w").pack(side="left")
        tk.Entry(frame_origem, textvariable=self.pasta_origem).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(frame_origem, text="Escolher...", command=self._escolher_origem).pack(side="left")

        frame_destino = tk.Frame(self.aba_execucao)
        frame_destino.pack(fill="x", **padding)
        tk.Label(frame_destino, text="Pasta de destino:", width=16, anchor="w").pack(side="left")
        tk.Entry(frame_destino, textvariable=self.pasta_destino).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(frame_destino, text="Sugerir", command=self._sugerir_destino).pack(side="left", padx=(0, 5))
        tk.Button(frame_destino, text="Escolher...", command=self._escolher_destino).pack(side="left")

        frame_opcoes = tk.LabelFrame(self.aba_execucao, text="Opções de Organização")
        frame_opcoes.pack(fill="x", **padding)

        tk.Checkbutton(
            frame_opcoes, text="Organizar por mês (ex: 2024/03 - Marco/)",
            variable=self.organizar_por_mes
        ).pack(anchor="w", padx=10, pady=2)

        tk.Checkbutton(
            frame_opcoes, text="Separar em subpastas 'Fotos' e 'Videos'",
            variable=self.separar_por_tipo
        ).pack(anchor="w", padx=10, pady=2)

        tk.Checkbutton(
            frame_opcoes, text="Padronizar nomes (ex: IMG_20240315_143022.jpg / VID_...)",
            variable=self.renomear_arquivos
        ).pack(anchor="w", padx=10, pady=2)

        frame_dup = tk.Frame(frame_opcoes)
        frame_dup.pack(fill="x", padx=10, pady=2)

        tk.Checkbutton(
            frame_dup, text="Detectar duplicados:",
            variable=self.verificar_duplicatas,
            command=self._alternar_estado_duplicata
        ).pack(side="left")

        self.combo_duplicatas = ttk.Combobox(
            frame_dup,
            textvariable=self.acao_duplicata,
            values=[
                "Ignorar (Apenas pular)",
                "Isolar na pasta '_Duplicatas'",
                "Registrar em 'duplicatas.txt'"
            ],
            state="readonly",
            width=30
        )
        self.combo_duplicatas.pack(side="left", padx=5)

        tk.Checkbutton(
            frame_opcoes, text="Mover arquivos em vez de copiar (apaga da origem)",
            variable=self.modo_mover, fg="#b71c1c"
        ).pack(anchor="w", padx=10, pady=2)

        if not HACHOIR_DISPONIVEL:
            tk.Label(
                frame_opcoes,
                text="Aviso: 'hachoir' não encontrado. Vídeos dependerão de Regex no nome ou data do SO.",
                fg="#a15c00", wraplength=600, justify="left"
            ).pack(anchor="w", padx=10, pady=(2, 2))

        if not HEIF_DISPONIVEL:
            tk.Label(
                frame_opcoes,
                text="Aviso: 'pillow-heif' não instalado. Fotos .HEIC dependerão de Regex no nome ou data do SO.",
                fg="#a15c00", wraplength=600, justify="left"
            ).pack(anchor="w", padx=10, pady=(0, 4))

        frame_botoes = tk.Frame(self.aba_execucao)
        frame_botoes.pack(fill="x", **padding)
        self.botao_iniciar = tk.Button(
            frame_botoes, text="Iniciar Organização", command=self._iniciar,
            bg="#2e7d32", fg="white", font=("Segoe UI", 10, "bold")
        )
        self.botao_iniciar.pack(side="left", padx=(0, 8))

        self.botao_simular = tk.Button(
            frame_botoes, text="Simular Organização", command=lambda: self._iniciar(simulacao=True),
            bg="#1565c0", fg="white", font=("Segoe UI", 10, "bold")
        )
        self.botao_simular.pack(side="left", padx=(0, 8))

        self.botao_parar = tk.Button(
            frame_botoes, text="Parar", command=self._parar, state="disabled",
            bg="#c62828", fg="white", activebackground="#8e0000",
            activeforeground="white", font=("Segoe UI", 10, "bold")
        )
        self.botao_parar.pack(side="left")

        self.barra_progresso = ttk.Progressbar(self.aba_execucao, mode="determinate")
        self.barra_progresso.pack(fill="x", padx=10, pady=(4, 0))

        self.label_progresso = tk.Label(self.aba_execucao, text="Pronto para começar.")
        self.label_progresso.pack(anchor="w", padx=10)

        frame_log = tk.LabelFrame(self.aba_execucao, text="Atividade")
        frame_log.pack(fill="both", expand=True, **padding)

        frame_filtro = tk.Frame(frame_log)
        frame_filtro.pack(fill="x", padx=5, pady=(5, 2))
        tk.Label(frame_filtro, text="Exibir:").pack(side="left")
        self.combo_filtro_log = ttk.Combobox(
            frame_filtro,
            textvariable=self.filtro_log,
            values=["Todos", "Operações", "Duplicatas", "Conflitos", "Erros"],
            state="readonly",
            width=16
        )
        self.combo_filtro_log.pack(side="left", padx=5)
        self.combo_filtro_log.bind("<<ComboboxSelected>>", self._atualizar_filtro_log)

        self.caixa_log = tk.Text(frame_log, wrap="word", state="disabled", height=10)
        self.caixa_log.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame_log, command=self.caixa_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.caixa_log.configure(yscrollcommand=scrollbar.set)

    def _montar_aba_relatorio(self):
        frame_acoes = tk.Frame(self.aba_relatorio)
        frame_acoes.pack(fill="x", padx=10, pady=(5, 0))
        self.label_status_relatorio = tk.Label(
            frame_acoes, text="Nenhuma execução concluída.", anchor="w",
            font=("Segoe UI", 10, "bold")
        )
        self.label_status_relatorio.pack(side="left", fill="x", expand=True)
        self.botao_exportar_plano = tk.Button(
            frame_acoes, text="Exportar Plano", command=self._exportar_plano,
            state="disabled", bg="#ef6c00", fg="white",
            activebackground="#b53d00", activeforeground="white",
            font=("Segoe UI", 9, "bold")
        )
        self.botao_exportar_plano.pack(side="right")

        frame_tabela = tk.LabelFrame(self.aba_relatorio, text="Comparativo Antes & Depois")
        frame_tabela.pack(fill="x", padx=10, pady=5)

        colunas = ("metrica", "antes", "depois", "resultado")
        self.tabela_resumo = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=5)
        self.tabela_resumo.heading("metrica", text="Métrica")
        self.tabela_resumo.heading("antes", text="Antes (Origem)")
        self.tabela_resumo.heading("depois", text="Depois (Destino)")
        self.tabela_resumo.heading("resultado", text="Ganho / Resultado")

        self.tabela_resumo.column("metrica", width=160)
        self.tabela_resumo.column("antes", width=140)
        self.tabela_resumo.column("depois", width=140)
        self.tabela_resumo.column("resultado", width=220)
        self.tabela_resumo.pack(fill="x", padx=5, pady=5)

        frame_detalhes = tk.LabelFrame(self.aba_relatorio, text="Relatório Completo de Auditoria")
        frame_detalhes.pack(fill="both", expand=True, padx=10, pady=5)

        self.caixa_relatorio_txt = tk.Text(frame_detalhes, wrap="word", font=("Consolas", 9), state="disabled")
        self.caixa_relatorio_txt.pack(side="left", fill="both", expand=True)

        scrollbar_rel = tk.Scrollbar(frame_detalhes, command=self.caixa_relatorio_txt.yview)
        scrollbar_rel.pack(side="right", fill="y")
        self.caixa_relatorio_txt.configure(yscrollcommand=scrollbar_rel.set)

    def _alternar_estado_duplicata(self):
        if self.verificar_duplicatas.get():
            self.combo_duplicatas.config(state="readonly")
        else:
            self.combo_duplicatas.config(state="disabled")

    def _escolher_origem(self):
        caminho = filedialog.askdirectory(title="Escolha a pasta de origem")
        if caminho:
            self.pasta_origem.set(caminho)
            if not self.pasta_destino.get().strip():
                self._sugerir_destino()

    def _sugerir_destino(self):
        origem = self.pasta_origem.get().strip()
        if not origem or not os.path.isdir(origem):
            messagebox.showinfo("Sugestão de destino", "Escolha uma pasta de origem válida primeiro.")
            return

        pasta_origem = os.path.abspath(origem)
        nome_origem = os.path.basename(os.path.normpath(pasta_origem))
        destino = os.path.join(os.path.dirname(pasta_origem), f"{nome_origem}_Organizado")
        self.pasta_destino.set(destino)

    def _escolher_destino(self):
        caminho = filedialog.askdirectory(title="Escolha a pasta de destino")
        if caminho:
            self.pasta_destino.set(caminho)

    def _log(self, mensagem):
        self._historico_log.append(mensagem)
        self.after(0, self._atualizar_caixa_log)

    def _atualizar_caixa_log(self, _evento=None):
        filtro = self.filtro_log.get()

        def deve_exibir(mensagem):
            if filtro == "Todos":
                return True
            if filtro == "Erros":
                return "ERRO" in mensagem.upper()
            if filtro == "Conflitos":
                return "[CONFLITO]" in mensagem
            if filtro == "Duplicatas":
                return "duplicat" in mensagem.lower()
            return "[SIMULAÇÃO:" in mensagem or " -> " in mensagem or " <- " in mensagem

        def atualizar():
            self.caixa_log.configure(state="normal")
            self.caixa_log.delete("1.0", "end")
            for mensagem in self._historico_log:
                if deve_exibir(mensagem):
                    self.caixa_log.insert("end", mensagem + "\n")
            self.caixa_log.see("end")
            self.caixa_log.configure(state="disabled")
        atualizar()

    def _atualizar_filtro_log(self, _evento=None):
        self._atualizar_caixa_log()

    def _progresso(self, atual, total, segundos_restantes):
        def atualizar():
            if total > 0:
                self.barra_progresso["maximum"] = total
                self.barra_progresso["value"] = atual
                eta_texto = formatar_segundos(segundos_restantes)
                self.label_progresso.config(
                    text=f"Processando {atual} de {total} arquivos... (Restante estimado: ~{eta_texto})"
                )
        self.after(0, atualizar)

    def _iniciar(self, simulacao=False):
        origem = self.pasta_origem.get().strip()
        destino = self.pasta_destino.get().strip()

        if not origem or not os.path.isdir(origem):
            messagebox.showerror("Erro", "Escolha uma pasta de origem válida.")
            return
        if not destino:
            messagebox.showerror("Erro", "Escolha uma pasta de destino.")
            return

        if self.modo_mover.get() and not simulacao:
            confirmar = messagebox.askyesno(
                "Atenção",
                "A opção MOVER está ativada. Os arquivos serão retirados da origem permanentemente.\n\nDeseja continuar?"
            )
            if not confirmar:
                return

        self._parar_flag = False
        self.botao_iniciar.config(state="disabled")
        self.botao_simular.config(state="disabled")
        self.botao_parar.config(state="normal")
        self.caixa_log.configure(state="normal")
        self.caixa_log.delete("1.0", "end")
        self.caixa_log.configure(state="disabled")
        self._historico_log.clear()
        self.barra_progresso["value"] = 0
        self.label_progresso.config(text="Iniciando...")

        modo = "mover" if self.modo_mover.get() else "copiar"

        self._thread_em_execucao = threading.Thread(
            target=self._executar_em_thread,
            args=(
                origem, destino, self.organizar_por_mes.get(),
                self.separar_por_tipo.get(), self.renomear_arquivos.get(),
                modo, self.verificar_duplicatas.get(), self.acao_duplicata.get(),
                simulacao
            ),
            daemon=True,
        )
        self._thread_em_execucao.start()

    def _executar_em_thread(self, origem, destino, por_mes, por_tipo, renomear, modo, duplicatas, acao_dup, simulacao):
        try:
            processar_organizacao(
                origem, destino, por_mes, por_tipo, renomear, modo, duplicatas, acao_dup,
                callback_log=self._log,
                callback_progresso=self._progresso,
                callback_concluido=lambda stats: self.after(0, self._exibir_relatorio_final, stats),
                deve_parar=lambda: self._parar_flag,
                simulacao=simulacao,
            )
        except Exception as e:
            self._log(f"ERRO CRÍTICO: {e}")
        finally:
            self.after(0, self._finalizar)

    def _exibir_relatorio_final(self, stats):
        self._stats_ultimo_relatorio = stats
        simulacao = stats.get("simulacao", False)
        self.label_status_relatorio.config(
            text=("SIMULAÇÃO: nenhuma alteração foi feita."
                  if simulacao else "EXECUÇÃO REAL concluída."),
            fg="#1565c0" if simulacao else "#2e7d32"
        )
        self.botao_exportar_plano.config(state="normal")
        self.tabela_resumo.heading("antes", text="Antes (Origem)")
        self.tabela_resumo.heading("depois", text="Depois (Previsto)" if simulacao else "Depois (Destino)")

        for item in self.tabela_resumo.get_children():
            self.tabela_resumo.delete(item)

        self.tabela_resumo.insert("", "end", values=(
            "Arquivos Totais",
            str(stats.get("origem_total_arq", 0)),
            str(stats.get("organizados", 0)),
            f"{stats.get('duplicados', 0)} duplicatas; {len(stats.get('conflitos', []))} conflitos"
        ))
        self.tabela_resumo.insert("", "end", values=(
            "Espaço em Disco",
            formatar_bytes(stats.get("origem_total_bytes", 0)),
            formatar_bytes(stats.get("espaco_destino_necessario", 0)),
            (f"{formatar_bytes(stats.get('espaco_destino_necessario', 0))} previstos"
             if simulacao else f"-{formatar_bytes(stats.get('bytes_economizados', 0))} liberados")
        ))
        self.tabela_resumo.insert("", "end", values=(
            "Fotos / Vídeos",
            "Não categorizados",
            f"{stats.get('fotos', 0)} fotos / {stats.get('videos', 0)} vídeos",
            "Separados por tipo" if stats.get("separar_por_tipo", False) else "Mesma pasta"
        ))
        self.tabela_resumo.insert("", "end", values=(
            "Estrutura",
            f"{stats.get('origem_qtd_pastas', 0)} pastas de origem",
            f"{len(stats.get('distribuicao_anos', {}))} anos previstos" if simulacao
            else f"{len(stats.get('distribuicao_anos', {}))} anos organizados",
            f"{len(stats.get('conflitos', []))} conflitos de nome"
        ))

        texto_relatorio = gerar_texto_relatorio(stats)
        self.caixa_relatorio_txt.configure(state="normal")
        self.caixa_relatorio_txt.delete("1.0", "end")
        self.caixa_relatorio_txt.insert("end", texto_relatorio)
        self.caixa_relatorio_txt.configure(state="disabled")

        self.notebook.select(self.aba_relatorio)

    def _exportar_plano(self):
        if not self._stats_ultimo_relatorio:
            return

        caminho = filedialog.asksaveasfilename(
            title="Exportar plano de organização",
            defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv"), ("Arquivo de texto", "*.txt")]
        )
        if not caminho:
            return

        plano = self._stats_ultimo_relatorio.get("plano_operacoes", [])
        try:
            if caminho.lower().endswith(".txt"):
                with open(caminho, "w", encoding="utf-8") as arquivo:
                    for item in plano:
                        arquivo.write(
                            f"{item.get('acao', '').upper()}: "
                            f"{item.get('origem', '')} -> {item.get('destino', '')} "
                            f"[{item.get('status', '')}]\n"
                        )
            else:
                with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
                    campos = ["acao", "origem", "destino", "status", "conflito"]
                    escritor = csv.DictWriter(arquivo, fieldnames=campos)
                    escritor.writeheader()
                    escritor.writerows({campo: item.get(campo, "") for campo in campos} for item in plano)
            self._log(f"Plano exportado para: {caminho}")
        except OSError as erro:
            messagebox.showerror("Erro", f"Não foi possível exportar o plano:\n{erro}")

    def _finalizar(self):
        self.botao_iniciar.config(state="normal")
        self.botao_simular.config(state="normal")
        self.botao_parar.config(state="disabled")
        self.label_progresso.config(
            text="Interrompido." if self._parar_flag else "Concluído."
        )

    def _parar(self):
        self._parar_flag = True
        self.botao_parar.config(state="disabled")
        self.label_progresso.config(text="Parando...")