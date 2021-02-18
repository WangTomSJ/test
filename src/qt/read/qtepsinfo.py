import weakref

from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidget, QLabel, QListWidgetItem

from src.index.book import BookMgr
from src.qt.com.qtloading import QtLoading
from src.util.status import Status
from ui.qtepsinfo import Ui_EpsInfo


class QtEpsInfo(QtWidgets.QWidget, Ui_EpsInfo):
    def __init__(self, owner):
        super(self.__class__, self).__init__()
        Ui_EpsInfo.__init__(self)
        self.setupUi(self)
        self.owner = weakref.ref(owner)

        self.epsListWidget = QListWidget()
        self.epsListWidget.setFlow(self.epsListWidget.LeftToRight)
        self.epsListWidget.setWrapping(True)
        self.epsListWidget.setFrameShape(self.epsListWidget.NoFrame)
        self.epsListWidget.setResizeMode(self.epsListWidget.Adjust)
        self.epsListWidget.itemClicked.connect(self.SelectEps)
        self.gridLayout_2.addWidget(self.epsListWidget, 1, 0)
        self.closeFlag = self.__class__.__name__
        self.bookId = ""
        self.loadingForm = QtLoading(self)
        self.setWindowTitle("章节列表")

        self.greed = QColor(18, 161, 130)
        self.blue = QColor(97, 154, 195)
        self.white = QColor(0, 0, 0, 0)

    def OpenEpsInfo(self, bookId):
        self.show()
        self.loadingForm.show()
        self.bookId = bookId
        self.epsListWidget.clear()
        if bookId not in BookMgr().books:
            self.owner().qtTask.AddHttpTask(lambda x: BookMgr().AddBookById(self.bookId, x), self.OpenBookInfoBack,
                                            cleanFlag=self.closeFlag)
        else:
            self.owner().qtTask.AddHttpTask(lambda x: BookMgr().AddBookEpsInfo(self.bookId, x), self.OpenEpsInfoBack,
                                            cleanFlag=self.closeFlag)

    def OpenBookInfoBack(self, msg):
        if msg == Status.Ok:
            self.owner().qtTask.AddHttpTask(lambda x: BookMgr().AddBookEpsInfo(self.bookId, x), self.OpenEpsInfoBack,
                                            cleanFlag=self.closeFlag)
        else:
            self.loadingForm.close()

    def OpenEpsInfoBack(self, msg):
        self.loadingForm.close()
        self.epsListWidget.clear()
        if msg == Status.Ok:
            self.UpdateEpsInfo()
        return

    def UpdateEpsInfo(self):
        self.epsListWidget.clear()
        info = BookMgr().books.get(self.bookId)
        if not info:
            return
        downloadEpsId = self.owner().downloadForm.GetDownloadEpsId(self.bookId)
        for index, epsInfo in enumerate(info.eps):
            label = QLabel(epsInfo.title)
            label.setContentsMargins(20, 10, 20, 10)
            item = QListWidgetItem(self.epsListWidget)
            item.setSizeHint(label.sizeHint())
            if index in downloadEpsId:
                item.setBackground(self.greed)
            else:
                item.setBackground(self.white)
            self.epsListWidget.setItemWidget(item, label)

    def SelectEps(self, item):
        if item.background().color() == self.greed:
            return
        elif item.background().color() == self.blue:
            item.setBackground(self.white)
        else:
            item.setBackground(self.blue)
        return

    def SelectAll(self):
        for i in range(self.epsListWidget.count()):
            item = self.epsListWidget.item(i)
            if item.background().color() == self.greed:
                continue
            item.setBackground(self.blue)
        return

    def CancleSelect(self):
        for i in range(self.epsListWidget.count()):
            item = self.epsListWidget.item(i)
            if item.background().color() == self.greed:
                continue
            item.setBackground(self.white)
        return

    def StartDownload(self):
        downloadIds = []
        for i in range(self.epsListWidget.count()):
            item = self.epsListWidget.item(i)
            if item.background().color() == self.blue:
                downloadIds.append(i)
        if not downloadIds:
            return
        self.owner().downloadForm.AddDownload(self.bookId, downloadIds)
        self.UpdateEpsInfo()
        return
