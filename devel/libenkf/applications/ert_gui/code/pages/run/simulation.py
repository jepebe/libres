from __future__ import division
from PyQt4 import QtGui, QtCore
from widgets.util import resourceIcon, resourceStateIcon, shortTime
import time
import ertwrapper


class SimulationList(QtGui.QListWidget):
    def __init__(self):
        QtGui.QListWidget.__init__(self)

        self.setViewMode(QtGui.QListView.IconMode)
        self.setMovement(QtGui.QListView.Static)
        self.setResizeMode(QtGui.QListView.Adjust)

        self.setItemDelegate(SimulationItemDelegate())
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSelectionRectVisible(False)

        self.setSortingEnabled(True)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        
class SimulationItem(QtGui.QListWidgetItem):
    def __init__(self, simulation):
        self.simulation = simulation
        QtGui.QListWidgetItem.__init__(self, type=9901)
        self.updateSimulation()

    def updateSimulation(self):
        self.setData(QtCore.Qt.DisplayRole, self.simulation)

    def __ge__(self, other):
        return self.simulation >= other.simulation

    def __lt__(self, other):
        return not self >= other


class SimulationItemDelegate(QtGui.QStyledItemDelegate):
    waiting = QtGui.QColor(200, 200, 255)
    running = QtGui.QColor(200, 255, 200)
    failed = QtGui.QColor(255, 200, 200)
    unknown = QtGui.QColor(255, 200, 128)
    userkilled = QtGui.QColor(255, 255, 200)
    finished = QtGui.QColor(200, 200, 200)
    notactive = QtGui.QColor(255, 255, 255)

    size = QtCore.QSize(32, 18)

    def __init__(self):
        QtGui.QStyledItemDelegate.__init__(self)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        data = index.model().data(index)

        if data is None:
            data = Simulation("0")
            data.status = 0
        else:
            data = data.toPyObject()

        if data.isWaiting():
            color = self.waiting
        elif data.isRunning():
            color = self.running
        elif data.finishedSuccesfully():
            color = self.finished
        elif data.hasFailed():
            color = self.failed
        elif data.notActive():
            color = self.notactive
        elif data.isUserKilled():
            color = self.userkilled
        else:
            color = self.unknown

        painter.setPen(color)
        rect = QtCore.QRect(option.rect)
        rect.setX(rect.x() + 1)
        rect.setY(rect.y() + 1)
        rect.setWidth(rect.width() - 2)
        rect.setHeight(rect.height() - 2)
        painter.fillRect(rect, color)

        painter.setPen(QtCore.Qt.black)

        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        painter.drawRect(rect)

        if option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(option.rect, QtGui.QColor(255, 255, 255, 150))

        painter.drawText(rect, QtCore.Qt.AlignCenter + QtCore.Qt.AlignVCenter, str(data.name))

        painter.restore()

    def sizeHint(self, option, index):
        return self.size


