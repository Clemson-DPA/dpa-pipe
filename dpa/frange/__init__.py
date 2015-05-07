# -----------------------------------------------------------------------------
# Module: dpa.frange
# Author: Chuqiao Wang (chuqiaw)
# -----------------------------------------------------------------------------
"""A frame ranger parser

A frame ranger parser that parses, adds and removes frame ranges  

Classes
-------
Frange
    A class that represents a frame range
FrangeError
    Syntax error when parsing a frame range

Examples
--------
    >>> # create an instance of Frange
    >>> from dpa.frange import Frange
    >>> f = Frange("-2-8:2")
    >>> print f
    [-2-8:2]

    >>> # add a frame range
    >>> f.add("3, 5")  
    >>> print f
    [-2-2:2, 3-6, 8]

    >>> # remove a frame range
    >>> f.remove("4-8")       
    >>> print f5
    [-2-2:2, 3]

"""

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import re
import sys

# -----------------------------------------------------------------------------
# Public Classes: (if there are any) 
# -----------------------------------------------------------------------------
class Frange(object):
    """A frame range parser that identifies and parses frame ranges

    A frange range parser that
        * identify a frame range syntax. (f.e. start-end:step)
        * support negative frames
        * parse a list of integers to a frame range syntax.ex. 2,4,6,8 >> 2-8:2
        * parse a frame range syntax into list of integers 3-12:3 >> 3,6,9,12
        * support tuples of frame ranges and collapsing them into condensed 
          ranges 
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------
    _pattern = re.compile("^(\-?[0-9]+)\-?(\-?[0-9]+)?:?(\-?[0-9]+)?$")

    """ _pattern : the regular expression for each valid syntax """

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, input_range=None):
        """Constructor. 

        :arg str inputRange: The frame range to initialize the object with

        """
        super(Frange, self).__init__()
        self._frames = list()
        if (input_range is not None):
            self.add(input_range)

    def __str__(self):
        """ print the frame range out in its most compact form """
        _ordered_frames = sorted(self._frames)
        compact_frames = []
        i = 0

        if (len(_ordered_frames) < 3):
            return ",".join(str(f) for f in _ordered_frames)
        else:
            i = 0
            while (i < len(_ordered_frames) - 1):
                step = _ordered_frames[i+1] - _ordered_frames[i]
                length = 1
                while (i < len(_ordered_frames) - 1 and (_ordered_frames[i+1] - _ordered_frames[i] == step) ):
                    i += 1
                    length += 1
                if (length > 2):
                    start = str(_ordered_frames[i - length + 1])
                    end = str(_ordered_frames[i])
                    if (step == 1):
                        compact_frames.append(start + "-" + end)
                    else:
                        compact_frames.append(start + "-" + end + ":" + str(step))
                    i += 1
                    if (i == len(_ordered_frames) - 1):
                        compact_frames.append(_ordered_frames[i])
                else:
                    compact_frames.append(_ordered_frames[i-1])
                    if (i == len(_ordered_frames) - 1):
                        compact_frames.append(_ordered_frames[i])

            return ",".join(str(f) for f in compact_frames)

    # -------------------------------------------------------------------------
    # Instance methods:
    # -------------------------------------------------------------------------
    def add(self, frames):
        """ Add specified frames to the range

        :arg str frames: The frame range to add

        """
        
        matched = False
        if isinstance(frames, basestring):            
            parts = frames.split(',')
            for i in range(len(parts)):
                #print "".join(parts[i].split())
                self._add_single_range(parts[i].strip())
        else:
            for i in range(len(frames)):
                part = str(frames[i])
                self._add_single_range(part.strip())
                    
    def remove(self, frames):
        """ Remove specified frames from the range
        
        :arg str frames: The frame range to remove

        """
        matched = False
        if isinstance(frames, basestring):
            parts = frames.split(',')
            for i in range(len(parts)):
                self._remove_single_range(parts[i].strip())

        else:
            for i in range(len(frames)):
                part = str(frames[i])
                self._remove_single_range(part.strip())

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def start(self):
        """first frame in the sorted range"""
        _ordered_frames = sorted(self._frames)
        
        if (len(_ordered_frames) == 0):
            return None
        return _ordered_frames[0]

    @property
    def end(self):
        """last frame in the sorted range"""
        _ordered_frames = sorted(self._frames)
        
        if (len(_ordered_frames) == 0):
            return None 
        return _ordered_frames[len(_ordered_frames)-1]

    @property
    def first(self):
        """first frame in the range"""
        if (len(self._frames) == 0):
            return None
        return self._frames[0]

    @property
    def last(self):
        """last frame in the range"""
        if (len(self._frames) == 0):
            return None 
        return self._frames[len(self._frames)-1]

    @property
    def step(self):
        """the frame step if there is a consistent one, None otherwise"""
        _ordered_frames = sorted(self._frames)
        
        if (len(_ordered_frames) == 0):
            return None

        if (len(_ordered_frames) == 1):
            return 1

        if (len(_ordered_frames) > 1):
            step = _ordered_frames[1] - _ordered_frames[0]
            
            if (len(_ordered_frames) == 2):
                return step
            else:
                for i in range(2, len(_ordered_frames)):
                    if (not int(_ordered_frames[i] - _ordered_frames[i-1]) == step):
                        return None
                return step
    
    @property
    def frames(self):
        """a generator for each frame in the range in order"""
        return self._frames

    @property
    def count(self):
        """the total number of frames"""
        return len(self._frames)
    
    @property
    def sorted(self):
        """the frames in order"""
        _ordered_frames = str(sorted(self._frames)).strip('[]')
        return Frange(_ordered_frames)

    # -------------------------------------------------------------------------
    # Private methods:
    # -------------------------------------------------------------------------
    def _parse_single_range(self, single_range):
        """Parse a single frame range.

        Parse a single frame range within an input frame range.
        Examples:
            1-10
            2
            1-20:2

        If valid, return the parsed range; raises FrangeError exception otherwise.

        """
        match = self._pattern.match(single_range)

        if match:
            return match.groups()    
        else:
            raise FrangeError(" invalid syntax for frame range")
     
    def _add_single_range(self, single_range):
        """ Add a single frame range. 

            Call _parsesingle_range to parse the frame range and add valid 
            frame range.
        """
        groups = self._parse_single_range(single_range)
        length = len(groups)
                
        if groups[1] == None:
            frames = [int(groups[0])]
            
        elif groups[2] == None:
            frames = xrange(int(groups[0]), int(groups[1])+1)

        else:
            start = int(groups[0])
            end = int(groups[1])
            step = int(groups[2])
            frames = xrange(start, end+1, step)

        _f = [f for f in frames if f not in self._frames]
        self._frames.extend(_f)

    def _remove_single_range(self, single_range):
        """ Remove a single frame range.

            Call _parsesingle_range to parse the frame range and remove valid 
            frame range.
        """
        groups = self._parse_single_range(single_range)
        length = len(groups)
                
        if groups[1] == None:
            frames = [int(groups[0])]
            
        elif groups[2] == None:
            frames = xrange(int(groups[0]), int(groups[1])+1)

        else:
            start = int(groups[0])
            end = int(groups[1])
            step = int(groups[2])
            frames = xrange(start, end+1, step)

        self._frames = [f for f in self.frames if f not in frames]

# -----------------------------------------------------------------------------
# Exceptions:
# -----------------------------------------------------------------------------
class FrangeError(Exception):
    """Invalid frame range syntax

    """
    pass
