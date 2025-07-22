import pandas as pd
import os
import re
from collections import defaultdict
import json


class AcoMilitarProcessor:
    """
    Processa arquivos Excel de vantagens, consolida dados de matrículas militares,
    aplica limites de horas/valor e prepara o arquivo final para implantação.
    """

    def __init__(self, logger_callback=None):
        self.log = logger_callback if logger_callback else self._default_logger
        self.LIMITE_PADRAO_HORAS = 192
        self.LIMITE_PADRAO_GMR_HORAS = 48

    def _default_logger(self, message):
        """Um logger padrão simples para uso quando nenhum callback é fornecido."""
        print(message)

    def _tratar_valor_monetario(self, valor):
        """Converte um valor monetário para o formato de centavos inteiro."""
        if pd.isna(valor) or str(valor).strip() == '':
            return 0
        s_valor = str(valor).strip().replace('.', '').replace(',', '.')
        try:
            f_valor = float(s_valor)
            if '.' in s_valor and len(s_valor.split('.')[-1]) <= 2:
                return int(round(f_valor * 100))
            else:
                return int(round(f_valor))
        except ValueError:
            return 0

    def _limpar_campo(self, campo):
        """
        Limpa um campo genérico, removendo '.0' do final e espaços.
        Garante que a saída seja uma string limpa.
        """
        if pd.isna(campo) or str(campo).strip() == '':
            return ''
        campo_str = str(campo).strip()
        if campo_str.endswith('.0'):
            campo_str = campo_str[:-2]
        return campo_str.strip()

    def _parse_referencia(self, ref_int: int) -> tuple[int, int]:
        """
        Divide um valor de referência inteiro em horas majoradas e normais.
        Estrutura esperada: MMMNNN (ex: 120024 -> 120 majorada, 24 normal).
        """
        if not isinstance(ref_int, (int, float)) or pd.isna(ref_int):
            return 0, 0

        ref_str = str(int(ref_int)).zfill(6)
        h_majorada = int(ref_str[:-3])
        h_normal = int(ref_str[-3:])
        return h_majorada, h_normal

    def validar_e_padronizar_arquivo(self, caminho_arquivo):
        """
        Valida, limpa e padroniza o arquivo Excel de forma rigorosa.
        - Valida o tipo de dado de cada coluna individualmente.
        - Remove linhas cuja coluna 'REFERENCIA' seja 0.
        - Retorna um erro específico se qualquer validação falhar.
        - Retorna um dicionário com o status, uma mensagem e o DataFrame padronizado.
        """
        try:
            if not os.path.exists(caminho_arquivo):
                return {'status': 'erro', 'mensagem': f'Arquivo não encontrado: {caminho_arquivo}', 'dataframe': None}

            df = pd.read_excel(caminho_arquivo, dtype=str, engine='openpyxl').fillna('')

            if df.empty:
                return {'status': 'erro', 'mensagem': 'O arquivo Excel está vazio.', 'dataframe': None}

            colunas_obrigatorias = ['OPERACAO', 'MATRICULA', 'CODIGO', 'VALOR', 'REFERENCIA', 'PRAZO']
            colunas_atuais = df.columns
            mensagens_aviso = []

            # Etapa de Renomeação de Colunas
            if not set(colunas_obrigatorias).issubset(colunas_atuais):
                if len(colunas_atuais) < len(colunas_obrigatorias):
                    return {'status': 'erro',
                            'mensagem': f'O arquivo possui apenas {len(colunas_atuais)} colunas. São necessárias {len(colunas_obrigatorias)}.',
                            'dataframe': None}

                mapeamento = dict(zip(colunas_atuais[:len(colunas_obrigatorias)], colunas_obrigatorias))
                df.rename(columns=mapeamento, inplace=True)
                renamed_cols_str = ", ".join([f'"{k}" -> "{v}"' for k, v in mapeamento.items()])
                aviso = f"Colunas renomeadas automaticamente: {renamed_cols_str}"
                mensagens_aviso.append(aviso)

            # --- VALIDAÇÃO GRANULAR COLUNA POR COLUNA ---

            # 1. Validar colunas de texto obrigatórias
            for col in ['MATRICULA', 'OPERACAO', 'CODIGO']:
                if df[col].astype(str).str.strip().eq('').any():
                    linha_problema = df[df[col].astype(str).str.strip().eq('')].index[0] + 2
                    return {'status': 'erro',
                            'mensagem': f"Erro de Validação: A coluna '{col}' possui células vazias. Verifique a linha {linha_problema} do Excel.",
                            'dataframe': None}

            # 2. Validar e converter 'VALOR'
            df['VALOR'] = df['VALOR'].str.strip().str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            valores_invalidos = pd.to_numeric(df['VALOR'], errors='coerce').isna() & (df['VALOR'] != '')
            if valores_invalidos.any():
                linha_problema = valores_invalidos.idxmax() + 2
                valor_problema = df.loc[valores_invalidos.idxmax(), 'VALOR']
                return {'status': 'erro',
                        'mensagem': f"Erro de Validação: A coluna 'VALOR' contém um texto ('{valor_problema}') que não é um número válido. Verifique a linha {linha_problema} do Excel.",
                        'dataframe': None}
            df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)

            # 3. Validar e converter 'PRAZO'
            df['PRAZO'] = df['PRAZO'].str.strip().str.replace(r'\.0*$', '', regex=True)  # Remove .0 ou .00 do final
            prazos_invalidos = pd.to_numeric(df['PRAZO'], errors='coerce').isna() & (df['PRAZO'] != '')
            if prazos_invalidos.any():
                linha_problema = prazos_invalidos.idxmax() + 2
                valor_problema = df.loc[prazos_invalidos.idxmax(), 'PRAZO']
                return {'status': 'erro',
                        'mensagem': f"Erro de Validação: A coluna 'PRAZO' contém um texto ('{valor_problema}') que não é um número inteiro. Verifique a linha {linha_problema} do Excel.",
                        'dataframe': None}
            df['PRAZO'] = pd.to_numeric(df['PRAZO'], errors='coerce').fillna(0).astype(int)

            # 4. Validar e converter 'REFERENCIA' para inteiro
            df['REFERENCIA'] = df['REFERENCIA'].str.strip().str.replace('.', '', regex=False)
            df['REFERENCIA'] = df['REFERENCIA'].str.replace(r',0*$', '', regex=True)  # Remove ,0 ou ,00 do final

            nao_numerico = pd.to_numeric(df['REFERENCIA'], errors='coerce').isna() & (df['REFERENCIA'] != '')
            if nao_numerico.any():
                linha_problema = nao_numerico.idxmax() + 2
                valor_problema = df.loc[nao_numerico.idxmax(), 'REFERENCIA']
                return {'status': 'erro',
                        'mensagem': f"Erro de Validação: A coluna 'REFERENCIA' contém um valor ('{valor_problema}') que não é um número. Verifique a linha {linha_problema} do Excel.",
                        'dataframe': None}

            df['REFERENCIA'] = pd.to_numeric(df['REFERENCIA'], errors='coerce').fillna(0).astype(int)

            # --- ETAPA 5: Remover matrículas com referência 0 ---
            linhas_originais = len(df)
            df = df[df['REFERENCIA'] != 0].copy()
            linhas_removidas = linhas_originais - len(df)

            if linhas_removidas > 0:
                aviso_remocao = f"{linhas_removidas} matrícula(s) com referência 0 foram removidas do processamento."
                mensagens_aviso.append(aviso_remocao)
                if hasattr(self, 'logger_callback') and self.logger_callback:
                    self.logger_callback(aviso_remocao)

            # Se todas as validações passaram, o arquivo é considerado válido
            mensagem_final = 'Arquivo válido.'
            if mensagens_aviso:
                mensagem_final += " " + "; ".join(mensagens_aviso)

            return {'status': 'sucesso', 'mensagem': mensagem_final, 'dataframe': df}

        except Exception as e:
            print(f"ERRO INESPERADO em validar_e_padronizar_arquivo: {e}")
            return {'status': 'erro', 'mensagem': f'Erro inesperado ao ler ou validar o arquivo: {str(e)}',
                    'dataframe': None}

    def processar_arquivos_militares(self, arquivos_info: list, pasta_destino: str,
                                     gerar_analise: bool = True) -> dict:
        """Consolida e processa arquivos de ACO e Magistério, utilizando DataFrames pré-validados quando disponíveis."""
        if not arquivos_info:
            raise ValueError("Nenhum arquivo para processar foi fornecido.")
        os.makedirs(pasta_destino, exist_ok=True)

        horas_magisterio_por_mat = defaultdict(int)
        dados_consolidados = {}
        log_detalhado = []

        # ETAPA 1: Processar Magistério para criar um dicionário de consulta
        self.log("\n--- ETAPA 1: Criando lookup de horas de Magistério ---")
        arquivos_magisterio = [f for f in arquivos_info if f.get('tipo', '').strip().upper() == 'MAGISTERIO']
        for item in arquivos_magisterio:
            caminho_arquivo = item['caminho']
            nome_amigavel = item.get('nome_amigavel', os.path.basename(caminho_arquivo))
            self.log(f"Lendo arquivo de Magistério para consulta: '{nome_amigavel}'")
            try:
                # Lógica para Magistério continua lendo do disco, pois não passa pela mesma validação na GUI
                all_sheets = pd.read_excel(caminho_arquivo, dtype=str, sheet_name=None, engine='openpyxl')
                first_sheet_name = list(all_sheets.keys())[0]
                df_mag = all_sheets[first_sheet_name]

                for _, row in df_mag.iterrows():
                    matricula = self._limpar_campo(row.get('MATRICULA'))
                    if not matricula: continue

                    raw_ref = row.get('REFERENCIA')
                    ref_val = pd.to_numeric(raw_ref, errors='coerce')

                    if pd.notna(ref_val):
                        total_a_somar = int(ref_val)
                        if total_a_somar > 0:
                            horas_magisterio_por_mat[matricula] += total_a_somar
            except Exception as e:
                self.log(f"Aviso: Erro ao processar arquivo de consulta de magistério '{nome_amigavel}': {e}. Pulando.")

        # ETAPA 2: Processar Ajuda de Custo (ACO)
        self.log("\n--- ETAPA 2: Processamento de arquivos de Ajuda de Custo (ACO) ---")
        arquivos_aco = [f for f in arquivos_info if f.get('tipo', '').strip().upper() == 'ACO']
        if not arquivos_aco:
            raise ValueError("Nenhum arquivo do tipo 'ACO' (militar/padrão) foi fornecido para processamento.")

        for item in arquivos_aco:
            caminho_arquivo = item['caminho']
            nome_amigavel = item.get('nome_amigavel', os.path.basename(caminho_arquivo))
            limite_horas = item.get('limite_horas', self.LIMITE_PADRAO_HORAS)
            limite_gmr = item.get('limite_gmr_horas', self.LIMITE_PADRAO_GMR_HORAS)
            self.log(f"Processando arquivo ACO '{nome_amigavel}'")
            try:
                # --- MELHORIA: Utiliza DataFrame pré-validado se disponível ---
                if 'dataframe' in item and isinstance(item.get('dataframe'), pd.DataFrame):
                    self.log(f"-> Usando dados pré-validados e limpos para '{nome_amigavel}'.")
                    df_aco = item['dataframe']
                else:
                    # Fallback: lê o arquivo do disco se não houver DataFrame
                    self.log(f"-> Lendo arquivo do disco para '{nome_amigavel}' (validação não fornecida).")
                    df_aco = pd.read_excel(caminho_arquivo, dtype=str, engine='openpyxl')
                # --- FIM DA MELHORIA ---

                for _, row in df_aco.iterrows():
                    matricula = self._limpar_campo(row.get('MATRICULA'))
                    codigo = self._limpar_campo(row.get('CODIGO'))
                    valor_num = self._tratar_valor_monetario(row.get('VALOR'))
                    # A coluna REFERENCIA já vem como int do processo de validação
                    ref_num = row.get('REFERENCIA', 0)

                    log_detalhado.append({
                        'ORIGEM_ARQUIVO': nome_amigavel, 'MATRICULA_LIMPA': matricula,
                        'CODIGO_LIMPO': codigo, 'REFERENCIA_LIDA': ref_num
                    })

                    if not matricula or (not codigo and ref_num == 0 and valor_num == 0):
                        continue

                    if matricula not in dados_consolidados:
                        dados_consolidados[matricula] = {
                            'limite_horas': 0, 'limite_gmr_horas': 0, 'soma_valor_total': 0,
                            'detalhes_por_codigo': defaultdict(
                                lambda: {'soma_referencia': 0, 'soma_valor': 0, 'operacao': 'I', 'prazo': '0',
                                         'origens': set()})
                        }

                    dados_consolidados[matricula]['limite_horas'] = max(dados_consolidados[matricula]['limite_horas'],
                                                                        limite_horas)
                    if valor_num > 0:
                        dados_consolidados[matricula]['limite_gmr_horas'] = max(
                            dados_consolidados[matricula]['limite_gmr_horas'], limite_gmr)

                    detalhe_codigo = dados_consolidados[matricula]['detalhes_por_codigo'][codigo]
                    detalhe_codigo['soma_referencia'] += ref_num
                    detalhe_codigo['soma_valor'] += valor_num
                    dados_consolidados[matricula]['soma_valor_total'] += valor_num
                    detalhe_codigo['operacao'] = row.get('OPERACAO', 'I')
                    detalhe_codigo['prazo'] = self._limpar_campo(row.get('PRAZO', '0'))
                    detalhe_codigo['origens'].add(nome_amigavel)
            except Exception as e:
                self.log(f"Erro ao processar arquivo ACO '{nome_amigavel}': {e}")
                continue

        # ... (O restante da função continua igual)
        caminhos_saida = {}
        if log_detalhado:
            df_log_detalhado = pd.DataFrame(log_detalhado)
            caminho_log_detalhado = os.path.join(pasta_destino, "log_detalhado_processamento.xlsx")
            df_log_detalhado.to_excel(caminho_log_detalhado, index=False)
            self.log(f"\n✓ Arquivo de log detalhado salvo em: {caminho_log_detalhado}")
            caminhos_saida["log_detalhado"] = caminho_log_detalhado

        # ETAPA 3: Geração da estrutura interna e do arquivo final
        self.log("\n--- INICIANDO ETAPA 3: Análise de horas e geração de arquivos ---")
        lista_final_para_df = []
        for matricula, data in dados_consolidados.items():
            for codigo, detalhes in data['detalhes_por_codigo'].items():
                soma_ref_bruta = detalhes['soma_referencia']
                h_majorada, h_normal = self._parse_referencia(soma_ref_bruta)
                h_total_aco = h_majorada + h_normal

                ref_magisterio = horas_magisterio_por_mat.get(matricula, 0)
                total_horas = h_total_aco + ref_magisterio

                referencia_final = soma_ref_bruta
                if detalhes['soma_valor'] > 0:
                    referencia_final = min(soma_ref_bruta, data['limite_gmr_horas'])

                origens_finais = set(detalhes['origens'])
                if ref_magisterio > 0:
                    origens_finais.add("Grat. Magistério (Consulta)")

                lista_final_para_df.append({
                    'MATRICULA': matricula, 'CODIGO': codigo, 'OPERACAO': detalhes['operacao'],
                    'PRAZO': detalhes['prazo'], 'VALOR': detalhes['soma_valor'], 'REFERENCIA': referencia_final,
                    'SOMA_REF_BRUTA_ACO': soma_ref_bruta, 'H_NORMAL_ACO': h_normal, 'H_MAJORADA_ACO': h_majorada,
                    'H_TOTAL_ACO': h_total_aco, 'REF_MAGISTERIO_TOTAL_HORAS': ref_magisterio,
                    'TOTAL_HORAS': total_horas, 'VALOR_TOTAL': data['soma_valor_total'],
                    'LIMITE_HORAS_PADRAO': data['limite_horas'], 'LIMITE_GMR_APLICADO': data['limite_gmr_horas'],
                    'ORIGEM_ARQUIVOS': ', '.join(sorted(list(origens_finais)))
                })

        if not lista_final_para_df:
            self.log("Nenhum registro resultante após a consolidação.")
            return {"status": "sucesso", "mensagem": "Processamento concluído, mas nenhum registro válido encontrado.",
                    "caminhos_saida": caminhos_saida}

        df_completo = pd.DataFrame(lista_final_para_df)

        caminhos_saida["estrutura_interna"] = self._gerar_arquivo_estrutura_interna(df_completo, pasta_destino)

        # Gerando arquivo final para implantação com filtro
        self.log("\n--- Gerando arquivo final para implantação ---")

        total_registros_antes = len(df_completo)

        condicao_sem_gmr = (df_completo['VALOR_TOTAL'] == 0) & (
                    df_completo['TOTAL_HORAS'] <= df_completo['LIMITE_HORAS_PADRAO'])
        condicao_com_gmr = (df_completo['VALOR_TOTAL'] > 0) & (
                    df_completo['TOTAL_HORAS'] <= df_completo['LIMITE_GMR_APLICADO'])

        df_implantacao_filtrado = df_completo[condicao_sem_gmr | condicao_com_gmr].copy()
        total_registros_depois = len(df_implantacao_filtrado)

        self.log(f"Foram encontradas {total_registros_antes} vantagens no total.")
        self.log(
            f"Destas, {total_registros_depois} estão dentro do limite de horas aplicável e serão incluídas no arquivo de implantação.")
        self.log(
            f"Foram filtrados {total_registros_antes - total_registros_depois} registros por excederem o limite de horas.")

        colunas_saida_implantacao = ['OPERACAO', 'MATRICULA', 'CODIGO', 'VALOR', 'REFERENCIA', 'PRAZO']
        df_implantacao_output = df_implantacao_filtrado[colunas_saida_implantacao].copy()

        df_implantacao_output['VALOR'] = df_implantacao_output['VALOR'].apply(lambda x: '' if x == 0 else x)

        caminho_final_implantacao_output = os.path.join(pasta_destino, "implantacao_acordo_militar_final.xlsx")
        df_implantacao_output.to_excel(caminho_final_implantacao_output, index=False)
        self.log(
            f"✓ Arquivo para implantação salvo com {len(df_implantacao_output)} registros em: {caminho_final_implantacao_output}")
        caminhos_saida["para_implantacao"] = caminho_final_implantacao_output

        if gerar_analise:
            try:
                caminho_analise = self._gerar_arquivo_analise_novo(df_completo, pasta_destino)
                caminhos_saida["analise"] = caminho_analise
                self.log(f"✓ Arquivo de análise (com todos os dados) salvo em: {caminho_analise}")
            except Exception as e:
                self.log(f"⚠️ Erro ao gerar arquivo de análise: {e}")

        self.log("\n--- PROCESSAMENTO DE ACORDO MILITAR CONCLUÍDO ---")
        return {"status": "sucesso", "mensagem": "Processamento de Acordo Militar concluído com sucesso!",
                "caminhos_saida": caminhos_saida}

    def _gerar_arquivo_estrutura_interna(self, df_completo: pd.DataFrame, pasta_destino: str) -> str:
        """Gera um arquivo Excel mostrando a estrutura de dados interna completa para validação."""
        self.log("\n--- Gerando arquivo de validação da estrutura de dados interna ---")
        if df_completo.empty:
            self.log("Nenhum dado para gerar o arquivo de estrutura interna.")
            return ""

        colunas_estrutura = [
            'MATRICULA', 'CODIGO', 'ORIGEM_ARQUIVOS', 'SOMA_REF_BRUTA_ACO',
            'H_NORMAL_ACO', 'H_MAJORADA_ACO', 'H_TOTAL_ACO',
            'REF_MAGISTERIO_TOTAL_HORAS', 'TOTAL_HORAS', 'VALOR', 'VALOR_TOTAL',
            'LIMITE_HORAS_PADRAO', 'LIMITE_GMR_APLICADO'
        ]

        df_saida = df_completo.rename(columns={'VALOR': 'SOMA_VALOR_BRUTO_CENTAVOS_POR_LINHA'})
        df_saida = df_saida[[col for col in colunas_estrutura if col in df_saida.columns]]

        try:
            caminho_saida = os.path.join(pasta_destino, "estrutura_dados_interna.xlsx")
            df_saida.to_excel(caminho_saida, index=False)
            self.log(f"✓ Arquivo de validação da estrutura salvo em: {caminho_saida}")
            return caminho_saida
        except Exception as e:
            self.log(f"⚠️ Erro ao gerar arquivo da estrutura interna: {e}")
            return ""

    def _gerar_arquivo_analise_novo(self, df_analise_completo: pd.DataFrame, pasta_destino: str) -> str:
        """Gera um arquivo de análise a partir do DataFrame processado."""
        caminho_analise = os.path.join(pasta_destino, "analise_consolidada_militares.xlsx")
        with pd.ExcelWriter(caminho_analise, engine='openpyxl') as writer:
            # Filtra os dados para a aba de implantação DENTRO da análise
            condicao_sem_gmr = (df_analise_completo['VALOR_TOTAL'] == 0) & (
                        df_analise_completo['TOTAL_HORAS'] <= df_analise_completo['LIMITE_HORAS_PADRAO'])
            condicao_com_gmr = (df_analise_completo['VALOR_TOTAL'] > 0) & (
                        df_analise_completo['TOTAL_HORAS'] <= df_analise_completo['LIMITE_GMR_APLICADO'])
            df_implantacao_filtrado_analise = df_analise_completo[condicao_sem_gmr | condicao_com_gmr].copy()

            df_implantacao = df_implantacao_filtrado_analise[
                ['OPERACAO', 'MATRICULA', 'CODIGO', 'VALOR', 'REFERENCIA', 'PRAZO']].copy()
            df_implantacao['VALOR'] = df_implantacao['VALOR'].apply(lambda x: '' if x == 0 else x)
            df_implantacao.to_excel(writer, sheet_name='Dados_Implantacao_Filtrados', index=False)

            # Aba de Detalhes do Processamento com TODOS os dados
            df_analise_completo.to_excel(writer, sheet_name='Detalhes_Processamento_TODOS', index=False)

            # Aba de Resumo por Matrícula com TODOS os dados
            resumo_matricula = df_analise_completo.groupby('MATRICULA').agg(
                VALOR_TOTAL_REAIS=('VALOR_TOTAL', 'first'),
                TOTAL_HORAS_NORMAIS_ACO=('H_NORMAL_ACO', 'sum'),
                TOTAL_HORAS_MAJORADAS_ACO=('H_MAJORADA_ACO', 'sum'),
                TOTAL_HORAS_ACO=('H_TOTAL_ACO', 'sum'),
                HORAS_MAGISTERIO=('REF_MAGISTERIO_TOTAL_HORAS', 'first'),
                LIMITE_HORAS_PADRAO=('LIMITE_HORAS_PADRAO', 'first'),
                LIMITE_GMR=('LIMITE_GMR_APLICADO', 'first')
            ).reset_index()
            resumo_matricula['VALOR_TOTAL_REAIS'] = resumo_matricula['VALOR_TOTAL_REAIS'] / 100.0
            resumo_matricula['TOTAL_HORAS'] = resumo_matricula['TOTAL_HORAS_ACO'] + resumo_matricula['HORAS_MAGISTERIO']

            # Aplica a lógica de limite excedido correta
            limite_aplicavel = resumo_matricula.apply(
                lambda row: row['LIMITE_GMR'] if row['VALOR_TOTAL_REAIS'] > 0 else row['LIMITE_HORAS_PADRAO'], axis=1)
            resumo_matricula['LIMITE_EXCEDIDO'] = resumo_matricula['TOTAL_HORAS'] > limite_aplicavel

            resumo_matricula.to_excel(writer, sheet_name='Resumo_Matricula', index=False)

            resumo_codigo = df_analise_completo.groupby('CODIGO').agg(
                VALOR_TOTAL_REAIS=('VALOR', lambda x: x.sum() / 100),
                TOTAL_HORAS_NORMAIS=('H_NORMAL_ACO', 'sum'),
                TOTAL_HORAS_MAJORADAS=('H_MAJORADA_ACO', 'sum'),
                QTD_MATRICULAS=('MATRICULA', 'nunique')
            ).reset_index()
            resumo_codigo.to_excel(writer, sheet_name='Resumo_Codigo', index=False)
        return caminho_analise