class SimulationPanel(QtGui.QStackedWidget):


    def __init__(self, parent=None):
        QtGui.QStackedWidget.__init__(self, parent)
        self.setFrameShape(QtGui.QFrame.Panel)
        self.setFrameShadow(QtGui.QFrame.Raised)

        self.setMinimumWidth(200)
        self.setMaximumWidth(200)

        self.ctrl = SimulationPanelController(self)

        self.createNoSelectionsPanel()
        self.createSingleSelectionsPanel()
        self.createManySelectionsPanel()

        self.addWidget(self.noSimulationsPanel)
        self.addWidget(self.singleSimulationsPanel)
        self.addWidget(self.manySimulationsPanel)

        
    def createButtons(self):
        self.killButton = QtGui.QToolButton(self)
        self.killButton.setIcon(resourceIcon("cross"))
        self.killButton.setToolTip("Kill job")
        self.connect(self.killButton, QtCore.SIGNAL('clicked()'), self.ctrl.kill)

        self.restartButton = QtGui.QToolButton(self)
        self.restartButton.setIcon(resourceIcon("refresh"))
        self.restartButton.setToolTip("Restart job")
        self.connect(self.restartButton, QtCore.SIGNAL('clicked()'), lambda : self.ctrl.restart(False))

        self.rrButton = QtGui.QToolButton(self)
        self.rrButton.setIcon(resourceIcon("refresh_resample"))
        self.rrButton.setToolTip("Resample and restart job")
        self.connect(self.rrButton, QtCore.SIGNAL('clicked()'), lambda : self.ctrl.restart(True))

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.killButton)
        buttonLayout.addWidget(self.restartButton)
        buttonLayout.addWidget(self.rrButton)

        return buttonLayout

    def createButtonedLayout(self, layout, stretch=True):
        btnlayout = QtGui.QVBoxLayout()
        btnlayout.addLayout(layout)

        if stretch:
            btnlayout.addStretch(1)

        btnlayout.addLayout(self.createButtons())
        return btnlayout


    def createManySelectionsPanel(self):
        self.manySimulationsPanel = QtGui.QWidget()

        layout = QtGui.QVBoxLayout()
        label = QtGui.QLabel("Selected jobs:")
        label.setAlignment(QtCore.Qt.AlignHCenter)
        layout.addWidget(label)

        self.selectedSimulationsLabel = QtGui.QLabel()
        self.selectedSimulationsLabel.setWordWrap(True)
        font = self.selectedSimulationsLabel.font()
        font.setWeight(QtGui.QFont.Bold)
        self.selectedSimulationsLabel.setFont(font)

        scrolledLabel = QtGui.QScrollArea()
        scrolledLabel.setWidget(self.selectedSimulationsLabel)
        scrolledLabel.setWidgetResizable(True)
        layout.addWidget(scrolledLabel)

        self.manySimulationsPanel.setLayout(self.createButtonedLayout(layout, False))

    def createSingleSelectionsPanel(self):
        self.singleSimulationsPanel = QtGui.QWidget()

        layout = QtGui.QFormLayout()
        layout.setLabelAlignment(QtCore.Qt.AlignRight)
        self.jobLabel = QtGui.QLabel()
        self.submitLabel = QtGui.QLabel()
        self.startLabel = QtGui.QLabel()
        self.finishLabel = QtGui.QLabel()
        self.waitingLabel = QtGui.QLabel()
        self.runningLabel = QtGui.QLabel()
        self.stateLabel = QtGui.QLabel()

        layout.addRow("Job #:", self.jobLabel)
        layout.addRow("Submitted:", self.submitLabel)
        layout.addRow("Started:", self.startLabel)
        layout.addRow("Finished:", self.finishLabel)
        layout.addRow("Waiting:", self.runningLabel)
        layout.addRow("Running:", self.waitingLabel)
        layout.addRow("State:", self.stateLabel)

        self.singleSimulationsPanel.setLayout(self.createButtonedLayout(layout))


    def createNoSelectionsPanel(self):
        self.noSimulationsPanel = QtGui.QWidget()

        layout = QtGui.QVBoxLayout()
        label = QtGui.QLabel("Pause queue after currently running jobs are finished.")
        label.setWordWrap(True)
        #label.setAlignment(QtCore.Qt.AlignHCenter)
        layout.addWidget(label)

        self.pauseButton = QtGui.QToolButton(self)
        #self.pauseButton.setIcon(resourceStateIcon("pause", "start"))
        self.pauseButton.setIcon(resourceIcon("pause"))
        self.pauseButton.setCheckable(True)
        self.connect(self.pauseButton, QtCore.SIGNAL('clicked()'), lambda : self.ctrl.pause(self.pauseButton.isChecked()))

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.pauseButton)
        buttonLayout.addStretch(1)

        layout.addLayout(buttonLayout)

        self.noSimulationsPanel.setLayout(layout)



    def setSimulations(self, selection=[]):
        self.ctrl.setSimulations(selection)

#    def markText(self, a, b):
#        if b.isRunning():
#            c = SimulationItemDelegate.running
#        elif b.isWaiting():
#            c = SimulationItemDelegate.waiting
#        else:
#            c = QtGui.QColor(255, 255, 255, 0)
#
#        color = "rgb(%d, %d, %d)" % (c.red(), c.green(), c.blue())
#
#        b = "<span style='background: " + color + ";'>" + str(b) + "</span>"
#
#        if not a == "":
#            return a + " " + b
#        else:
#            return b

    def setModel(self, ert):
        self.ctrl.setModel(ert)


