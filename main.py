from logic import *

def main():
    app = QtWidgets.QApplication([])
    window = Logic()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()