#!/usr/bin/env python

import pygtk
import gtk

from aboutdialog import AboutDialog
from config import DtGrepConfig
from mainwindow import MainWindow

pygtk.require("2.0")

def main():
    config = DtGrepConfig()
    MainWindow(config)
    gtk.main()

if __name__ == "__main__":
    main()

