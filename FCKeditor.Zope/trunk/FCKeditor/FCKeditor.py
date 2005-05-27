# Python
import re
from urllib import urlencode
from xml.sax import saxutils

# us
from Products.FCKeditor import FCKexception

class FCKtemplates:

    COMPATIBLE = """\
<div>
    <input type="hidden"
           id="%(InstanceName)s"
           name="%(InstanceName)s"
           value=%(Value)s />
    <input type="hidden"
           id="%(InstanceName)s___Config"
           value="%(ConfigQuerystring)s" />
    <iframe id="%(InstanceName)s___Frame"
            src="%(BasePath)seditor/fckeditor.html?InstanceName=%(InstanceName)s&Toolbar=%(ToolbarSet)s"
            width="%(Width)s" height="%(Height)s"
            frameborder="no" scrolling="no"></iframe>
</div>"""

    INCOMPATIBLE = """\
<div>
    <textarea name="%(InstanceName)s"
              rows="4" cols="40"
              style="width: %(Width)s; height: %(Height)s;"
              wrap="virtual" />
        %(Value)s
    </textarea>
</div>"""


class FCKeditor:
    """Provide API for tuning and instantiating an FCKeditor DHTML widget.
    """

    def __init__(self, InstanceName='MyEditor'):

        # defaults -- using instance attrs instead of class attrs so we can
        # use self.__dict__
        self.InstanceName       = self._scrub(InstanceName)
        self.Width              = '100%'
        self.Height             = '200px'
        self.ToolbarSet         = 'Default'
        self.Value              = ''
        self.BasePath           = '/FCKeditor/'
        self.ConfigQuerystring  = ''

        self.Config = {}

    _bad_chars = re.compile(r'[^a-zA-Z0-9-_]')
    def _scrub(self, InstanceName):
        """given an id, make it safe for use as an InstanceName, which is used
        as a CSS identifier. See:

            http://www.w3.org/TR/CSS21/syndata.html#value-def-identifier

        """
        scrubbed = self._bad_chars.sub('-', InstanceName)
        safety_belt = 0
        while not scrubbed[:1].isalpha(): # can only start with a letter
            scrubbed = scrubbed[1:]
            safety_belt += 1
            if safety_belt > 50: break
        if scrubbed == '':
            raise FCKexception, "The token '%s' has no " % InstanceName +\
                                "characters that are valid in a CSS " +\
                                "identifier."
        return scrubbed



    def Create(self):
        """Return an HTML snippet which instantiates an FCKeditor or a plain
        textarea.
        """

        if getattr(self, 'Compatible', None) is None:
            raise FCKexception, "You must run the SetCompatible method first"

        # parse width & height
        self.Width, self.Height = self._parse_dimensions( self.Width
                                                        , self.Height
                                                         )
        if self.Compatible:
            # escape the initial HTML value for use as an HTML attribute
            self.Value = saxutils.quoteattr(self.Value)

            # marshall config into a querystring
            self.ConfigQuerystring = urlencode(self.Config) # from urllib

            return FCKtemplates.COMPATIBLE % self.__dict__
        else:
            # escape the initial HTML value for use inside a <textarea>
            self.Value = saxutils.escape(self.Value)

            return FCKtemplates.INCOMPATIBLE % self.__dict__

    def _parse_dimensions(self, w, h):
        """Given a width and a height either as ints or strings, return a tuple
        of strings.
        """
        if str(w).isdigit():
            w = '%spx' % w
        if str(h).isdigit():
            h = '%spx' % h
        return (w, h)



    def SetCompatible(self, useragent):
        """Given a browser's user-agent string, set a boolean on self and
        return it.
        """

        useragent = useragent.lower()
        Compatible = False # default

    	# Internet Explorer
        """Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)"""
    	match = re.search(r'msie (\d*\.\d*)', useragent)
    	if match is not None:
    	    version = match.group(1)
    	    if version is not None:
        	    Compatible = float(version) >= 5.5

    	# Gecko
        """Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.7) Gecko/20050414 Firefox/1.0.3"""
    	match = re.search(r'gecko/(\d*)', useragent)
    	if match is not None:
    	    version = match.group(1)
    	    if version is not None:
	            Compatible = int(version) >= 20030210

        self.Compatible = Compatible
        return Compatible
