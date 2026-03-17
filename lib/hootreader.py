#!/usr/bin/python3

import subprocess
import os
import os.path
import tempfile
import sys

from lib.wpilogreader import WpilogReader


class HootReader:
    def __init__(self, filename: str):
        self.wpireader = None

        # owlet only outputs to a file
        # can't get a pipe to work >;-(
        # don't use a changing temp name. Otherwise the files might accumulate
        self.tmp_name = os.path.join(tempfile.gettempdir(), "hootreader_temp.wpilog")
        self.proc = subprocess.Popen(["owlet", "-f", "wpilog", filename, self.tmp_name], stdout=sys.stderr)

        # Wait for the owlet process to finish producing the output
        try:
            self.proc.wait(timeout=15)
        except Exception:
            try:
                self.proc.kill()
                self.proc.wait()
            except Exception:
                pass

        # Start the WpilogReader after owlet has finished writing
        self.wpireader = WpilogReader(self.tmp_name)
        return
    
    def close(self) -> None:
        if self.wpireader is not None:
            self.wpireader.close()
        if os.path.exists(self.tmp_name):
            os.unlink(self.tmp_name)
        return
    
    def __iter__(self):
        for rec in self.wpireader:
            yield rec
        return