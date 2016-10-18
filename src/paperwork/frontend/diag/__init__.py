import logging
import os

import gettext
from gi.repository import GLib
from gi.repository import Gtk

from paperwork.frontend.util import load_uifile


_ = gettext.gettext


class LogTracker(logging.Handler):
    def __init__(self):
        super(LogTracker, self).__init__()
        self._formatter = logging.Formatter(
            '%(levelname)-6s %(name)-30s %(message)s'
        )
        self.output = []

    def emit(self, record):
        line = self._formatter.format(record)
        self.output.append(line)

    def get_logs(self):
        return "\n".join(self.output)

    @staticmethod
    def init():
        logger = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(g_log_tracker._formatter)
        logger.addHandler(handler)
        logger.addHandler(g_log_tracker)
        logger.setLevel({
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }[os.getenv("PAPERWORK_VERBOSE", "INFO")])


g_log_tracker = LogTracker()


class DiagDialog(object):
    def __init__(self, main_win):
        widget_tree = load_uifile(
            os.path.join("diag", "diagdialog.glade"))

        self.buf = widget_tree.get_object("textbufferDiag")

        self.dialog = widget_tree.get_object("dialogDiag")
        self.dialog.set_transient_for(main_win.window)
        self.dialog.connect("response", self._on_response)

        self.scrollwin = widget_tree.get_object("scrolledwindowDiag")

        self._main_win = main_win

        self.set_text(g_log_tracker.get_logs())

        txt_view = widget_tree.get_object("textviewDiag")
        txt_view.connect("size-allocate", self.scroll_to_bottom)

    def set_text(self, txt):
        self.buf.set_text(txt, -1)
        GLib.idle_add(self.scroll_to_bottom)

    def scroll_to_bottom(self, *args, **kwargs):
        vadj = self.scrollwin.get_vadjustment()
        vadj.set_value(vadj.get_upper())

    def _on_response(self, widget, response):
        if response == 0:  # close
            self.dialog.set_visible(False)
            self.dialog.destroy()
            self.dialog = None
            return True
        if response == 1:  # save as
            chooser = Gtk.FileChooserDialog(
                title=_("Save as"),
                transient_for=self._main_win.window,
                action=Gtk.FileChooserAction.SAVE
            )
            file_filter = Gtk.FileFilter()
            file_filter.set_name("text")
            file_filter.add_mime_type("text/plain")
            chooser.add_filter(file_filter)
            chooser.add_buttons(Gtk.STOCK_CANCEL,
                                Gtk.ResponseType.CANCEL,
                                Gtk.STOCK_SAVE,
                                Gtk.ResponseType.OK)
            response = chooser.run()
            try:
                if response != Gtk.ResponseType.OK:
                    return True

                filepath = chooser.get_filename()
                with open(filepath, "w") as fd:
                    start = self.buf.get_iter_at_offset(0)
                    end = self.buf.get_iter_at_offset(-1)
                    text = self.buf.get_text(start, end, False)
                    fd.write(text)
            finally:
                chooser.set_visible(False)
                chooser.destroy()

            return True
        if response == 2:  # copy
            gdk_win = self._main_win.window.get_window()
            clipboard = Gtk.Clipboard.get_default(gdk_win.get_display())
            start = self.buf.get_iter_at_offset(0)
            end = self.buf.get_iter_at_offset(-1)
            text = self.buf.get_text(start, end, False)
            clipboard.set_text(text, -1)
            return True

    def show(self):
        self.dialog.set_visible(True)