from PyQt6.QtWidgets import QFrame, QSizePolicy


class QHSeparationLine(QFrame):
    """a horizontal separation line"""
    def __init__(self, line_width: int = 1):
        if not 0 <= line_width <= 3:
            # needs to be a value between 0 and 3
            raise ValueError('line_width out of range')

        super().__init__()
        self.setMinimumWidth(1)
        self.setFixedHeight(20)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setLineWidth(line_width)
