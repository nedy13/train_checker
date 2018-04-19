import datetime
import schiene
import smtplib
from tabulate import tabulate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

### GENERAL ########
CHECKTIME = 120  # two hours before departure (in minutes)

### TRAIN ROUTE ####
HOMESTATION = "Karstädt"
WORKSTATION = "Berlin Zoologischer Garten"
DEPARTURE_TIME_FROM_WORK = "17:31"
DEPARTURE_TIME_FROM_HOME = "06:50"

### MAIL ###########
MAIL_SEND_ON = True
MAIL_SMTPSERVER = "smtp.strato.de:587"
MAIL_LOGIN = "account@domain.eu"
MAIL_PASSWORD = "MySecret"
MAIL_FROM = "account@domain.eu"
MAIL_TO = "mail@nedy.eu"
MAIL_SUBJECT = "DB MONITOR: Verspätung / Ausfall"

MAIL_TEXT = """
ACHTUNG: BAHNVERSPÄTUNG

Genauen Daten:

{table}

MfG
Me"""

MAIL_HTML = """
<html><body><p>ACHTUNG: BAHNVERSPÄTUNG</p>
<p>Genauen Daten:</p>
{table}
<p>MfG</p>
<p>Me</p>
</body></html>
"""
class Connection:

    def __init__(self, name, from_station, to_station, departure_time):
        self.name = name
        self.from_station = from_station
        self.to_station = to_station
        self._departure_time = None
        self.departure_time = departure_time
        self._trains_data = None
        self.trains_data = None

    @property
    def departure_time(self):
        return self._departure_time

    @departure_time.setter
    def departure_time(self, deptime_str):
        departure_date_today = datetime.date.today()
        departure_time_time = datetime.datetime.strptime(deptime_str, "%H:%M").time()
        departure_datetime = datetime.datetime.combine(departure_date_today, departure_time_time)
        self._departure_time = departure_datetime

    @property
    def trains_data(self):
        if self._trains_data is None:
            self._trains_data = self._get_connection_data()
            return self._trains_data
        else:
            return self._trains_data

    @trains_data.setter
    def trains_data(self, data):
        self._trains_data = data

    def in_checktime(self):
        now = datetime.datetime.now()
        delta = datetime.timedelta(minutes=CHECKTIME)
        delta_after = datetime.timedelta(minutes=20)
        checktime_begin = self.departure_time - delta
        checktime_end = self.departure_time + delta_after

        print(self.name + ":Checktime Begin: " + str(checktime_begin))
        print(self.name + ":Checktime End: " + str(checktime_end))
        if checktime_begin < now < checktime_end:
            return True
        else:
            return False

    def trains_ontime(self):

        def is_ontime(train_data):
            if train_data["ontime"] is False or train_data["canceled"]:
                return False
            else:
                return True

        if self.trains_data:
            return all(map(is_ontime, self.trains_data))
        else:
            return False

    def get_email_msg(self):
        data = self._format_for_tabulate(self.trains_data)
        print(tabulate(data, headers="firstrow", tablefmt="grid"))
        mailtext = MAIL_TEXT.format(table=tabulate(data, headers="firstrow", tablefmt="grid"))
        mailhtml = MAIL_HTML.format(table=tabulate(data, headers="firstrow", tablefmt="html"))
        message = MIMEMultipart("alternative", None, [MIMEText(mailtext), MIMEText(mailhtml, "html")])
        return message

    def _format_for_tabulate(self, data):
        headers = [list(data[0].keys())]
        values = [list(item.values()) for item in data]
        result = headers + values
        return result

    def _get_connection_data(self):
        db = schiene.Schiene()
        connections = db.connections(self.from_station, self.to_station, self.departure_time)
        return connections


def sendemail(from_addr, to_addr_list, subject, message, login, password, smtpserver='smtp.gmail.com:587'):

    message['Subject'] = subject
    message['From'] = from_addr
    message['To'] = to_addr_list

    server = smtplib.SMTP(smtpserver)
    server.ehlo_or_helo_if_needed()
    server.starttls()
    server.login(login, password)
    problems = server.sendmail(from_addr, to_addr_list, message.as_string())
    print(problems)
    server.quit()


def main():

    from_home = Connection("HOME", HOMESTATION, WORKSTATION, DEPARTURE_TIME_FROM_HOME)
    from_work = Connection("WORK", WORKSTATION, HOMESTATION, DEPARTURE_TIME_FROM_WORK)

    connections = [from_home, from_work]

    for conn in connections:
        if conn.in_checktime():
            if not conn.trains_ontime():
                msg = conn.get_email_msg()
                if MAIL_SEND_ON:
                    print("sending email")
                    sendemail(MAIL_FROM, MAIL_TO, MAIL_SUBJECT, msg, MAIL_LOGIN, MAIL_PASSWORD, MAIL_SMTPSERVER)
            else:
                print(conn.name + ": all trains on time")
        else:
            print(conn.name + " not in checktime")


if __name__ == '__main__':
    main()











