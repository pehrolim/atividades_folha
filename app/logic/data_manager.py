import pandas as pd
from datetime import datetime
import os
from io import StringIO


class DataManager:
    """
    Gerencia o DataFrame acumulado e as operações de dados relacionadas à folha.
    Também fornece métodos de utilidade estáticos para operações com DataFrames.
    """

    def __init__(self, columns):
        self.columns = columns
        self.df_acumulado = pd.DataFrame(columns=self.columns)

    # --- Métodos de Instância (operam em self.df_acumulado) ---

    def adicionar_dados_do_txt(self, conteudo_arquivo: str) -> int:
        """Adiciona dados de um TXT ao DataFrame acumulado."""
        try:
            df_novo = pd.read_csv(StringIO(conteudo_arquivo), sep=",", names=self.columns, header=None)
            linhas_antes = len(self.df_acumulado)
            self.df_acumulado = pd.concat([self.df_acumulado, df_novo], ignore_index=True)
            self.df_acumulado.drop_duplicates(inplace=True)
            return len(self.df_acumulado) - linhas_antes
        except Exception as e:
            raise ValueError(f"Erro ao processar conteúdo do arquivo para DataFrame: {e}")

    def obter_dados_acumulados(self) -> pd.DataFrame:
        """Retorna uma cópia do DataFrame acumulado."""
        return self.df_acumulado.copy()

    def limpar_dados(self):
        """Limpa o DataFrame acumulado."""
        self.df_acumulado = pd.DataFrame(columns=self.columns)
##
    def esta_vazio(self) -> bool:
        """Verifica se o DataFrame acumulado está vazio."""
        return self.df_acumulado.empty

    # --- Métodos de salvamento que usam os dados da instância ---

    def salvar_para_csv(self, filepath: str):
        """Salva o DataFrame acumulado da instância em um arquivo CSV."""
        if self.df_acumulado.empty:
            raise ValueError("Não há dados para salvar em CSV.")
        self.df_acumulado.to_csv(filepath, index=False, encoding='utf-8-sig')

    def salvar_para_xlsx(self, filepath: str):
        """Salva o DataFrame acumulado da instância em um arquivo XLSX."""
        if self.df_acumulado.empty:
            raise ValueError("Não há dados para salvar em XLSX.")
        self.df_acumulado.to_excel(filepath, index=False)

    # --- Métodos de Utilidade Estáticos (podem ser chamados de qualquer lugar) ---

    @staticmethod
    def save_df_to_xlsx(df: pd.DataFrame, filepath: str):
        """
        Salva um DataFrame qualquer em um arquivo XLSX.
        Método estático para ser usado como uma função de utilidade.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("O DataFrame fornecido está vazio ou é inválido.")
        df.to_excel(filepath, index=False)

    @staticmethod
    def generate_report_filename(prefix: str, extension: str) -> str:
        """
        Gera um nome de arquivo padronizado para relatórios.
        Ex: relatorio_sucesso_20250717_183055.xlsx
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.{extension}"
    @staticmethod
    def converter_para_numero(valor):
        if valor is None:
            return None

        valor_str = str(valor).strip()

        if not valor_str:
            return None
        valor_str = valor_str.lower().replace('r$', '').strip()

        try:
            if ',' in valor_str:
                valor_limpo = valor_str.replace('.', '').replace(',', '.')
                return float(valor_limpo)
            else:
                return float(valor_str)
                
        except (ValueError, TypeError):
            return None

