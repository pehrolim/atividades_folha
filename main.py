# main.py
import sys
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Define uma folha de estilos global para um visual mais moderno
    app.setStyleSheet("""
        QWidget {
            font-family: Roboto, Segoe UI, Arial;
            font-size: 11pt;
        }
        QHeaderView::section {
            background-color: #f0f0f0;
            padding: 4px;
            border: 1px solid #dcdcdc;
            font-weight: bold;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())