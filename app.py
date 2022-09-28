# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Open selection in Shotgun
"""

from pprint import pformat
import hiero.core

from tank.platform import Application
from tank import TankError
from tank.platform.qt import QtGui, QtCore


class HieroOpenInShotgun(Application):
    """
    This app adds a menu item that allows a user to jump from an object
    in Hiero to the associated object in Shotgun.
    """

    def init_app(self):
        """
        Initialization
        """
        self.engine.register_command("Open in Shotgun", self.callback)

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True

    def callback(self):
        """
        Command implementation
        """
        try:
            self._open_shot()
        except TankError as e:
            # report all tank errors with a UI popup.
            QtGui.QMessageBox.critical(None, "Shot Lookup Error!", str(e))
        except Exception as e:
            # log full call stack to console
            self.log_exception("General error reported.")
            # pop up message
            msg = "A general error was reported: %s" % e
            QtGui.QMessageBox.critical(None, "Shot Lookup Error!", msg)

    def _open_shot(self):
        """
        Look up shot in shotgun from selection
        """

        # THIS SEEMS TO NO LONGER WORK
        # grab the current selection from the view that triggered the event.
        # selection = self.engine.get_menu_selection()

        # get the active sequence, editor and selection
        activeSeq = hiero.ui.activeSequence()
        activeEditor = hiero.ui.getTimelineEditor(activeSeq)
        selection = activeEditor.selection()
        self.logger.debug("Selection: {}".format(pformat(selection)))

        # Exclude transisions from the list of selected items if this version of
        # hiero supports effects
        if hasattr(hiero.core, "Transition"):
            self.logger.debug("Excluding items of type: hiero.core.Transition")
            selection = [
                s for s in selection if not isinstance(s, hiero.core.Transition)
            ]
        self.logger.debug("Selection: {}".format(pformat(selection)))

        # Exclude effects from the list of selected items if this version of
        # hiero supports effects
        if hasattr(hiero.core, "EffectTrackItem"):
            self.logger.debug("Excluding items of type: hiero.core.EffectTrackItem")
            selection = [
                s for s in selection if not isinstance(s, hiero.core.EffectTrackItem)
            ]
        self.logger.debug("Selection: {}".format(pformat(selection)))

        # Exclude non TrackItems from the list of selected items
        self.logger.debug("Excluding items NOT of type: hiero.core.TrackItem...")
        selection = [
            s for s in selection if isinstance(s, hiero.core.TrackItem)
        ]
        self.logger.debug("Selection: {}".format(pformat(selection)))

        if len(selection) == 0:
            raise TankError("Please select a Shot in the Timeline or Spreadsheet!")

        # deal with each selected hiero.core.TrackItem
        for item in selection:
            # this is always okay according to the hiero API docs
            sequence = item.parent().parent()

            shot_name = item.name()
            sequence_name = sequence.name()

            self.log_debug(
                "Looking for a shot '%s' in ShotGrid..."
                % (shot_name)
            )

            filters = [
                ["project", "is", self.context.project],
                ["code", "is", shot_name]
            ]

            sg_data = self.shotgun.find_one("Shot", filters)

            if sg_data is None:
                raise TankError(
                    "Could not find a Shot in ShotGrid with name '%s'!"
                    % (shot_name)
                )

            # launch Shotgun Url using default browser
            url = "%s/detail/Shot/%s" % (self.shotgun.base_url, sg_data["id"])
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
