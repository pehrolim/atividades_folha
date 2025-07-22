import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import datetime
import threading
import sys
import pandas as pd

# Importa a lógica do processador e os nossos widgets padrão
from app.logic.aco_militar_processor import AcoMilitarProcessor
from app.widgets.custom_button import StandardButton
from app.widgets.custom_labels import TitleLabel, InfoLabel, ValueLabel
from app.widgets.custom_frames import StandardFrame, TransparentFrame # <-- Importa os novos frames

class AcoMilitarGUI(ctk.CTkFrame):
    """
    View para o processamento de Acordos Militares, construída com CustomTkinter
    e utilizando componentes padronizados.
    """
    def __init__(self, master=None):
        super().__init__(master, fg_color="transparent")

        self.arquivos_selecionados = []
        self.pasta_destino_saida = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../data/acordo_militar_outputs'))
        os.makedirs(self.pasta_destino_saida, exist_ok=True)
        self.processor = AcoMilitarProcessor(logger_callback=self._log_mensagem)

        self.var_gerar_analise = ctk.BooleanVar(value=True)

        self._criar_interface()

    def _criar_interface(self):
        # --- Frame Principal para Arquivos (Seleção e Lista) ---
        files_main_frame = StandardFrame(self) # <-- Usa StandardFrame
        files_main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Botão de adicionar fica no topo deste frame
        StandardButton(files_main_frame, text="➕ Adicionar Arquivo Excel",
                       command=self._adicionar_arquivo_militar,
                       variant="success").pack(pady=15)

        # A lista de arquivos (ScrollableFrame) também fica neste frame
        self.frame_lista_arquivos = ctk.CTkScrollableFrame(files_main_frame, label_text="Arquivos Adicionados")
        self.frame_lista_arquivos.pack(fill="both", expand=True, padx=10, pady=10)
        self._atualizar_lista_arquivos_gui()  # Chamada inicial para mostrar a mensagem "Nenhum arquivo"

        # --- Frame Reduzido para Configurações de Saída ---
        output_frame = StandardFrame(self) # <-- Usa StandardFrame
        output_frame.pack(pady=10, padx=10, fill="x")

        TitleLabel(output_frame, text="Configurações de Saída").pack(pady=(5, 10))
        InfoLabel(output_frame, text="📂 Pasta de Destino:").pack()
        self.lbl_pasta_destino = ValueLabel(output_frame, text=self.pasta_destino_saida, wraplength=900)
        self.lbl_pasta_destino.pack(padx=10, pady=(0, 5))

        StandardButton(output_frame, text="Selecionar Outra Pasta",
                       command=self._selecionar_pasta_destino,
                       variant="primary").pack(pady=5)

        ctk.CTkCheckBox(output_frame, text="📊 Gerar arquivo de análise consolidada",
                        variable=self.var_gerar_analise).pack(pady=10)

        # --- Botão de Processamento e Log ---
        self.btn_processar = StandardButton(self, text="⚙️ Iniciar Processamento",
                                            command=self._iniciar_processamento_threaded,
                                            variant="processing")
        self.btn_processar.pack(pady=20, ipady=5)

        self.caixa_log = ctk.CTkTextbox(self, height=120, state='disabled', wrap='word')
        self.caixa_log.pack(fill="x", expand=False, padx=10, pady=5)

    def _atualizar_lista_arquivos_gui(self):
        for widget in self.frame_lista_arquivos.winfo_children():
            widget.destroy()

        if not self.arquivos_selecionados:
            ctk.CTkLabel(self.frame_lista_arquivos, text="Nenhum arquivo selecionado.", text_color="gray").pack(pady=20)
            return

        for i, arquivo_info in enumerate(self.arquivos_selecionados):
            # O frame de cada item da lista também pode ser padronizado
            main_block_frame = StandardFrame(self.frame_lista_arquivos, border_width=1)
            main_block_frame.pack(fill="x", pady=(5, 10), padx=5)

            TitleLabel(main_block_frame, text=arquivo_info['nome_amigavel'], font=("Roboto", 12, "bold")).pack(pady=5, padx=10, anchor="w")

            # Usa TransparentFrame para agrupar widgets sem fundo
            top_frame = TransparentFrame(main_block_frame)
            top_frame.pack(fill="x", expand=True, padx=10)

            InfoLabel(top_frame, text="Origem:").pack(side="left")
            entry_origem = ctk.CTkEntry(top_frame, placeholder_text=arquivo_info['nome_amigavel'])
            entry_origem.insert(0, arquivo_info['origem_manual'])
            entry_origem.bind("<FocusOut>", lambda e, idx=i, w=entry_origem: self._atualizar_origem_entry(idx, w))
            entry_origem.pack(side="left", padx=5, fill="x", expand=True)

            InfoLabel(top_frame, text="Tipo:").pack(side="left", padx=(10, 0))
            combo_tipo = ctk.CTkComboBox(top_frame, values=["Militar (Padrão)", "Grat. Magistério"], state="readonly", width=180)
            combo_tipo.set(arquivo_info['tipo'])
            combo_tipo.configure(command=lambda choice, idx=i, w=combo_tipo: self._atualizar_tipo_arquivo(idx, w))
            combo_tipo.pack(side="left", padx=5)

            # Usa TransparentFrame para a segunda linha de widgets
            bottom_frame = TransparentFrame(main_block_frame)
            bottom_frame.pack(fill="x", expand=True, pady=5, padx=10)

            InfoLabel(bottom_frame, text="Limite (h):").pack(side="left")
            entry_limite_horas = ctk.CTkEntry(bottom_frame, width=60, justify='center')
            entry_limite_horas.insert(0, str(arquivo_info['limite_horas']))
            entry_limite_horas.bind("<FocusOut>", lambda e, idx=i, w=entry_limite_horas: self._atualizar_limite_entry(idx, 'limite_horas', w))
            entry_limite_horas.pack(side="left", padx=5)

            InfoLabel(bottom_frame, text="GMR (h):").pack(side="left", padx=(10, 0))
            entry_limite_gmr = ctk.CTkEntry(bottom_frame, width=60, justify='center')
            entry_limite_gmr.insert(0, str(arquivo_info['limite_gmr_horas']))
            entry_limite_gmr.bind("<FocusOut>", lambda e, idx=i, w=entry_limite_gmr: self._atualizar_limite_entry(idx, 'limite_gmr_horas', w))
            entry_limite_gmr.pack(side="left", padx=5)

            status_color = "green" if "✅" in arquivo_info['status_validacao'] else "red" if "❌" in arquivo_info['status_validacao'] else "orange"
            ctk.CTkLabel(bottom_frame, text=f"Status: {arquivo_info['status_validacao']}", text_color=status_color).pack(side="left", padx=15)

            StandardButton(bottom_frame, text="🗑️", command=lambda idx=i: self._remover_arquivo(idx),
                           variant="danger", width=40).pack(side="right")

    def _log_mensagem(self, mensagem: str):
        if self.winfo_exists():
            self.after(0, self._append_log_message, mensagem)

    def _append_log_message(self, mensagem: str):
        self.caixa_log.configure(state='normal')
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.caixa_log.insert('end', f"[{timestamp}] {mensagem}\n")
        self.caixa_log.see('end')
        self.caixa_log.configure(state='disabled')

    def _adicionar_arquivo_militar(self):
        arquivo = filedialog.askopenfilename(title="Selecione um arquivo Excel de Vantagens",
                                             filetypes=[("Arquivos Excel", "*.xlsx *.xls")])
        if not arquivo: return
        nome_amigavel = os.path.basename(arquivo)
        if any(item['caminho'] == arquivo for item in self.arquivos_selecionados): self._log_mensagem(
            f"⚠️ Aviso: Arquivo '{nome_amigavel}' já foi adicionado."); return
        arquivo_info = {'caminho': arquivo, 'tipo': "Militar (Padrão)", 'origem_manual': nome_amigavel,
                        'limite_horas': self.processor.LIMITE_PADRAO_HORAS,
                        'limite_gmr_horas': self.processor.LIMITE_PADRAO_GMR_HORAS, 'nome_amigavel': nome_amigavel,
                        'status_validacao': 'Pendente'}
        self.arquivos_selecionados.append(arquivo_info)
        threading.Thread(target=self._validar_arquivo_background, args=(len(self.arquivos_selecionados) - 1,)).start()
        self._atualizar_lista_arquivos_gui()
        self._log_mensagem(f"📁 Arquivo adicionado: {nome_amigavel}")

    def _validar_arquivo_background(self, index):
        """Valida o arquivo em background e armazena o DataFrame validado em caso de sucesso."""
        try:
            arquivo_info = self.arquivos_selecionados[index]
            self._log_mensagem(f"🔍 Validando arquivo: {arquivo_info['nome_amigavel']}...")
            resultado = self.processor.validar_e_padronizar_arquivo(arquivo_info['caminho'])

            if resultado['status'] == 'sucesso':
                arquivo_info['status_validacao'] = 'Válido ✅'
                arquivo_info['dataframe'] = resultado['dataframe']
                self._log_mensagem(f"✅ Arquivo '{arquivo_info['nome_amigavel']}' validado com sucesso.")
            else:
                arquivo_info['status_validacao'] = f"Erro ❌"
                if 'dataframe' in arquivo_info:
                    del arquivo_info['dataframe']
                self._log_mensagem(f"❌ Erro na validação de '{arquivo_info['nome_amigavel']}': {resultado.get('mensagem', 'Erro desconhecido')}")
        except Exception as e:
            self.arquivos_selecionados[index]['status_validacao'] = f"Erro ❌"
            if 'dataframe' in self.arquivos_selecionados[index]:
                del self.arquivos_selecionados[index]['dataframe']
            self._log_mensagem(f"🚨 Erro inesperado na validação de '{arquivo_info['nome_amigavel']}': {str(e)}")
        finally:
            self.after(0, self._atualizar_lista_arquivos_gui)

    def _remover_arquivo(self, index):
        if 0 <= index < len(self.arquivos_selecionados): nome_removido = self.arquivos_selecionados[index][
            'nome_amigavel']; del self.arquivos_selecionados[index]; self._log_mensagem(
            f"🗑️ Arquivo removido: {nome_removido}"); self._atualizar_lista_arquivos_gui()

    def _atualizar_limite_entry(self, index, entry_type, entry_widget):
        try:
            new_value = entry_widget.get().strip();
            default_value = self.processor.LIMITE_PADRAO_HORAS if entry_type == 'limite_horas' else self.processor.LIMITE_PADRAO_GMR_HORAS;
            limite_int = int(new_value) if new_value else default_value
            if limite_int < 0: raise ValueError("O limite não pode ser negativo.")
            self.arquivos_selecionados[index][entry_type] = limite_int;
            entry_widget.delete(0, 'end');
            entry_widget.insert(0, str(limite_int))
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Por favor, digite um número inteiro válido.");
            entry_widget.delete(
                0, 'end');
            entry_widget.insert(0, str(self.arquivos_selecionados[index][entry_type]))

    def _atualizar_origem_entry(self, index, entry_widget):
        nova_origem = entry_widget.get().strip()
        if not nova_origem: nova_origem = self.arquivos_selecionados[index]['nome_amigavel']; entry_widget.delete(0,
                                                                                                                  'end'); entry_widget.insert(
            0, nova_origem)
        self.arquivos_selecionados[index]['origem_manual'] = nova_origem;
        self._log_mensagem(
            f"🏷️ Origem para {self.arquivos_selecionados[index]['nome_amigavel']} definida como '{nova_origem}'.")

    def _atualizar_tipo_arquivo(self, index, combobox_widget):
        novo_tipo = combobox_widget.get();
        self.arquivos_selecionados[index]['tipo'] = novo_tipo;
        self._log_mensagem(
            f"🔄 Tipo do arquivo '{self.arquivos_selecionados[index]['nome_amigavel']}' alterado para: {novo_tipo}.")

    def _selecionar_pasta_destino(self):
        pasta = filedialog.askdirectory(initialdir=self.pasta_destino_saida, title="Selecione a pasta de saída")
        if pasta: self.pasta_destino_saida = pasta; self.lbl_pasta_destino.configure(text=pasta); os.makedirs(
            self.pasta_destino_saida, exist_ok=True)

    def _iniciar_processamento_threaded(self):
        if not self.arquivos_selecionados: messagebox.showwarning("Arquivos Faltando",
                                                                  "Por favor, adicione pelo menos um arquivo para processar."); return
        if any("Pendente" in a['status_validacao'] or "Erro" in a['status_validacao'] for a in
               self.arquivos_selecionados): messagebox.showerror("Validação Incompleta",
                                                                 "Existem arquivos pendentes de validação ou com erros. Por favor, corrija antes de processar."); return
        self.btn_processar.configure(state="disabled", text="Processando...");
        self._limpar_log_gui();
        self._log_mensagem("🚀 Iniciando o processamento...");
        threading.Thread(target=self._executar_processamento).start()

    def _executar_processamento(self):
        """Prepara os dados (incluindo o DataFrame pré-validado) e inicia o processamento."""
        try:
            arquivos_para_processor = []
            for arq in self.arquivos_selecionados:
                tipo_logica = "ACO" if arq['tipo'] == "Militar (Padrão)" else "MAGISTERIO"
                info_para_processador = {
                    'caminho': arq['caminho'],
                    'limite_horas': arq['limite_horas'],
                    'limite_gmr_horas': arq['limite_gmr_horas'],
                    'nome_amigavel': arq['origem_manual'],
                    'tipo': tipo_logica
                }
                if 'dataframe' in arq and isinstance(arq.get('dataframe'), pd.DataFrame):
                    info_para_processador['dataframe'] = arq['dataframe']

                arquivos_para_processor.append(info_para_processador)

            resultado = self.processor.processar_arquivos_militares(arquivos_para_processor, self.pasta_destino_saida,
                                                                    gerar_analise=self.var_gerar_analise.get())
            self.after(0, self._pos_processamento_gui, resultado)
        except Exception as e:
            error_message = f"Ocorreu um erro durante o processamento: {e}";
            self.after(0, lambda
                msg=error_message: messagebox.showerror("Erro de Processamento", msg));
            self.after(0, lambda
                err=e: self._log_mensagem(f"💥 Erro fatal no processamento: {err}"))
        finally:
            self.after(0, lambda: self.btn_processar.configure(state="normal", text="⚙️ Iniciar Processamento"))

    def _pos_processamento_gui(self, resultado):
        if resultado["status"] == "sucesso":
            messagebox.showinfo("Processamento Concluído", resultado["mensagem"]);
            self._log_mensagem("🎉 Processamento concluído com sucesso!")
            if os.path.exists(self.pasta_destino_saida) and messagebox.askyesno("Abrir Pasta",
                                                                                "Deseja abrir a pasta com os arquivos gerados?"):
                try:
                    os.startfile(self.pasta_destino_saida)
                except AttributeError:
                    opener = "open" if sys.platform == "darwin" else "xdg-open";
                    import subprocess;
                    subprocess.Popen(
                        [opener, self.pasta_destino_saida])
                except Exception as e:
                    self._log_mensagem(f"Não foi possível abrir a pasta de destino automaticamente: {e}")
        else:
            messagebox.showerror("Erro no Processamento", resultado.get("mensagem", "Ocorreu um erro desconhecido."))

    def _limpar_log_gui(self):
        self.caixa_log.configure(state='normal');
        self.caixa_log.delete("1.0", 'end');
        self.caixa_log.configure(
            state='disabled')