class SimulationPanelController:
    def __init__(self, view):
        self.view = view
        self.initialized = False
        self.selectedSimulations = []
        self.view.connect(self.view, QtCore.SIGNAL('simulationsUpdated()'), self.showSelectedSimulations)

    def initialize(self, ert):
        if not self.initialized:
            ert.setTypes("job_queue_get_pause", library = ert.job_queue)
            ert.setTypes("job_queue_set_pause_on", library = ert.job_queue)
            ert.setTypes("job_queue_set_pause_off", library = ert.job_queue)
            ert.setTypes("enkf_main_iget_state", argtypes=ertwrapper.c_int)
            ert.setTypes("enkf_state_kill_simulation", None)
            ert.setTypes("enkf_state_resubmit_simulation", None, ertwrapper.c_int)
            ert.setTypes("enkf_state_get_run_status", ertwrapper.c_int)
            ert.setTypes("site_config_get_job_queue")
            self.initialized = True

    def setModel(self, ert):
        self.initialize(ert)
        self.ert = ert

    def kill(self):
        """Kills the selected simulations."""
        for simulation in self.selectedSimulations:
            state = self.ert.enkf.enkf_main_iget_state(self.ert.main, simulation.name)
            status = self.ert.enkf.enkf_state_get_run_status(state)

            if status == Simulation.RUNNING:
                self.ert.enkf.enkf_state_kill_simulation(state)

    def restart(self, resample):
        """Restarts the selected simulations. May also resample."""
        for simulation in self.selectedSimulations:
            state = self.ert.enkf.enkf_main_iget_state(self.ert.main, simulation.name)
            status = self.ert.enkf.enkf_state_get_run_status(state)

            if status == Simulation.USER_KILLED:
                self.ert.enkf.enkf_state_resubmit_simulation(state, resample)

    def pause(self, pause):
        job_queue = self.ert.enkf.site_config_get_job_queue(self.ert.site_config)

        if pause:
            self.ert.job_queue.job_queue_set_pause_on(job_queue)
        else:
            self.ert.job_queue.job_queue_set_pause_off(job_queue)


    def showSelectedSimulations(self):
        if len(self.selectedSimulations) >= 2:
            members = reduce(lambda a, b: str(a) + " " + str(b), sorted(self.selectedSimulations))
            self.view.selectedSimulationsLabel.setText(members)
        elif len(self.selectedSimulations) == 1:
            sim = self.selectedSimulations[0]
            self.view.jobLabel.setText(str(sim.name))
            self.view.submitLabel.setText(shortTime(sim.submitTime))
            self.view.startLabel.setText(shortTime(sim.startTime))
            self.view.finishLabel.setText(shortTime(sim.finishedTime))

            if sim.startTime == -1:
                runningTime = "-"
            elif sim.finishedTime > -1:
                runningTime = sim.finishedTime - sim.startTime
            else:
                runningTime = int(time.time()) - sim.startTime


            if sim.submitTime == -1:
                waitingTime = "-"
            elif sim.startTime > -1:
                waitingTime = sim.startTime - sim.submitTime
            else:
                waitingTime = int(time.time()) - sim.submitTime

            self.view.runningLabel.setText(str(waitingTime) + " secs")
            self.view.waitingLabel.setText(str(runningTime) + " secs")

            status = Simulation.job_status_type[sim.status]
            status = status[10:]
            self.view.stateLabel.setText(status)


    def setSimulations(self, selection=[]):
        self.selectedSimulations = selection

        if len(selection) >= 2:
            self.view.setCurrentWidget(self.view.manySimulationsPanel)
        elif len(selection) == 1:
            self.view.setCurrentWidget(self.view.singleSimulationsPanel)
        else:
            self.view.setCurrentWidget(self.view.noSimulationsPanel)

        self.showSelectedSimulations()


