# atividades_folha/app/logic/file_monitor.py
import os
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Importa a classe DataManager da mesma camada logic
from app.logic.data_manager import DataManager

class FileProcessingHandler(FileSystemEventHandler):
    """
    Manipulador de eventos do sistema de arquivos que reage à criação de arquivos.
    Processa novos arquivos .txt e os move para uma pasta de destino.
    """
    def __init__(self, data_manager: DataManager, pasta_destino: str, logger_callback, arquivo_processado_callback):
        """
        Inicializa o manipulador de eventos.

        Args:
            data_manager (DataManager): Instância do DataManager para manipulação dos dados.
            pasta_destino (str): Caminho para a pasta onde os arquivos processados serão movidos.
            logger_callback (callable): Função para registrar mensagens (geralmente da GUI).
            arquivo_processado_callback (callable): Função a ser chamada após o processamento de um arquivo.
        """
        self.data_manager = data_manager
        self.pasta_destino = pasta_destino
        self.log = logger_callback
        self.arquivo_processado_callback = arquivo_processado_callback

    def on_created(self, event):
        """
        Chamado quando um arquivo ou diretório é criado.
        """
        if event.is_directory:
            return

        caminho_origem = event.src_path
        nome_arquivo = os.path.basename(caminho_origem)

        # 1. Ignora arquivos temporários de download
        if nome_arquivo.endswith((".part", ".crdownload", ".tmp")):
            self.log(f"[-] Ignorado arquivo temporário: {nome_arquivo}")
            return

        # 2. Garante que o arquivo não seja processado se já estiver na pasta de destino
        # Compara caminhos absolutos para evitar problemas de caminho relativo
        if os.path.dirname(os.path.abspath(caminho_origem)) == os.path.abspath(self.pasta_destino):
            self.log(f"[-] Ignorado: arquivo já está na pasta de destino: {nome_arquivo}")
            return

        # 3. Verifica se o arquivo está estável (download concluído)
        if not self._aguardar_estabilidade_arquivo(caminho_origem, nome_arquivo):
            self.log(f"[!] O tamanho do arquivo {nome_arquivo} continua mudando ou desapareceu. Processamento cancelado.")
            return

        # 4. Processa o arquivo
        self._processar_arquivo(caminho_origem, nome_arquivo)

    def _aguardar_estabilidade_arquivo(self, caminho_arquivo: str, nome_arquivo: str) -> bool:
        """
        Espera até que o tamanho do arquivo se estabilize, indicando que o download está completo.

        Args:
            caminho_arquivo (str): Caminho completo para o arquivo.
            nome_arquivo (str): Nome do arquivo.

        Returns:
            bool: True se o arquivo se tornou estável, False caso contrário.
        """
        tamanho = -1
        # Tenta por até 5 segundos (10 * 0.5s)
        for _ in range(10):
            try:
                novo_tamanho = os.path.getsize(caminho_arquivo)
                if novo_tamanho == tamanho and tamanho != 0: # Garante que o arquivo não está mais crescendo
                    return True
                tamanho = novo_tamanho
                time.sleep(0.5)
            except FileNotFoundError:
                # O arquivo pode ter sido movido ou excluído por outro processo
                self.log(f"[!] Arquivo '{nome_arquivo}' desapareceu antes de se estabilizar.")
                return False
        return False # Não ficou estável dentro do tempo limite

    def _processar_arquivo(self, caminho_origem: str, nome_arquivo: str):
        """
        Lê, processa e move um arquivo.
        """
        try:
            self.log(f"[📄] Lendo {nome_arquivo}...")
            # Lê o conteúdo do arquivo
            with open(caminho_origem, 'r', encoding='utf-8') as f:
                conteudo = f.read()

            # Adiciona os dados ao DataManager
            novos_registros = self.data_manager.adicionar_dados_do_txt(conteudo)
            self.log(f"[+] Dados de {nome_arquivo} armazenados. Novos registros: {novos_registros}. Total de registros: {len(self.data_manager.obter_dados_acumulados())}")

            # Move o arquivo processado
            caminho_destino = os.path.join(self.pasta_destino, nome_arquivo)
            shutil.move(caminho_origem, caminho_destino)
            self.log(f"[↪️] Arquivo movido para: {caminho_destino}")

            # Notifica a camada de apresentação que um arquivo foi processado
            self.arquivo_processado_callback()

        except Exception as e:
            self.log(f"[❌] Erro ao processar '{nome_arquivo}': {e}")


class FileMonitor:
    """
    Gerencia o ciclo de vida do monitoramento de pastas usando watchdog.
    """
    def __init__(self, data_manager: DataManager, logger_callback, arquivo_processado_callback):
        """
        Inicializa o monitor de arquivos.

        Args:
            data_manager (DataManager): Instância do DataManager para passar ao handler.
            logger_callback (callable): Função para registrar mensagens (geralmente da GUI).
            arquivo_processado_callback (callable): Função a ser chamada após o processamento de um arquivo.
        """
        self.observer = None
        self.handler = None
        self._is_monitoring = False # Variável interna para o estado do monitoramento
        self.data_manager = data_manager
        self.log = logger_callback
        self.arquivo_processado_callback = arquivo_processado_callback

    def iniciar_monitoramento(self, pasta_origem: str, pasta_destino: str) -> bool:
        """
        Inicia o monitoramento de uma pasta especificada para novos arquivos.

        Args:
            pasta_origem (str): O caminho da pasta a ser monitorada.
            pasta_destino (str): O caminho da pasta para onde os arquivos serão movidos.

        Returns:
            bool: True se o monitoramento foi iniciado com sucesso, False caso contrário.
        """
        if self._is_monitoring:
            self.log("Monitoramento já está em execução.")
            return False

        # Garante que a pasta de destino exista
        os.makedirs(pasta_destino, exist_ok=True)

        self.handler = FileProcessingHandler(
            self.data_manager,
            pasta_destino,
            self.log,
            self.arquivo_processado_callback
        )
        self.observer = Observer()
        # Agenda o handler para monitorar a pasta de origem (não recursivamente)
        self.observer.schedule(self.handler, path=pasta_origem, recursive=False)
        self.observer.start()
        self._is_monitoring = True
        self.log(f"🟢 Monitoramento iniciado na pasta: {pasta_origem}. Arquivos serão movidos para: {pasta_destino}")
        return True

    def parar_monitoramento(self) -> bool:
        """
        Para o monitoramento de arquivos.

        Returns:
            bool: True se o monitoramento foi parado com sucesso, False caso contrário.
        """
        if not self._is_monitoring:
            self.log("Monitoramento não está em execução.")
            return False

        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join() # Espera o thread do observer finalizar
        self._is_monitoring = False
        self.log("🔴 Monitoramento parado.")
        return True

    def obter_status_monitoramento(self) -> bool:
        """
        Retorna o estado atual do monitoramento (ativo ou inativo).

        Returns:
            bool: True se o monitoramento estiver ativo, False caso contrário.
        """
        return self._is_monitoring