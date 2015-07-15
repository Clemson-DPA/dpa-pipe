# -----------------------------------------------------------------------------
# Module: dpa.output
# Author: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------
"""Consistent shell output."""

# TODO:
# * sorting
# * cell alignment
# * header alignment
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

# built-in 
from collections import defaultdict, namedtuple
import os
import re

# 3rd party
import colorama
from colorama import Fore, Back, Style

from dpa.cli import date_time_from_str

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class Bg(object):
    """Background colors.

    This class defines the background colors available for any color attributes
    on :py:obj:`Output` instances.

    """

    #: ``Bg.red`` - set the bg color to red.
    red = Back.RED

    #: ``Bg.green`` - set the bg color to green.
    green = Back.GREEN

    #: ``Bg.blue`` - set the bg color to blue.
    blue = Back.BLUE

    #: ``Bg.yellow`` - set the bg color to yellow.
    yellow = Back.YELLOW

    #: ``Bg.magenta`` - set the bg color to magenta.
    magenta = Back.MAGENTA

    #: ``Bg.black`` - set the bg color to black.
    black = Back.BLACK

    #: ``Bg.white`` - set the bg color to white.
    white = Back.WHITE

    #: ``Bg.cyan`` - set the bg color to cyan.
    cyan = Back.CYAN

    #: ``Bg.reset`` - resets the background color to the default value.
    reset = Back.RESET

    _all = [
        red,
        green,
        blue,
        yellow,
        magenta,
        black,
        white,
        cyan,
        reset,
    ]

# -----------------------------------------------------------------------------
class Fg(object):
    """Background colors.

    This class defines the foreground colors available for any color attributes
    on :py:obj:`Output` instances.

    """

    #: ``Fg.red`` - set the fg color to red.
    red = Fore.RED

    #: ``Fg.green`` - set the fg color to green.
    green = Fore.GREEN

    #: ``Fg.blue`` - set the fg color to blue.
    blue = Fore.BLUE

    #: ``Fg.yellow`` - set the fg color to yellow.
    yellow = Fore.YELLOW

    #: ``Fg.magenta`` - set the fg color to magenta.
    magenta = Fore.MAGENTA

    #: ``Fg.black`` - set the fg color to black.
    black = Fore.BLACK

    #: ``Fg.white`` - set the fg color to white.
    white = Fore.WHITE

    #: ``Fg.cyan`` - set the fg color to cyan.
    cyan = Fore.CYAN

    #: ``Fg.reset`` - resets the foreground color to the default value.
    reset = Fore.RESET

    _all = [
        red,
        green,
        blue,
        yellow,
        magenta,
        black,
        white,
        cyan,
        reset,
    ]

# -----------------------------------------------------------------------------
class Style(object):
    """Text style.

    This class defines the text style available for any color attributes
    on :py:obj:`Output` instances.

    """

    #: ``Style.dim`` - display the text with a dimmer fg color.
    dim = Style.DIM

    #: ``Style.normal`` - normal display of the text.
    normal = Style.NORMAL

    #: ``Style.bright`` - display the text with a brighter fg color.
    bright = Style.BRIGHT

    #: ``Style.reset`` - reset the text style to the default value.
    reset = Style.RESET_ALL

    _all = [
        dim,
        normal,
        bright,
        reset,
    ]

# helper for length determination, for efficiency
_special_chars = Bg._all + Fg._all + Style._all

