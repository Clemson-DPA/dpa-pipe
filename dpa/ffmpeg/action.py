# ----------------------------------------------------------------------------

import argparse
import os
import platform
import shlex
from subprocess import Popen

from dpa.action import Action, ActionError
from dpa.config import Config
from dpa.env import EnvVar
from dpa.ptask import PTaskArea

# ----------------------------------------------------------------------------

FFMPEG_ACTION_CONFIG = "config/actions/ffmpeg.cfg"

# ----------------------------------------------------------------------------
class FfmpegAction(Action):

    name = 'ffmpeg'
    target_type = 'file'
    description = 'Create a movie from a sequence of images.'
    
    # ------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(self, parser):

        # the file or software
        parser.add_argument(
            "basename",
            help="Base name of the sequence",
        )
        
        parser.add_argument(
            "-g", "--gamma",
            default=1.0,
            help="Gamma to apply to sequence.",
            metavar="type"
        )

    # ------------------------------------------------------------------------
    def __init__(self, basename, gamma):
        super(FfmpegAction, self).__init__(basename, gamma)

        self._basename = basename
        self._gamma = gamma

    # ------------------------------------------------------------------------
    def execute(self):
        print "making movie"
        sys_command = "ffmpeg -v 0 -y -r 24 -i %s.%%04d.exr -vf eq=gamma=%s -vcodec mjpeg -b:v 50M -r 24 %s.mov" % (self._basename, self._gamma, self._basename)
        os.system(sys_command)

    # ------------------------------------------------------------------------
    def undo(self):
        pass

    # ------------------------------------------------------------------------
    @property
    def basename(self):
        return self._basename

    # ------------------------------------------------------------------------
    @property
    def gamma(self):
        return self._gamma