class Simulation:
    job_status_type_reverse = {"JOB_QUEUE_NOT_ACTIVE" : 0,
                               "JOB_QUEUE_LOADING" : 1,
                               "JOB_QUEUE_NULL" : 2,
                               "JOB_QUEUE_WAITING" : 3,
                               "JOB_QUEUE_PENDING" : 4,
                               "JOB_QUEUE_RUNNING" : 5,
                               "JOB_QUEUE_DONE" : 6,
                               "JOB_QUEUE_EXIT" : 7,
                               "JOB_QUEUE_RUN_OK" : 8,
                               "JOB_QUEUE_RUN_FAIL" : 9,
                               "JOB_QUEUE_ALL_OK" : 10,
                               "JOB_QUEUE_ALL_FAIL" : 11,
                               "JOB_QUEUE_USER_KILLED" : 12,
                               "JOB_QUEUE_MAX_STATE" : 13}

    job_status_type = {0 : "JOB_QUEUE_NOT_ACTIVE",
                       1 : "JOB_QUEUE_LOADING",
                       2 : "JOB_QUEUE_NULL",
                       3 : "JOB_QUEUE_WAITING",
                       4 : "JOB_QUEUE_PENDING",
                       5 : "JOB_QUEUE_RUNNING",
                       6 : "JOB_QUEUE_DONE",
                       7 : "JOB_QUEUE_EXIT",
                       8 : "JOB_QUEUE_RUN_OK",
                       9 : "JOB_QUEUE_RUN_FAIL",
                       10 : "JOB_QUEUE_ALL_OK",
                       11 : "JOB_QUEUE_ALL_FAIL",
                       12 : "JOB_QUEUE_USER_KILLED",
                       13 : "JOB_QUEUE_MAX_STATE"}
    
    
    NOT_ACTIVE = 0
    LOADING = 1
    NULL = 2
    WAITING = 3
    PENDING = 4
    RUNNING = 5
    DONE = 6
    EXIT = 7
    RUN_OK = 8
    RUN_FAIL = 9
    ALL_OK = 10
    ALL_FAIL = 11
    USER_KILLED = 12
    MAX_STATE = 13
    

    def __init__(self, name, statistics=None):
        self.name = name
        self.status = Simulation.NOT_ACTIVE
        self.statuslog = []
        self.statistics = statistics

        self.resetTime()

    def checkStatus(self, type):
        return self.status == type

    def isWaiting(self):
        return self.checkStatus(Simulation.WAITING) or self.checkStatus(Simulation.PENDING)

    def isRunning(self):
        return self.checkStatus(Simulation.RUNNING)

    def hasFailed(self):
        return self.checkStatus(Simulation.ALL_FAIL)

    def notActive(self):
        return self.checkStatus(Simulation.NOT_ACTIVE)

    def finishedSuccesfully(self):
        return self.checkStatus(Simulation.ALL_OK)

    def isUserKilled(self):
        return self.checkStatus(Simulation.USER_KILLED)


    def setStatus(self, status):
        if len(self.statuslog) == 0 or not self.statuslog[len(self.statuslog) - 1] == status:
            self.statuslog.append(status)

            if status == Simulation.ALL_OK:
                self.setFinishedTime(int(time.time()))

        self.status = status

    def setStartTime(self, secs):
        self.startTime = secs

    def setSubmitTime(self, secs):
        self.submitTime = secs
        if self.submitTime > self.finishedTime:
            self.finishedTime = -1

    def setFinishedTime(self, secs):
        self.finishedTime = secs
        
        if not self.statistics is None:
            self.statistics.addTime(self.submitTime, self.startTime, self.finishedTime)

    def printTime(self, secs):
        if not secs == -1:
            print time.localtime(secs)

    def resetTime(self):
       self.startTime = -1
       self.submitTime = -1
       self.finishedTime = -1

    def __str__(self):
        return str(self.name)

    def __ge__(self, other):
        return self.name >= other.name

    def __lt__(self, other):
        return not self >= other


class SimulationStatistics:


    def __init__(self, name="default"):
        self.name = name

        self.clear()

    def clear(self):
        self.jobs = 0
        self.waiting = 0
        self.running = 0
        self.total = 0
        self.start = 0
        self.last = 0

    def startTiming(self):
        self.start = int(time.time())

    def jobsPerSecond(self):
        #t = self.last - self.start
        t = int(time.time()) - self.start
        if t > 0:
            return self.jobs / t
        else:
            return 0

    def secondsPerJob(self):
        return 1.0 / self.jobsPerSecond()

    def estimate(self, jobs):
        if self.jobsPerSecond() > 0:
            spj = self.secondsPerJob()
            jobs_estimate = spj * (jobs - self.jobs)

            timeUsed = int(time.time()) - self.last
            return jobs_estimate - timeUsed
        else:
            return -1


    def addTime(self, submit, start, finish):
        self.jobs += 1
        self.waiting += start - submit
        self.running += finish - start
        self.total += finish - submit
        self.last = int(time.time())
