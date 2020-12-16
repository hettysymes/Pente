from Ui import Gui, Terminal
from sys import argv
import Database

# If no recognised command is input to the terminal, the usage function displays a usage message.
def usage():
    print(f"""
Usage: {argv[0]} [g | t]
g: play with GUI
t: play with Terminal""")
    quit()

# If the program is run, depending on the command, the program will run one of the graphical UI or the terminal UI.
# A new database is also created if not database is detected to exist, which is done by calling the database's exists function.
if __name__ == "__main__":
    if len(argv) != 2:
        usage()
    elif argv[1] == "g":
        ui = Gui()
    elif argv[1] == "t":
        ui = Terminal()
    else:
        usage()
    if not Database.exists():
        Database.createDatabase()
    ui.run()