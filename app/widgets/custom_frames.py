# app/widgets/custom_frames.py

import customtkinter as ctk

class StandardFrame(ctk.CTkFrame):
    """
    Um CTkFrame padronizado para seções principais e contêineres da aplicação.
    Define um estilo visual consistente.
    """
    def __init__(self, master, **kwargs):
        """
        Construtor do StandardFrame.

        Args:
            master: O widget pai.
            **kwargs: Outros argumentos que CTkFrame possa aceitar para sobrescrever o padrão.
        """
        # Define os parâmetros de estilo padrão aqui
        default_style = {
            "corner_radius": 10,
            "border_width": 0
            # Você pode adicionar outras propriedades padrão aqui, como "fg_color"
        }

        # Atualiza o estilo padrão com quaisquer argumentos passados
        style = {**default_style, **kwargs}

        # Chama o construtor da classe pai (ctk.CTkFrame) com todos os parâmetros
        super().__init__(master=master, **style)

class TransparentFrame(ctk.CTkFrame):
    """
    Um CTkFrame padronizado com um fundo transparente.
    Útil para agrupar widgets sem adicionar um fundo visual.
    """
    def __init__(self, master, **kwargs):
        style = {"fg_color": "transparent", **kwargs}
        super().__init__(master=master, **style)
