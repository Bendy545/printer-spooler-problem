from devices.printer import Printer
from spooler.task_list import TaskList
from users.user import User

def main():
    spooler_1 = TaskList()

    printer = Printer(spooler_1,"Laser Jet")
    printer.start()

    users = [User(f"user{i}", spooler_1, i) for i in range(1,6)]


    for user in users:
        user.start()

    for user in users:
        user.join()

    printer.stop()
    printer.join()


if __name__ == '__main__':
    main()