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
        }

        style = {**default_style, **kwargs}

        # --- CORREÇÃO APLICADA AQUI ---
        # Garante que os valores de dimensão sejam sempre inteiros para evitar o TclError.
        # Isso torna o widget mais robusto contra erros de scaling do customtkinter.
        for key in ["corner_radius", "border_width", "width", "height"]:
            if key in style:
                try:
                    style[key] = int(style[key])
                except (ValueError, TypeError):
                    # Se o valor não puder ser convertido, remove para usar o padrão da biblioteca
                    del style[key]

        # Chama o construtor da classe pai (ctk.CTkFrame) com os parâmetros sanitizados
        super().__init__(master=master, **style)


class TransparentFrame(ctk.CTkFrame):
    """
    Um CTkFrame padronizado com um fundo transparente.
    Útil para agrupar widgets sem adicionar um fundo visual.
    """

    def __init__(self, master, **kwargs):
        style = {"fg_color": "transparent", **kwargs}

        # Aplica a mesma correção por segurança, embora seja menos provável de ocorrer aqui.
        for key in ["corner_radius", "border_width", "width", "height"]:
            if key in style:
                try:
                    style[key] = int(style[key])
                except (ValueError, TypeError):
                    del style[key]

        super().__init__(master=master, **style)