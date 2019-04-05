from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit


def is_blank(text):
    if text and text.strip():
        return False
    return True


def is_not_blank(text):
    if text and text.strip():
        return True
    return False


def show_error_dialog(error_message):
    err_dialog = QMessageBox()
    err_dialog.setIcon(QMessageBox.Critical)
    err_dialog.setText(error_message)
    err_dialog.setWindowTitle("Error")
    err_dialog.exec_()


def show_input_dialog(self, title, label):
    text, ok_pressed = QInputDialog.getText(self, title, label, QLineEdit.Normal, "")
    if ok_pressed and text != '':
        return text
    return ''
