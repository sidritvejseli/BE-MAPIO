from interface import Interface
from logger import construire_logger


if __name__ == "__main__":
    construire_logger()

    app = Interface()
    app.mainloop()
