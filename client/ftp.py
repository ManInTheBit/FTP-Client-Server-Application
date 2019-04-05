"""
   Created by burakisik on 27.03.2019.
"""
import os
import sys
from datetime import datetime
import ftplib

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QIntValidator, QStandardItemModel, QStandardItem, QIcon, QCursor
from PyQt5.QtWidgets import QFileSystemModel, QTableView, QMenu, QAction, QLineEdit
from client.utility import show_error_dialog, is_not_blank, show_input_dialog


class MainWindow(QtWidgets.QMainWindow):
    connection_status = 0
    file_path = ''
    ftp = ftplib.FTP('')

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = uic.loadUi('ftp.ui', self)
        self.model = QFileSystemModel()
        self.setFixedSize(810, 563)
        self.init_ui()
        self.bind_event()
        self.set_validation_type()

    def init_ui(self):
        self.populate_local_tree_view()
        self.show()

    def populate_local_tree_view(self):
        self.fsm = QFileSystemModel(self)
        self.fsm.setRootPath('')
        self.fsm.setReadOnly(True)
        # self.fsm.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.ui.local_tree_view.setModel(self.fsm)
        self.local_tree_view.setRootIndex(self.fsm.index(self.fsm.rootPath()))
        self.ui.local_tree_view.setAnimated(False)
        self.ui.local_tree_view.setIndentation(20)
        self.ui.local_tree_view.setSortingEnabled(True)

    def bind_event(self):
        self.ui.btn_login.clicked.connect(self.on_login_click)
        self.ui.local_tree_view.clicked.connect(self.on_tree_view_clicked)
        # self.ui.tableView.doubleClicked.connect(self.on_click)

    def on_tree_view_clicked(self, index):
        index_item = self.fsm.index(index.row(), 0, index.parent())
        path = str(self.fsm.filePath(index_item))
        self.selected_file_path = path

    def set_validation_type(self):
        only_int = QIntValidator()
        self.ui.input_port_number.setValidator(only_int)  # allowing only integer input
        self.ui.input_password.setEchoMode(QLineEdit.Password)

    @pyqtSlot()
    def on_login_click(self):
        if self.connection_status == 0:
            host_name = self.ui.input_host_name.text().strip()
            usr = self.ui.input_username.text().strip()
            password = self.ui.input_password.text().strip()
            port_number = self.ui.input_port_number.text().strip()

            if is_not_blank(host_name) and is_not_blank(usr) and is_not_blank(password) and is_not_blank(port_number):
                port_number = int(port_number)
                try:
                    self.ftp.connect(host_name, port_number)
                    self.ftp.login(usr, password)

                    self.add_item_to_log_list_widget("login successful")
                    self.ui.btn_login.setText("Disconnect")
                    self.connection_status = 1
                    self.get_remote_file()
                except ftplib.all_errors:
                    self.add_item_to_log_list_widget("logged in incorrect credentials")
                    show_error_dialog("Please check your credentials")
            else:
                show_error_dialog("Please enter all credentials")
        else:
            self.logout()

    def get_remote_file(self):
        self.model = QStandardItemModel()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(['Name', 'Size', 'Last Modified'])

        files = self.ftp.nlst()
        i = 0
        for filename in files:
            self.add_row_item(i, 0, self.model, filename)
            try:
                self.ftp.voidcmd('TYPE I')
                size = str(self.ftp.size(filename))
                size = size + " KB"
                self.add_row_item(i, 1, self.model, size)
                modified_time = self.ftp.sendcmd('MDTM ' + filename)
                formatted_time = datetime.strptime(modified_time[4:], "%Y%m%d%H%M%S").strftime("%d %B %Y %H:%M:%S")
                self.add_row_item(i, 2, self.model, formatted_time)
                self.add_item_to_log_list_widget("remote directory listing successful")
            except:
                item = QStandardItem(filename)
                item.setTextAlignment(Qt.AlignVCenter)
                item.setEditable(False)
                self.model.setItem(i, 0, item)
                item.setIcon(QIcon("static/ic_folder.png"))
            i += 1
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.set_property()

    @staticmethod
    def add_row_item(row, column, model, text):
        item = QStandardItem(text)
        item.setTextAlignment(Qt.AlignVCenter)
        item.setEditable(False)
        model.setItem(row, column, item)

    def set_property(self):
        self.ui.tableView.setColumnWidth(0, 120)
        self.ui.tableView.setColumnWidth(1, 120)
        self.ui.tableView.setColumnWidth(2, 160)
        self.ui.tableView.setShowGrid(False)
        header = self.ui.tableView.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignVCenter)

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        rename_action = QAction('Rename', self)
        rename_action.triggered.connect(lambda: self.rename_slot(event))
        self.menu.addAction(rename_action)

        delete_action = QAction('Delete', self)
        delete_action.triggered.connect(lambda: self.delete_slot(event))
        self.menu.addAction(delete_action)

        download_action = QAction('Download', self)
        download_action.triggered.connect(lambda: self.download_slot(event))
        self.menu.addAction(download_action)

        create_dir_action = QAction('New Dir', self)
        create_dir_action.triggered.connect(lambda: self.create_dir_slot(event))
        self.menu.addAction(create_dir_action)

        upload_file_action = QAction('Upload', self)
        upload_file_action.triggered.connect(lambda: self.upload_file_slot(event))
        self.menu.addAction(upload_file_action)

        self.menu.popup(QCursor.pos())

    @pyqtSlot()
    def rename_slot(self, event):
        # indexes = self.ui.tableView.selectionModel().selectedRows()
        # for index in sorted(indexes):
        # print('Row %d is selected' % index.row())
        for index in sorted(self.ui.tableView.selectionModel().selectedRows()):
            selected_filename = self.model.data(self.model.index(index.row(), 0))
            new_name = show_input_dialog(self, "Rename", "New Name")
            if new_name != '' and len(new_name) != 0:
                try:
                    self.ftp.rename(selected_filename, new_name)
                    self.get_remote_file()
                    self.add_item_to_log_list_widget(
                        selected_filename + " change with " + new_name + " successfully on remote")
                except:
                    show_error_dialog("Unexpected error occurred")
            else:
                show_error_dialog("Invalid file name")
            break  # just rename one file

    @pyqtSlot()
    def delete_slot(self, event):
        for index in sorted(self.ui.tableView.selectionModel().selectedRows()):
            try:
                selected_filename = self.model.data(self.model.index(index.row(), 0))
                self.ftp.rmd(selected_filename)
                self.add_item_to_log_list_widget(selected_filename + " deleted on remote")
            except:
                print("")

    @pyqtSlot()
    def download_slot(self, event):
        for index in sorted(self.ui.tableView.selectionModel().selectedRows()):
            selected_filename = str(self.model.data(self.model.index(index.row(), 0)))
            try:
                local_file = open(selected_filename, 'wb')
                self.ftp.retrbinary('RETR ' + selected_filename, local_file.write, 1024)
                local_file.close()
                self.add_item_to_log_list_widget(selected_filename + "file is downloaded successfully")
            except Exception as e:
                print(e)  # show_error_dialog("Unexpected error occurred")

    @pyqtSlot()
    def create_dir_slot(self, event):
        self.add_item_to_log_list_widget("test file is downloaded successfully")
        file_name = show_input_dialog(self, "New Directory", "Directory Name")
        try:
            if file_name != '' and len(file_name) != 0:
                self.ftp.mkd(file_name)
                self.get_remote_file()
                self.add_item_to_log_list_widget(file_name + " created successfully")
            else:
                show_error_dialog("Invalid directory name")
        except:
            print("")

    @pyqtSlot()
    def upload_file_slot(self, event):
        try:
            if os.path.isfile(self.file_path):
                file_name = os.path.basename(self.file_path)
                self.ftp.storbinary('STOR ' + file_name, open(self.file_path, 'rb'))
                self.get_remote_file()
                self.add_item_to_log_list_widget(file_name + " uploaded successfully")
        except:
            show_error_dialog("Please choose only one file")

    @pyqtSlot()
    def on_delete_file_click(self):
        files = list(self.ftp.nlst())
        for f in files:
            self.ftp.delete(f)

    def get_size(self, directory):
        size = 0
        for file in self.ftp.nlst(directory):
            size += self.ftp.size(file)
        return size

    def add_item_to_log_list_widget(self, log):
        self.ui.log_list_widget.addItem("status\t" + log)

    def logout(self):
        self.ftp.close()
        self.add_item_to_log_list_widget("logout successfully")
        self.connection_status = 0
        self.ui.btn_login.setText("Connect")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
