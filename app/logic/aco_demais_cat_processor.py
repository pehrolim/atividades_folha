#app/logic/aco_demais_cat_processor.py
import pandas as pd
import os
from collections import defaultdict


class AcoDemaisCatProcessor:
    """
    Processa arquivos Excel de vantagens para as demais categorias (não militares),
    consolida dados, aplica um único limite de horas e prepara o arquivo final para implantação.
    """

    def __init__(self, logger_callback=None):
        self.log = logger_callback if logger_callback else self._default_logger
        self.LIMITE_PADRAO_HORAS = 192

    def _default_logger(self, message):
        """Um logger padrão simples para uso quando nenhum callback é fornecido."""
        print(message)

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
        """Valida se o arquivo Excel possui as colunas necessárias e estrutura correta."""
        try:
            if not os.path.exists(caminho_arquivo):
                return {'status': 'erro', 'mensagem': f'Arquivo não encontrado: {caminho_arquivo}'}
            df = pd.read_excel(caminho_arquivo, dtype=str, engine='openpyxl')
            if df.empty:
                return {'status': 'erro', 'mensagem': 'Arquivo está vazio'}
            # A validação de colunas é simplificada, pois VALOR não é mais usado para lógica
            colunas_obrigatorias = ['OPERACAO', 'MATRICULA', 'CODIGO', 'REFERENCIA', 'PRAZO']
            colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
            if colunas_faltantes:
                return {'status': 'erro', 'mensagem': f'Colunas obrigatórias faltantes: {", ".join(colunas_faltantes)}'}
            if df['MATRICULA'].isna().all():
                return {'status': 'erro', 'mensagem': 'Coluna MATRICULA não possui dados válidos'}
            return {'status': 'sucesso', 'mensagem': 'Arquivo válido'}
        except Exception as e:
            return {'status': 'erro', 'mensagem': f'Erro ao validar arquivo: {str(e)}'}

    def processar_arquivos(self, arquivos_com_limites: list, pasta_destino: str,
                           gerar_analise: bool = True) -> dict:
        """Consolida e processa arquivos de ajuda de custo."""
        if not arquivos_com_limites:
            raise ValueError("Nenhum arquivo para processar foi fornecido.")
        os.makedirs(pasta_destino, exist_ok=True)

        dados_consolidados = {}

        # Etapa Única: Processar todos os arquivos de ajuda de custo
        self.log("\n--- Iniciando Processamento de Ajuda de Custo ---")
        for item in arquivos_com_limites:
            caminho_arquivo = item['caminho']
            nome_amigavel = item.get('nome_amigavel', os.path.basename(caminho_arquivo))
            limite_horas = item.get('limite_horas', self.LIMITE_PADRAO_HORAS)
            self.log(f"Lendo arquivo '{nome_amigavel}' (Limite de Horas: {limite_horas})")

            try:
                df = pd.read_excel(caminho_arquivo, dtype=str, engine='openpyxl')
                for _, row in df.iterrows():
                    matricula = self._limpar_campo(row.get('MATRICULA'))
                    codigo = self._limpar_campo(row.get('CODIGO'))
                    ref_val = pd.to_numeric(row.get('REFERENCIA'), errors='coerce')
                    ref_num = int(ref_val) if pd.notna(ref_val) else 0

                    if not matricula or (not codigo and ref_num == 0):
                        continue

                    if matricula not in dados_consolidados:
                        dados_consolidados[matricula] = {
                            'limite_horas': 0,
                            'detalhes_por_codigo': defaultdict(
                                lambda: {'soma_referencia': 0, 'operacao': 'I', 'prazo': '0', 'origens': set()})
                        }

                    dados_consolidados[matricula]['limite_horas'] = max(dados_consolidados[matricula]['limite_horas'],
                                                                        limite_horas)

                    detalhe_codigo = dados_consolidados[matricula]['detalhes_por_codigo'][codigo]
                    detalhe_codigo['soma_referencia'] += ref_num
                    detalhe_codigo['operacao'] = row.get('OPERACAO', 'I')
                    detalhe_codigo['prazo'] = self._limpar_campo(row.get('PRAZO', '0'))
                    detalhe_codigo['origens'].add(nome_amigavel)
            except Exception as e:
                self.log(f"Erro ao processar arquivo '{nome_amigavel}': {e}")
                continue

        # Etapa final: Geração dos arquivos
        self.log("\n--- Análise de horas e geração de arquivos ---")
        lista_final_para_df = []
        for matricula, data in dados_consolidados.items():
            for codigo, detalhes in data['detalhes_por_codigo'].items():
                soma_ref_bruta = detalhes['soma_referencia']
                h_majorada, h_normal = self._parse_referencia(soma_ref_bruta)
                total_horas = h_majorada + h_normal

                lista_final_para_df.append({
                    'MATRICULA': matricula, 'CODIGO': codigo, 'OPERACAO': detalhes['operacao'],
                    'PRAZO': detalhes['prazo'], 'VALOR': '',  # Coluna VALOR vazia por padrão
                    'REFERENCIA': soma_ref_bruta, 'H_NORMAL_ACO': h_normal, 'H_MAJORADA_ACO': h_majorada,
                    'TOTAL_HORAS': total_horas, 'LIMITE_HORAS_APLICADO': data['limite_horas'],
                    'ORIGEM_ARQUIVOS': ', '.join(sorted(list(detalhes['origens'])))
                })

        if not lista_final_para_df:
            self.log("Nenhum registro resultante após a consolidação.")
            return {"status": "sucesso", "mensagem": "Processamento concluído, mas nenhum registro válido encontrado.",
                    "caminhos_saida": {}}

        df_completo = pd.DataFrame(lista_final_para_df)

        # Filtro para o arquivo de implantação
        df_implantacao_filtrado = df_completo[df_completo['TOTAL_HORAS'] <= df_completo['LIMITE_HORAS_APLICADO']].copy()

        self.log(
            f"Encontrados {len(df_completo)} registros. Destes, {len(df_implantacao_filtrado)} estão dentro do limite para implantação.")

        # Geração dos arquivos
        caminhos_saida = {}
        colunas_implantacao = ['OPERACAO', 'MATRICULA', 'CODIGO', 'VALOR', 'REFERENCIA', 'PRAZO']
        df_implantacao_output = df_implantacao_filtrado[colunas_implantacao]
        caminho_implantacao = os.path.join(pasta_destino, "implantacao_demais_categorias.xlsx")
        df_implantacao_output.to_excel(caminho_implantacao, index=False)
        caminhos_saida["para_implantacao"] = caminho_implantacao
        self.log(f"✓ Arquivo de implantação salvo em: {caminho_implantacao}")

        if gerar_analise:
            try:
                caminho_analise = self._gerar_arquivo_analise(df_completo, pasta_destino)
                caminhos_saida["analise"] = caminho_analise
                self.log(f"✓ Arquivo de análise salvo em: {caminho_analise}")
            except Exception as e:
                self.log(f"⚠️ Erro ao gerar arquivo de análise: {e}")

        self.log("\n--- PROCESSAMENTO CONCLUÍDO ---")
        return {"status": "sucesso", "mensagem": "Processamento concluído com sucesso!",
                "caminhos_saida": caminhos_saida}

    def _gerar_arquivo_analise(self, df_analise_completo: pd.DataFrame, pasta_destino: str):
        """Gera um arquivo de análise simplificado."""
        caminho_analise = os.path.join(pasta_destino, "analise_demais_categorias.xlsx")

        df_analise_completo['LIMITE_EXCEDIDO'] = df_analise_completo['TOTAL_HORAS'] > df_analise_completo[
            'LIMITE_HORAS_APLICADO']

        with pd.ExcelWriter(caminho_analise, engine='openpyxl') as writer:
            df_analise_completo.to_excel(writer, sheet_name='Detalhes_Processamento_TODOS', index=False)

            # Resumo por Matrícula
            resumo_matricula = df_analise_completo.groupby('MATRICULA').agg(
                TOTAL_HORAS_ACO=('TOTAL_HORAS', 'sum'),
                LIMITE_HORAS=('LIMITE_HORAS_APLICADO', 'first'),
                LIMITE_EXCEDIDO=('LIMITE_EXCEDIDO', 'any')  # Se qualquer linha exceder, marca como excedido
            ).reset_index()
            resumo_matricula.to_excel(writer, sheet_name='Resumo_Matricula', index=False)

        return caminho_analise
