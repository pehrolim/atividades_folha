# app/views/home_gui.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class HomeGUI(QWidget):
    """
    View para a tela inicial (Home) da aplicação.
    """
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label_boas_vindas = QLabel("Seja Bem-vindo à Aplicação!")
        font = QFont("Roboto", 24)
        font.setBold(True)
        label_boas_vindas.setFont(font)
        
        layout.addWidget(label_boas_vindas)