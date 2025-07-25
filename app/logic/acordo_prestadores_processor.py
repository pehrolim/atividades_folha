# atividades_folha/app/logic/acordo_prestadores_processor.py
import pandas as pd
import os
import re
import sys  # Para sys.exit(), se ainda for necessário em caso de cancelamento
import subprocess


class AcordoPrestadoresProcessor:
    """
    Processa dados para o 'Acordo de Prestadores', realizando leitura de múltiplos arquivos,
    cruzamento, filtragem e geração de relatórios de saída.
    """

    def __init__(self, logger_callback=None):
        """
        Inicializa o processador.
        Args:
            logger_callback (callable): Função para registrar mensagens de log (geralmente da GUI).
        """
        self.log = logger_callback if logger_callback else self._default_logger
        self.clf_habilitadas = [10021, 10033, 10015, 49911, 49921]  # Constante de filtro

    def _default_logger(self, message):
        """Um logger padrão simples para uso quando nenhum callback é fornecido."""
        print(message)

    def _formatar_cpf_padrao(self, cpf):
        """Converte CPF para uma string de 11 dígitos, removendo caracteres extras."""
        # Garante que 'cpf' é uma string antes de chamar métodos de string
        cpf_texto = str(cpf).split('.')[0]
        numeros = re.sub(r'\D', '', cpf_texto)
        return numeros.zfill(11)

    def _formatar_matricula(self, mat):
        """Converte matrícula para uma string limpa, removendo '.0' e espaços."""
        # Garante que 'mat' é uma string antes de chamar métodos de string
        mat_texto = str(mat).split('.')[0]
        return mat_texto.strip()

    def processar_acordo_prestadores(self,
                                     arquivo_cadastro: str,
                                     arquivo_advogados: str,
                                     arquivo_116: str,
                                     arquivo_898_csv: str,
                                     caminho_base_saida: str):
        """
        Orquestra todo o processo de geração do 'Acordo de Prestadores'.

        Args:
            arquivo_cadastro (str): Caminho para o arquivo Excel de cadastro geral.
            arquivo_advogados (str): Caminho para a lista de advogados (Excel).
            arquivo_116 (str): Caminho para o arquivo CSV do código 116.
            arquivo_898_csv (str): Caminho para o arquivo CSV do código 898.
            caminho_base_saida (str): Pasta onde todos os arquivos de saída serão salvos.
        """
        self.log("----- INICIANDO PROCESSO COMPLETO DE ACORDO DE PRESTADORES -----")
        os.makedirs(caminho_base_saida, exist_ok=True)  # Garante que a pasta de destino exista

        # --- 2. LEITURA E FILTRO INICIAL DO CADASTRO ---
        try:
            colunas_cadastro = ['CPF', 'NOME', 'MATRICULA', 'CLAS_FUNC', 'SITUACAO']
            df_cadastro = pd.read_excel(arquivo_cadastro, usecols=colunas_cadastro)
            df_cadastro.dropna(subset=['CPF'], inplace=True)
            df_resumido = df_cadastro[df_cadastro['CLAS_FUNC'].isin(self.clf_habilitadas)].copy()
            df_resumido['CPF_PADRAO'] = df_resumido['CPF'].apply(self._formatar_cpf_padrao)
            self.log(f"✓ Cadastro lido e filtrado por CLF: {len(df_resumido)} registros.")
        except Exception as e:
            raise ValueError(f"Erro ao ler ou processar o Arquivo de Cadastro Geral: {e}")

        # --- 3. LEITURA DA LISTA DOS ADVOGADOS ---
        try:
            df_adv = pd.read_excel(arquivo_advogados, usecols=['CPF x1'])
            df_adv.dropna(subset=['CPF x1'], inplace=True)
            df_adv['CPF_PADRAO'] = df_adv['CPF x1'].apply(self._formatar_cpf_padrao)
            self.log(f"✓ Lista de advogados lida: {len(df_adv)} CPFs.")
        except Exception as e:
            raise ValueError(f"Erro ao ler ou processar a Lista dos Advogados: {e}")

        # --- 4. CRUZAMENTO INICIAL E GERAÇÃO DE INAPTOS ---
        df_merged = pd.merge(df_resumido, df_adv, on='CPF_PADRAO', how='right', indicator=True)
        df_aptos_inicial = df_merged[df_merged['_merge'] == 'both'].copy()

        # Garante que as colunas existam antes de selecioná-las
        colunas_finais_aptos = [col for col in ['CPF x1', 'CPF', 'NOME', 'MATRICULA', 'CLAS_FUNC', 'SITUACAO'] if
                                col in df_aptos_inicial.columns]
        df_aptos_inicial = df_aptos_inicial[colunas_finais_aptos]
        self.log(f"✓ Cruzamento inicial encontrou {len(df_aptos_inicial)} servidores no cadastro.")

        df_inaptos = df_merged[df_merged['_merge'] == 'right_only'].copy()
        df_inaptos['OBSERVACAO'] = 'CPF NÃO ENCONTRADO NO CADASTRO COM CLF HABILITADA'

        # Garante que 'CPF x1' exista antes de tentar salvar
        colunas_inaptos = [col for col in ['CPF x1', 'OBSERVACAO'] if col in df_inaptos.columns]
        if colunas_inaptos:
            df_inaptos[colunas_inaptos].to_excel(os.path.join(caminho_base_saida, 'INAPTOS.xlsx'), index=False)
            self.log(f"✓ Arquivo 'INAPTOS.xlsx' salvo com {len(df_inaptos)} servidores.")
        else:
            self.log("Aviso: Não foi possível gerar 'INAPTOS.xlsx' por falta de colunas necessárias.")

        # --- 5. PROCESSAMENTO DOS CÓDIGOS DA FOLHA ---
        colunas_folha = ['MATRICULA', 'NOME', 'CODIGO', 'VALOR', 'REFERENCIA', 'PRAZO', 'ORGAO', 'CLF', 'SIMBOLO',
                         'SITUACAO', 'SAIDA', 'DATA_AFAST', 'GRUPO', 'REGIME_PREV']
        try:
            df_116 = pd.read_csv(arquivo_116, sep=',', names=colunas_folha, header=None, dtype=str)
            df_898 = pd.read_csv(arquivo_898_csv, sep=',', names=colunas_folha, header=None, dtype=str)
            df_codigos_folha = pd.concat([df_116, df_898], ignore_index=True)
            df_codigos_folha.to_excel(os.path.join(caminho_base_saida, 'CODIGOS_FOLHA.xlsx'), index=False)
            self.log(f"✓ Arquivo 'CODIGOS_FOLHA.xlsx' salvo com {len(df_codigos_folha)} linhas.")
        except Exception as e:
            raise ValueError(f"Erro ao ler ou concatenar os arquivos de Código 116/898: {e}")

        # --- 6. IDENTIFICAÇÃO DE DUPLICADOS (PRIMEIRO FILTRO) ---
        df_aptos_inicial['MATRICULA'] = df_aptos_inicial['MATRICULA'].apply(self._formatar_matricula)
        df_codigos_folha['MATRICULA'] = df_codigos_folha['MATRICULA'].apply(self._formatar_matricula)

        # Garante que as matriculas são strings antes de usar unique
        matriculas_pagas = df_codigos_folha['MATRICULA'].astype(str).dropna().unique()

        df_duplicados = df_aptos_inicial[df_aptos_inicial['MATRICULA'].isin(matriculas_pagas)].copy()
        df_duplicados.to_excel(os.path.join(caminho_base_saida, 'DUPLICADOS.xlsx'), index=False)
        self.log(f"✓ Arquivo 'DUPLICADOS.xlsx' salvo com {len(df_duplicados)} servidores.")

        # --- 7. SEPARAÇÃO DE AFASTADOS E GERAÇÃO DE APTOS FINAIS ---
        df_nao_duplicados = df_aptos_inicial[~df_aptos_inicial['MATRICULA'].isin(matriculas_pagas)].copy()

        # Garante que 'SITUACAO' existe antes de filtrar
        if 'SITUACAO' in df_nao_duplicados.columns:
            df_exonerados = df_nao_duplicados[df_nao_duplicados['SITUACAO'] == 'AFASTADO'].copy()
            df_exonerados.to_excel(os.path.join(caminho_base_saida, 'EXONERADOS.xlsx'), index=False)
            self.log(f"✓ Arquivo 'EXONERADOS.xlsx' salvo com {len(df_exonerados)} servidores.")

            df_aptos_final = df_nao_duplicados[df_nao_duplicados['SITUACAO'] != 'AFASTADO'].copy()
            df_aptos_final.to_excel(os.path.join(caminho_base_saida, 'APTOS.xlsx'), index=False)
            self.log(f"✓ Arquivo 'APTOS.xlsx' salvo com {len(df_aptos_final)} servidores.")
        else:
            self.log(
                "Aviso: Coluna 'SITUACAO' não encontrada. 'EXONERADOS.xlsx' e 'APTOS.xlsx' não foram filtrados por situação.")
            df_aptos_final = df_nao_duplicados.copy()  # Se não tem situação, todos são considerados aptos finais por padrão.
            df_aptos_final.to_excel(os.path.join(caminho_base_saida, 'APTOS.xlsx'), index=False)
            self.log(f"✓ Arquivo 'APTOS.xlsx' salvo com {len(df_aptos_final)} servidores (sem filtro de situação).")

        # --- 8. GERAÇÃO DO ARQUIVO DE IMPLANTAÇÃO ---
        if not df_aptos_final.empty:
            # Garante que 'MATRICULA' exista
            if 'MATRICULA' in df_aptos_final.columns:
                df_data_116 = pd.DataFrame(
                    {'OPERACAO': '7', 'MATRICULA': df_aptos_final['MATRICULA'], 'CODIGO': 116, 'VALOR': '',
                     'REFERENCIA': '', 'PRAZO': ''})
                df_data_898 = pd.DataFrame(
                    {'OPERACAO': '7', 'MATRICULA': df_aptos_final['MATRICULA'], 'CODIGO': 898, 'VALOR': 27344,
                     'REFERENCIA': '', 'PRAZO': 4})
                df_implantacao = pd.concat([df_data_116, df_data_898], ignore_index=True)
                df_implantacao.to_excel(os.path.join(caminho_base_saida, 'IMPLANTACAO_FINAL.xlsx'), index=False)
                self.log(f"✓ Arquivo 'IMPLANTACAO_FINAL.xlsx' salvo com {len(df_implantacao)} linhas.")
            else:
                self.log("Aviso: Coluna 'MATRICULA' não encontrada para gerar o arquivo de implantação.")
                self.log("✓ Nenhum arquivo de implantação gerado por falta de matrículas.")
        else:
            self.log("✓ Nenhum servidor na lista final para gerar arquivo de implantação.")

        self.log("\n----- PROCESSO DE ACORDO DE PRESTADORES CONCLUÍDO -----")
        return "Processo de Acordo de Prestadores concluído com sucesso!"