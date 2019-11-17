from PyQt5 import QtGui, QtCore, QtWidgets
from ui_pdf2img_tableview import Ui_MainWindow
import sys
import fitz
import math

class Pdf2ImgTableview(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setup_ui()
        self.setup_logic()
        self.setup_events()

    ########################################
    #       init methods
    ########################################
    def setup_ui(self):
        # UI variables should be stored here.
        self.screen = QtWidgets.QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, 
                        int(self.screen.width() * 3/4),
                        int(self.screen.height() * 3/4))
        self.setCentralWidget(self.table)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

    def setup_logic(self):
        # logical variables stored here
        self.num_columns = 8
        self.num_rows = -1              # determined dynamically by #pages
        self.axis_ratio = 0.7071        # w/h ratio is 1/sqrt(2), A4 standard
        self.page_width = int(self.screen.width() / 8)
        self.page_height = int(self.page_width / self.axis_ratio)
        # page doc logics
        self.pdf_doc = None             # determined when loading a doc
        self.num_pages = -1             # determined when loading a doc

    def setup_events(self):
        self.actionQuit.triggered.connect(self.close)
        self.actionOpen.triggered.connect(self.on_open)

    ########################################
    #             events
    ########################################
    @QtCore.pyqtSlot()
    def on_open(self):
        """
        Event function triggered when the "Open" action in the menu
        is clicked or when the corresponding shortcut is pressed.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open PDF File",
            "C:\\",
            "PDF Files (*.pdf)"
        )
        if filename:
            self.load_doc(filename)
    
    ########################################
    #       interfacing methods
    ########################################
    def load_doc(self, filename):
        doc = fitz.open(filename)
        if doc is None:
            raise Exception("Error in loading {}!".format(filename))
        # setup local logical variables
        self.pdf_doc = doc
        self.num_pages = doc.pageCount
        self.num_rows = int(math.ceil(self.num_pages / self.num_columns))
        # setup UI accordingly
        try:
            self.refresh_table()
        except:
            QtWidgets.QMessageBox.critical(
                self,
                "PDF to Image Converter",
                "Error occurred in loading pages to table!",
                QtWidgets.QMessageBox.Ok
            )
        self.statusBar().showMessage("{} loaded.".format(filename))
    
    def refresh_table(self):
        """
        Based on the logical variables, update the table accordingly.
        Firstly, it checks whether a pdf doc has been loaded. If not,
        raise an exception.
        """
        assert self.pdf_doc is not None
        # set # of rows and columns
        self.table.setColumnCount(self.num_columns)
        assert self.num_rows > 0
        self.table.setRowCount(self.num_rows)
        # set cell dimensions
        for i in range(self.num_rows):
            self.table.setRowHeight(i, self.page_height) # set height of each row
        for i in range(self.num_columns):
            self.table.setColumnWidth(i, self.page_width) # set width of each col
        # load pages to each table cell
        for page_num in range(self.num_pages):
            row_num, col_num = self.get_table_position(page_num)
            qtimg = self.page_to_qimage(self.pdf_doc[page_num])
            lblCover = QtWidgets.QLabel(self)
            lblCover.setFixedSize(self.page_width, self.page_height)
            self.table.setCellWidget(row_num, col_num, lblCover)
            print("Size of lblCover: {}x{}".format(lblCover.width(), lblCover.height()))
            print("Size of screen: {}x{}".format(self.screen.width(), self.screen.height()))
            print("Size of each logical cell: {}x{}".format(self.page_width, self.page_height))
            lblCover.setScaledContents(True)
            lblCover.setPixmap(QtGui.QPixmap.fromImage(qtimg))
            del lblCover


    ########################################
    #       internal methods
    ########################################
    def page_to_qimage(self, pdf_page, zoom=1.0):
        """
        Take a pdf_page object, return a QImage object.
        """
        matrix = fitz.Matrix(zoom, zoom)
        pix = pdf_page.getPixmap(matrix=matrix)
        return QtGui.QImage(pix.samples, 
                    pix.width, pix.height, pix.stride, 
                    QtGui.QImage.Format_RGB888)

    def get_table_position(self, page_number):
        """
        Given a page number, return which row and which column
        the page should be at. For example, Page 0 should be at
        0th row and 0th column, whereas Page 8 should be at
        1st row and 0th column.
        """
        assert self.pdf_doc is not None
        assert (isinstance(page_number, int) and 
                page_number >= 0 and 
                page_number < self.num_pages)
        return (page_number // self.num_columns, page_number % self.num_columns)

    def get_page_number_at(self, row_num, col_num):
        """
        Given the position of a page in the table, return the page number.
        
        Raises exception if `row_num` or `col_num` is out of index, but does not
        raise en exception when the page_number returned is out of the current
        pdf_doc's total number of pages. User should manually check that.
        """
        assert self.pdf_doc is not None
        assert isinstance(row_num, int) and isinstance(col_num, int)
        assert 0 <= row_num < self.num_rows
        assert 0 <= col_num < self.num_columns
        return row_num * self.num_columns + col_num


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = Pdf2ImgTableview()
    win.show()
    sys.exit(app.exec_())


