# app/widgets/custom_labels.py

import customtkinter as ctk

class TitleLabel(ctk.CTkLabel):
    """Um label padronizado para títulos de seções."""
    # CORREÇÃO: 'text' é agora opcional e 'textvariable' é aceito.
    def __init__(self, master, text=None, textvariable=None, **kwargs):
        style = {
            "font": ("Roboto", 14, "bold"),
            **kwargs
        }
        # Passa ambos para o construtor pai.
        super().__init__(master=master, text=text, textvariable=textvariable, **style)

class InfoLabel(ctk.CTkLabel):
    """Um label padronizado para textos informativos (descrições)."""
    # CORREÇÃO: 'text' é agora opcional e 'textvariable' é aceito.
    def __init__(self, master, text=None, textvariable=None, **kwargs):
        style = {
            "font": ("Roboto", 11),
            **kwargs
        }
        # Passa ambos para o construtor pai.
        super().__init__(master=master, text=text, textvariable=textvariable, **style)

class ValueLabel(ctk.CTkLabel):
    """Um label para exibir valores, como caminhos de pasta, em preto/branco e negrito."""
    # CORREÇÃO: 'text' é agora opcional e 'textvariable' é aceito.
    def __init__(self, master, text=None, textvariable=None, **kwargs):
        style = {
            "font": ("Roboto", 11, "bold"),
            "text_color": ("#000000", "#FFFFFF"),
            **kwargs
        }
        # Passa ambos para o construtor pai.
        super().__init__(master=master, text=text, textvariable=textvariable, **style)
