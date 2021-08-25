from PySide2 import QtWidgets
from PySide2.QtCore import QUrl
from PySide2.QtGui import QDesktopServices, Qt

from src.qt.com.qtbubblelabel import QtBubbleLabel
from src.qt.qtmain import QtOwner
from src.qt.util.qttask import QtTaskBase
from src.server import req, config, Server, Log
from ui.login_proxy import Ui_LoginProxy


class QtLoginProxy(QtWidgets.QWidget, Ui_LoginProxy, QtTaskBase):
    def __init__(self):
        super(self.__class__, self).__init__()
        Ui_LoginProxy.__init__(self)
        QtTaskBase.__init__(self)
        self.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)
        self.speedTest = []
        self.speedIndex = 0
        self.speedPingNum = 0
        self.buttonGroup.setId(self.radioButton_1, 1)
        self.buttonGroup.setId(self.radioButton_2, 2)
        self.buttonGroup.setId(self.radioButton_3, 3)
        self.buttonGroup.setId(self.radioButton_4, 4)
        self.LoadSetting()
        self.UpdateServer()

    def show(self):
        self.LoadSetting()
        super(self.__class__, self).show()

    def SetEnabled(self, enabled):
        self.testSpeedButton.setEnabled(enabled)
        self.saveButton.setEnabled(enabled)
        self.httpLine.setEnabled(enabled)
        self.cdnIp.setEnabled(enabled)
        self.radioButton_1.setEnabled(enabled)
        self.radioButton_2.setEnabled(enabled)
        self.radioButton_3.setEnabled(enabled)
        self.radioButton_4.setEnabled(enabled)

    def SpeedTest(self):
        self.speedIndex = 0
        self.speedPingNum = 0
        self.speedTest = []

        for i in range(1, 9):
            label = getattr(self, "label" + str(i))
            label.setText("")

        self.speedTest = [("", "", False, 1), ("", "", True, 2)]
        i = 3
        for address in config.Address:
            self.speedTest.append((address, config.ImageServer, False, i))
            i += 1
            self.speedTest.append((address, config.ImageServer, True, i))
            i += 1

        PreferCDNIP = self.cdnIp.text()
        if PreferCDNIP:
            self.speedTest.append((PreferCDNIP, PreferCDNIP, False, i))
            i += 1
            self.speedTest.append((PreferCDNIP, PreferCDNIP, True, i))
            i += 1

        self.StartSpeedPing()

    def StartSpeedPing(self):
        for v in self.speedTest:
            address, imageProxy, isHttpProxy, i = v
            httpProxy = self.httpLine.text()
            if isHttpProxy and not httpProxy:
                label = getattr(self, "label"+str(i))
                label.setText("无代理")
                self.speedPingNum += 1
                continue

            request = req.SpeedTestPingReq()
            if isHttpProxy:
                request.proxy = {"http": httpProxy, "https": httpProxy}
            else:
                request.proxy = ""
            self.AddHttpTask(lambda x: Server().TestSpeedPing(request, x, address, imageProxy), self.SpeedTestPingBack, i)
        return

    def SpeedTestPingBack(self, data, i):
        label = getattr(self, "label" + str(i))
        if float(data) > 0.0:
            label.setText("<font color=#7fb80e>{}</font>".format(str(int(float(data)*500)) + "ms") + "/")
        else:
            label.setText("<font color=#d71345>{}</font>".format("fail") + "/")
        self.speedPingNum += 1
        if self.speedPingNum >= len(self.speedTest):
            self.StartSpeedTest()
        return

    def StartSpeedTest(self):
        if len(self.speedTest) <= self.speedIndex:
            self.SetEnabled(True)
            return

        address, imageProxy, isHttpProxy, i = self.speedTest[self.speedIndex]
        httpProxy = self.httpLine.text()
        if isHttpProxy and not httpProxy:
            label = getattr(self, "label" + str(i))
            label.setText("无代理")
            self.speedIndex += 1
            self.StartSpeedTest()
            return

        request = req.SpeedTestReq()
        # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2MDEyMjg3YzYxYWFlODJmZDJjMGQzNTUiLCJlbWFpbCI6InRvbnF1ZXIyIiwicm9sZSI6Im1lbWJlciIsIm5hbWUiOiJ0b25xdWVyMiIsInZlcnNpb24iOiIyLjIuMS4zLjMuNCIsImJ1aWxkVmVyc2lvbiI6IjQ1IiwicGxhdGZvcm0iOiJhbmRyb2lkIiwiaWF0IjoxNjE0MjQxODY1LCJleHAiOjE2MTQ4NDY2NjV9.ZUmRP319zREBHk3ax_dJh-qeUDFLmOg_RQBPAMWN8II"
        testIp = address
        if isHttpProxy:
            request.proxy = {"http": httpProxy, "https": httpProxy}
        else:
            request.proxy = ""
        self.AddHttpTask(lambda x: Server().TestSpeed(request, x, testIp, imageProxy), self.SpeedTestBack, i)
        return

    def SpeedTestBack(self, data, i):
        if not data:
            data = "<font color=#d71345>fail</font>"
        else:
            data = "<font color=#7fb80e>{}</font>".format(data)
        label = getattr(self, "label" + str(i))
        label.setText(label.text()+data)
        self.speedIndex += 1
        self.StartSpeedTest()
        return

    def LoadSetting(self):
        config.PreferCDNIP = QtOwner().owner.settingForm.GetSettingV("Proxy/PreferCDNIP", config.PreferCDNIP)
        config.ProxySelectIndex = QtOwner().owner.settingForm.GetSettingV("Proxy/ProxySelectIndex", config.ProxySelectIndex)
        httpProxy = QtOwner().owner.settingForm.GetSettingV("Proxy/Http", config.HttpProxy)
        self.proxyBox.setChecked(config.IsHttpProxy)
        self.httpLine.setText(httpProxy)
        button = getattr(self, "radioButton_{}".format(config.ProxySelectIndex))
        button.setChecked(True)
        self.cdnIp.setText(config.PreferCDNIP)

    def UpdateServer(self):
        if config.ProxySelectIndex == 1:
            Server().imageServer = ""
            Server().address = ""
        elif config.ProxySelectIndex == 2:
            Server().imageServer = config.ImageServer
            Server().address = config.Address[0]
        elif config.ProxySelectIndex == 3:
            Server().imageServer = config.ImageServer
            Server().address = config.Address[1]
        else:
            Server().imageServer = config.PreferCDNIP
            Server().address = config.PreferCDNIP
        Log.Info("update proxy, setId:{}, image server:{}, address:{}".format(config.ProxySelectIndex, Server().imageServer, Server().address))

    def SaveSetting(self):
        config.PreferCDNIP = self.cdnIp.text()
        config.IsHttpProxy = int(self.proxyBox.isChecked())
        httpProxy = self.httpLine.text()
        config.ProxySelectIndex = self.buttonGroup.checkedId()
        QtOwner().owner.settingForm.SetSettingV("Proxy/ProxySelectIndex", config.ProxySelectIndex)
        QtOwner().owner.settingForm.SetSettingV("Proxy/PreferCDNIP", config.PreferCDNIP)
        QtOwner().owner.settingForm.SetSettingV("Proxy/Http", httpProxy)
        QtOwner().owner.settingForm.SetSettingV("Proxy/IsHttp", config.IsHttpProxy)
        self.UpdateServer()
        QtBubbleLabel().ShowMsgEx(self, "保存成功")
        self.close()
        return

    def OpenUrl(self):
        QDesktopServices.openUrl(QUrl(config.ProxyUrl))