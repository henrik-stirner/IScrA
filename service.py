import ctypes, sys

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket

from time import sleep

from mail import ScheduleManager
import auth


# ----------
# service
# ----------


class MailScheduler (win32serviceutil.ServiceFramework):
    _svc_name_ = "IScrAMailScheduler"
    _svc_display_name_ = "IScrA Mail Scheduler"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

        self.mail_schedule_manager = ScheduleManager(*auth.authenticate())

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

        self.mail_schedule_manager.shutdown()

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        while True:
            sleep(10)
            self.mail_schedule_manager.send_and_reschedule_scheduled_mails()


# ----------
# run
# ----------


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    win32serviceutil.HandleCommandLine(MailScheduler)


if __name__ == '__main__':
    if is_admin():
        main()
    else:
        # restart with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