# -----------------------------------------------------------------------------
class Output(object):
    """


    """

    _DEFAULT_COLOR = Style.reset + Bg.reset + Fg.reset

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def text(cls, text, margin=0):

        paragraphs = text.split("\n")
        for paragraph in paragraphs:
            cls.paragraph(paragraph, margin=margin)

    @classmethod
    def paragraph(cls, text, margin=0):

        (term_width, term_height) = _get_terminal_size()
        term_width -= 2 * margin
        words = text.split(" ")
        cur_len = 0
        out_text = []

        for word in words:
            
            word_len = _len(word) 
            while word_len > term_width:
                partial = word[0:term_width - 1]
                word = word[term_width:]
                out_text.append(partial + "-")
                out_text.append("\n" + " " * margin)
                word_len = _len(word)

            if (word_len + cur_len) > term_width:
                out_text.append("\n" + " " * margin)
                cur_len = 0

            out_text.append(word)
            cur_len += word_len + 1

        print " " * margin,
        print " ".join(out_text)

    # -------------------------------------------------------------------------
    @classmethod
    def prompt(cls, prompt_str, help_str=None, blank=True, formatter=None,
        separator=":"):

        while True:
            
            response = raw_input(prompt_str + separator + " ")

            # no response, either return none or continue depending on whether
            # blank values are allowed.
            if not response:
                if blank:
                    return None
                else:
                    print "  Response can not be empty."
                    continue

            # try to format the response
            if formatter:
                try:
                    response = formatter(response)
                except Exception as e:
                    print "   " + str(e)
                    print "   " + help_str
                    continue
                else:
                    return response

            return response

    # -------------------------------------------------------------------------
    @classmethod
    def prompt_date(cls, prompt_str, 
        help_str="Please enter a valid date string.", blank=True):

        return cls.prompt_datetime(prompt_str, help_str=help_str, blank=blank).\
            date()

    # -------------------------------------------------------------------------
    @classmethod
    def prompt_datetime(cls, prompt_str, 
        help_str="Please enter a valid datetime string.", blank=True):

        return cls.prompt(prompt_str, help_str=help_str, blank=blank,
            formatter=date_time_from_str)

    # -------------------------------------------------------------------------
    @classmethod
    def prompt_yes_no(cls, prompt_str):

        prompt_str += " [y/n]"

        return cls.prompt(prompt_str, help_str="Please type 'y' or 'n'",
            separator="?", formatter=_yes_no_formatter, blank=False)

    # -------------------------------------------------------------------------
    @classmethod
    def prompt_menu(cls, summary, prompt_str, options, none_option=False, 
        help_str="Please supply a number from the menu", custom_prompt=None, 
        custom_help=None, custom_blank=False, custom_formatter=None):

        header_names = [str(i) for i in range(len(options))]
        
        menu = {}
        lookup = []
        Option = namedtuple('Option', ['display', 'value'])
        for num, option_tuple in enumerate(options):
            option = Option(*option_tuple)
            menu[str(num)] = option.display
            lookup.append(option.value)

        if custom_prompt:
            menu[str(len(header_names))] = custom_prompt
            lookup.append('__custom__')
            header_names.append(str(len(header_names)))

        if none_option:
            menu[str(len(header_names))] = 'None'
            lookup.append(None)
            header_names.append(str(len(header_names)))

        def _formatter(response):

            try:
                response = int(response)
            except ValueError:
                raise ValueError("Invalid menu selection.")

            if not 0 <= response < len(header_names):
                raise ValueError("Invalid menu selection.")

            return lookup[response]

        output = Output()
        output.title = summary
        output.header_names = header_names

        output.add_item(
            menu, 
            color_all=Style.bright,
        )
            
        output.dump()

        response = Output.prompt(prompt_str, help_str=help_str, blank=False,
            formatter=_formatter)

        if response == "__custom__":
            response = Output.prompt(custom_prompt, help_str=custom_help,
                blank=custom_blank, formatter=custom_formatter)

        return response

    # -------------------------------------------------------------------------
    @classmethod
    def prompt_text_block(cls, prompt_str, help_str=None, blank=True, 
        separator=" (Ctrl+D to finish):"):

        while True:
            
            print prompt_str + separator + "\n"

            lines = []
            while True:
                try:
                    lines.append(raw_input())
                except EOFError:
                    break
            response = "\n".join(lines)

            # no response, either return none or continue depending on whether
            # blank values are allowed.
            if not response:
                if blank:
                    return None
                else:
                    print "  Response can not be empty."
                    continue

            return response
    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self):
        """Constructor."""
        super(Output, self).__init__()

        # turn off color changes after every print statement
        colorama.init(autoreset=True)

        # set defaults for data population
        self.reset()


        # ---- default values for display

        self.ellipses = u"\u2026"

        # title display
        self.title_color = self.default_color
        self.title_align = 'center'

        # separator between header and value in list output
        self.list_value_separator = ': '
        self.list_value_separator_color = self.default_color

        # horizontal padding in all output 
        self.horizontal_padding = 1 # spaces
        self.horizontal_separator = ' '
        self.horizontal_separator_color = self.default_color

        # vertical padding in all output 
        self.vertical_padding = 1 # lines
        self.vertical_separator = '-'
        self.vertical_separator_color = self.default_color

        self.table_cell_separator = '  '
        self.table_cell_separator_color = self.default_color
        self.table_header_separator = '='
        self.table_header_separator_color = self.default_color

        self.max_value_width = 100

    # -------------------------------------------------------------------------
    # Instance methods:
    # -------------------------------------------------------------------------
    def add_item(self, item_dict, color_all=None, colors=None):
        """Add an item to the list of items to output."""

        if not self.header_names:
            raise OutputError("No item header names specified.")

        item = defaultdict(str)

        colors = {} if colors is None else colors
        
        # the keywords must match header names.
        for key, value in item_dict.iteritems():
            if key not in self.header_names:
                raise OutputError("Unknown header item: " + str(key))
            item[key] = str(value)

            self._keep_stats(key, item[key])

            if not key in colors.keys() and color_all is not None:
                colors[key] = color_all

        item_info = (item, colors)

        self._items.append(item_info)

    # -------------------------------------------------------------------------
    def dump(self, output_format='list'):
        
        if output_format == 'list':
            self._dump_list()
        elif output_format == 'table':
            self._dump_table()
        else:
            raise OutputError("Unknown output format: " + output_format)

    # -------------------------------------------------------------------------
    def reset(self):
        self._force_full_header_names = True
        self._force_full_title = True
        self._header_names = None
        self._header_colors = defaultdict(str)
        self._header_alignments = defaultdict(str)
        self._items = []
        self._largest_header_width = 0
        self._largest_value_width = 0
        self._title = None
        self._value_sum = defaultdict(int)
        self._value_max = defaultdict(int)

    # -------------------------------------------------------------------------
    def set_header_colors(self, header_colors):

        if not self.header_names:
            raise OutputError("No item header names specified.")

        for header_name, color in header_colors.iteritems():
            if header_name not in self.header_names:
                raise OutputError("Unknown header item: " + str(header_name))

            self._header_colors[header_name] = color

    # -------------------------------------------------------------------------
    def set_header_alignment(self, header_alignments):

        if not self.header_names:
            raise OutputError("No item header names specified.")

        for header_name, alignment in header_alignments.iteritems():
            if header_name not in self.header_names:
                raise OutputError("Unknown header item: " + str(header_name))

            self._header_alignments[header_name] = alignment

    # -------------------------------------------------------------------------
    # Private methods:
    # -------------------------------------------------------------------------
    def _dump_list(self):

        display_width = self.list_display_width

        if self.vertical_padding:
            print self.vertical_padding_str,

        if self.title:
            print self.title_color + self._title_str(display_width)
        else:
            if self.vertical_separator:
                print self.vertical_separator_color + self._vertical_separator_str(display_width)

        for (item, colors) in self._items:

            if self.vertical_separator:
                print self.vertical_separator_color + self._vertical_separator_str(display_width)

            for header in self.header_names:
                value = item[header]

                color = colors[header] \
                    if header in colors.keys() else self.default_color
                
                line = \
                    self.horizontal_padding_str + \
                    self._header_colors[header] + \
                    self._list_header_str(header) + \
                    self.default_color + \
                    self.list_value_separator_color + \
                    self.list_value_separator + \
                    self.default_color + \
                    color + self._list_value_str(value) + \
                    self.default_color + \
                    self.horizontal_padding_str 
                print line

        if self.vertical_padding:
            print self.vertical_padding_str,

    # -------------------------------------------------------------------------
    def _dump_table(self):

        # sum of avg column widths
        avg_total = 0

        # sum of max column widths
        full_total = 0

        # avg column width for each header
        header_avgs = defaultdict(int)

        # compute avg width of each header/column
        for header_name in self.header_names:
            total_value_width = self._value_sum[header_name]
            avg_width = int(total_value_width / self.num_items)
            full_total += self._value_max[header_name]
            avg_total += avg_width
            header_avgs[header_name] = avg_width

        (term_width, term_height) = _get_terminal_size()

        # the horizontal cell dividers and padding placeholders
        placeholder_width = \
            ((self.num_headers - 1) * _len(self.table_cell_separator)) + \
            (self.horizontal_padding * 2)

        # calculate full table width if everything printed fully
        full_width = full_total + placeholder_width

        if full_width < term_width:
            display_width = full_width 
            header_widths = self._value_max
        else:
            display_width = term_width

            # total widths of columns only
            total_header_width_available = display_width - placeholder_width

            # compute header widths for each column
            header_widths = defaultdict(int)
            total_widths = 0
            for header_name in self.header_names:
                header_widths[header_name] = int(round(total_header_width_available * \
                    (header_avgs[header_name] / float(avg_total))))
                total_widths += header_widths[header_name]

            # give the leftover space to the last column
            leftover = total_header_width_available - total_widths
            header_widths[self.header_names[-1]] += leftover

        # ---- print the table

        if self.vertical_padding:
            print self.vertical_padding_str,

        if self.title:
            print self.title_color + self._title_str(display_width)

        print self.table_header_separator_color + \
              self._table_header_separator_str(display_width) + \
              self.default_color

        self._dump_table_headers(header_widths)

        print self.table_header_separator_color + \
              self._table_header_separator_str(display_width) + \
              self.default_color

        table_sep = \
            self.table_cell_separator_color + \
            self.table_cell_separator + \
            self.default_color

        for (item, colors) in self._items:

            line_parts = []

            for header in self.header_names:
                value = item[header]

                color = colors[header] \
                    if header in colors.keys() else self.default_color

                alignment = self._header_alignments[header]

                width = header_widths[header]
                value_display = self._list_value_str(value)

                if width > 0:
                    value_display = value_display[:width - 1] + self.ellipses \
                        if _len(value_display) > width \
                        else value_display
                else:
                    value_display = ""
                
                line_parts.append(
                    color + \
                    _align(value_display, alignment, width) + \
                    self.default_color
                )

            line = \
                self.horizontal_padding_str + \
                table_sep.join(line_parts) + \
                self.horizontal_padding_str 

            print line

            if self.vertical_separator:
                print self.vertical_separator_color + self._vertical_separator_str(display_width)

        if self.vertical_padding:
            print self.vertical_padding_str,

    # -------------------------------------------------------------------------
    def _dump_table_headers(self, header_widths):

        table_sep = \
            self.table_cell_separator_color + \
            self.table_cell_separator + \
            self.default_color

        header_parts = [] 
        for header_name in self.header_names:

            color = self._header_colors[header_name] 
            alignment = self._header_alignments[header_name]
            width = header_widths[header_name]

            if width > 0:
                header_display = header_name[:width - 1] + self.ellipses \
                    if _len(header_name) > width \
                    else header_name
            else:
                header_display = ""

            header_parts.append(
                color + \
                _align(header_display, alignment, width) + \
                self.default_color
            )

        line = \
            self.horizontal_padding_str + \
            table_sep.join(header_parts) + \
            self.horizontal_padding_str 
        
        print line

    # -------------------------------------------------------------------------
    def _list_header_str(self, header_name):
        return header_name.rjust(self._largest_header_width)

    # -------------------------------------------------------------------------
    def _list_value_str(self, value):
        if _len(value) > self.max_value_width:
            value = value[:self.max_value_width - 1] + self.ellipses

        return value

    # -------------------------------------------------------------------------
    def _table_header_separator_str(self, width):
        return self.table_header_separator * width

    # -------------------------------------------------------------------------
    def _title_str(self, width):
        title_str = self.title
        if not self.force_full_title and _len(title_str) > width:
            title_str = title_str[:width - 1] + self.ellipses

        return Style.bright + _align(title_str, self.title_align, width) + \
            Style.reset

    # -------------------------------------------------------------------------
    def _vertical_separator_str(self, width):
        return self.vertical_separator * width

    # -------------------------------------------------------------------------
    def _keep_stats(self, header, value):

        header_len = _len(header)
        value_len = _len(value)

        # sum of value widths per header
        self._value_sum[header] += value_len

        # keep track of the longest value per header
        if value_len > self._value_max[header]:
            self._value_max[header] = value_len

        # --- for list view

        # largest header width (across all headers)
        if header_len > self._largest_header_width:
            self._largest_header_width = header_len

        # largest value width (across all values)
        if value_len > self._largest_value_width:
            self._largest_value_width = value_len

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def default_color(self):
        return self.__class__._DEFAULT_COLOR

    # -------------------------------------------------------------------------
    @property
    def force_full_title(self):
        return self._force_full_title

    # -------------------------------------------------------------------------
    @force_full_title.setter
    def force_full_title(self, force):
        self._force_full_title = force

    # -------------------------------------------------------------------------
    @property
    def force_full_header_names(self):
        return self._force_full_header_names

    # -------------------------------------------------------------------------
    @force_full_header_names.setter
    def force_full_header_names(self, force):
        self._force_full_header_names = force

    # -------------------------------------------------------------------------
    @property
    def horizontal_padding_str(self):
        return " " * self.horizontal_padding

    # -------------------------------------------------------------------------
    @property
    def num_items(self):
        return len(self._items)

    # -------------------------------------------------------------------------
    @property
    def num_headers(self):
        return len(self.header_names)
    
    # -------------------------------------------------------------------------
    @property
    def vertical_padding_str(self):
        return "\n" * self.vertical_padding

    # -------------------------------------------------------------------------
    @property
    def header_names(self):
        """[str] header names for the data to output."""

        return self._header_names
    
    # -------------------------------------------------------------------------
    @header_names.setter
    def header_names(self, header_names):
        """Set the header names for the data to output."""

        if self._header_names is not None:
            raise OutputError("Header names already set.")
        elif not header_names:
            raise OutputError("Inavlid header names supplied.")

        self._header_names = header_names

        # pre-populate header colors
        for header_name in self._header_names:
            self._header_colors[header_name] = self.default_color
            self._header_alignments[header_name] = "left"

            if self.force_full_header_names:
                self._value_max[header_name] = _len(header_name)

    # -------------------------------------------------------------------------
    @property
    def list_display_width(self):
        """(int) width of list display based on current items."""

        (term_width, term_height) = _get_terminal_size()

        max_line_width = \
            (2 * self.horizontal_padding) + \
            self._largest_header_width + \
            _len(self.list_value_separator)

        if (max_line_width + self._largest_value_width) > term_width:
            self.max_value_width = term_width - max_line_width
            self._largest_value_width = self.max_value_width

        max_line_width += self._largest_value_width

        title_len = _len(self.title)
        if title_len > max_line_width:
            if title_len < term_width:
                max_line_width = title_len

        return min(term_width, max_line_width)

    # -------------------------------------------------------------------------
    @property
    def title(self):
        """(str) title for the output."""
        return self._title

    # -------------------------------------------------------------------------
    @title.setter
    def title(self, new_title):
        """Set the title for the output."""
        self._title = new_title 

# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------
class OutputError(Exception):
    pass

# -----------------------------------------------------------------------------
# Utility methods
# -----------------------------------------------------------------------------
def _align(in_str, alignment, width):
    
    if alignment == "left":
        return in_str.ljust(width)
    elif alignment == "right":
        return in_str.rjust(width)
    else:
        return in_str.center(width)

# -----------------------------------------------------------------------------
def _get_terminal_size():
    """Returns a tuple of width and height of the terminal."""
    if os.name == 'posix':
        return _get_terminal_size_posix()
    else:
        return _get_terminal_size_windows()

# -----------------------------------------------------------------------------
def _get_terminal_size_posix():
    """Returns a tuple for the terminal size on a posix system."""

    width = os.popen('tput cols', 'r').readline()
    height = os.popen('tput lines', 'r').readline()

    if not width:
        width = 80
    if not height:
        height = 25
 
    return (int(width), int(height))
 
# -----------------------------------------------------------------------------
def _get_terminal_size_windows():
    """Returns a tuple for the terminal size on a windows system."""

    from ctypes import windll, create_string_buffer
    import struct

    h = windll.kernel32.GetStdHandle(-12)
    csbi = create_string_buffer(22)
    res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
 
    #return default size if actual size can't be determined
    if not res: return (80, 25)
 
    (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy)\
        = struct.unpack("hhhhHhhhhhh", csbi.raw)
    width = int(right) - int(left) + 1
    height = int(bottom) - int(top) + 1
 
    return (width, height)

# -----------------------------------------------------------------------------
def _len(in_str):
    # get the length of a string, ignoring formatting characters

    pattern = re.compile("|".join([re.escape(c) for c in _special_chars]))
    return len(pattern.sub("", in_str))
 
# -----------------------------------------------------------------------------
def _yes_no_formatter(response):

    if response.lower() in ['y', 'yes']:
        return True

    elif response.lower() in ['n', 'no']:
        return False

    raise ValueError("Invalid yes/no response.")

