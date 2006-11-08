import cStringIO
import inspect
from os.path import isdir, isfile, join

from aspen.utils import is_valid_identifier
from aspen.exceptions import *


clean = lambda x: x.split('#',1)[0].strip() # clears comments & whitespace
default_handlers_conf = """\

    fnmatch     aspen.rules.fnmatch
    hashbang    aspen.rules.hashbang
    mime-type   aspen.rules.mimetype


    [aspen.handlers.HTTP404]
    fnmatch *.py[cod]           # hide any compiled Python scripts


    [aspen.handlers.pyscript]
        fnmatch     *.py        # exec python scripts ...
    OR  hashbang                # ... and anything with a hashbang


    [aspen.handlers.Simplate]
    mime-type text/html         # run html files through the Simplates engine


    [aspen.handlers.static]
    fnmatch *                   # anything else, serve it statically

"""

README_aspen = """\
This directory is served by the application configured on line %d of
__/etc/apps.conf. To wit:

%s

"""


class _HandlerRuleSet(object):
    """Represent the set of rules associated with a handler.

    Some optimization ideas:

      - cache the results of match()
      - evaluate the expression after each rule is added, exit early if False

    """

    handler = None # the handler callable we are tracking
    _rules = None # a list containing the rules

    def __init__(self, rulefuncs, handler, handler_name):
        """Takes a mapping of rulename to rulefunc, and a handler callable.
        """
        self._funcs = rulefuncs
        self.handler = handler
        self.handler_name = handler_name

    def __str__(self):
        return "<RuleSet for %s>" % self.handler_name
    __repr__ = __str__


    def add(self, rule, lineno):
        """Given a rule string, add it to the rules for this handler.

        The first item in self._rules is a two-tuple: (rulename, predicate),
        subsequent items are three-tuples: (boolean, rulename, predicate).

            boolean -- one of 'and', 'or', 'and not'. Any NOT in the conf file
                       becomes 'and not' here.

            rulename -- a name defined in the first (anonymous) section of
                        handlers.conf; maps to a rule callable in self._funcs

            predicate -- a string that is meaningful to the rule callable

        lineno is for error handling.

        """
        if self._rules is None:                 # no rules yet
            parts = rule.split(None, 1)
            if len(parts) != 2:
                msg = "need two tokens in '%s'" % rule
                raise HandlersConfError(msg, lineno)
            rulename, predicate = parts
            if rulename not in self._funcs:
                msg = "no rule named '%s'" % rulename
                raise HandlersConfError(msg, lineno)
            self._rules = [(rulename, predicate)]
        else:                                   # we have at least one rule
            parts = rule.split(None, 2)
            if len(parts) not in (2,3):
                msg = "need two or three tokens in '%s'" % rule
                raise HandlersConfError(msg, lineno)
            parts.reverse()

            orig = parts.pop()
            boolean = orig.lower()
            if boolean not in ('and', 'or', 'not'):
                msg = "bad boolean '%s' in '%s'" % (orig, rule)
                raise HandlersConfError(msg, lineno)
            boolean = (boolean == 'not') and 'and not' or boolean

            rulename = parts.pop()
            if rulename not in self._funcs:
                msg = "no rule named '%s'" % rulename
                raise HandlersConfError(msg, lineno)

            predicate = parts and parts.pop() or None

            self._rules.append((boolean, rulename, predicate))


    def match(self, fp):
        """Given a file pointer (positioned at 0), return a boolean.

        I thought of allowing rules to return arbitrary values that would then
        be passed along to the handlers. Basically this was to support routes-
        style regular expression matching, but that is an application use case,
        and handlers are specifically not for applications but publications.

        """
        if not self._rules: # None or []
            raise HandlerError, "no rules to match"

        rulename, predicate = self._rules[0]                    # first
        expressions = [str(self._funcs[rulename](fp, predicate))]

        for boolean, rulename, predicate in self._rules[1:]:    # subsequent
            fp.seek(0)
            result = bool(self._funcs[rulename](fp, predicate))
            expressions.append('%s %s' % (boolean, result))

        expression = ' '.join(expressions)
        return eval(expression) # e.g.: True or False and not True


class HandlerLoader(object):

    def load_rulesets(self):
        """Return a list of HandlerRuleSet instances.

        This method parses the __/etc/handlers.conf file. This file begins with
        a newline-separated list of white-space-separated rule name/object name
        pairs. The rule names can be any string without whitespace.

        Each object name must specify a Python class, instance, module, or
        function in dotted notation. In each case we are looking for a callable
        that takes a file object (positioned at 0) and an arbitrary predicate
        string, and returns a boolean. Here's how each is treated:

            class -- instantiated with the website instance as a positional
                     argument; a 'rule' attribute is the callable

            instance/module -- a 'rule' attribute is the callable

            function -- the function itself is the callable


        If the object name has no dots, it is imported as a module/package. If
        it does contain dots, then the last name becomes the 'import' target, and
        the remaining dotted portion becomes the 'from' target.

            aspen.handlers.static => from aspen.handlers import static


        The comment character for this file is #, and comments can be included
        in-line. Blank lines are ignored, as is initial and trailing whitespace
        per-line.

        Example (this is Aspen's default handlers configuration):

            %s


        If the file __/etc/handlers.conf exists at all, these defaults
        disappear, and you must respecify these rules in your own file if you
        want them.

        """ % default_handlers_conf


        # Find a conf file to parse.
        # ==========================

        user_conf = False
        if self.paths.__ is not None:
            path = join(self.paths.__, 'etc', 'handlers.conf')
            if isfile(path):
                user_conf = True

        if user_conf:
            fp = open(path)
        else:
            fp = cStringIO.StringIO(default_handlers_conf)


        # We have a config file; proceed.
        # ===============================
        # The conditions in the loop below are not in the order found in the
        # file, but are in the order necessary for correct processing.

        rulefuncs = {} # a mapping of function names to rule functions
        rulesets = [] # a list of HandlerRuleSet objects
        ruleset = None # the HandlerRuleSet we are currently processing
        lineno = 0

        for line in fp:
            lineno += 1
            line = clean(line)
            if not line:                            # blank line
                continue
            elif line.startswith('['):              # new section
                if not line.endswith(']'):
                    raise HandlersConfError("missing end-bracket", lineno)
                name = line[1:-1]
                obj = self.import_(name, HandlersConfError, lineno)
                msg = ''
                if inspect.isfunction(obj):
                    obj.handle = obj
                elif not hasattr(obj, 'handle'):
                    msg = "handler object at %s has no 'handle' callable" % name
                elif not callable(obj.handle):
                    msg = "'handle' attribute of %s is not callable" % name
                if msg:
                    raise HandlersConfError(msg, lineno)
                ruleset = _HandlerRuleSet(rulefuncs, obj, name)
                rulesets.append(ruleset)
                continue
            elif ruleset is None:                   # anonymous section
                rulename, name = line.split(None, 1)
                obj = self.import_(name, HandlersConfError, lineno)
                msg = ''
                if inspect.isfunction(obj):
                    obj.rule = obj
                elif not hasattr(obj, 'rule'):
                    msg = "rule object at %s has no 'rule' callable" % name
                elif not callable(obj.rule):
                    msg = "'rule' attribute of %s is not callable" % name
                if msg:
                    raise HandlersConfError(msg, lineno)
                rulefuncs[rulename] = obj.rule
            else:                                   # named section
                ruleset.add(line, lineno)

        return rulesets


class AppLoader:

    def load_apps(self):
        """Return a list of (URI paths, application callable) tuples.

        This method parses the __/etc/apps.conf file. This file contains a
        newline-separated list of white-space-separated path name/object name
        pairs. The path names refer to URL-space, but must be reflected on the
        filesystem. If the trailing slash is given, then requests for that
        directory will first be redirected to the trailing slash before being
        handed off to the application. If no trailing slash is given, the
        application will also get requests w/o the slash. Applications match in
        the order specified.

        Each object name must specify a Python class, instance, module, or
        function in dotted notation. In each case we are looking for a callable
        that takes a request object and returns a response object. Here's how
        each is treated:

            class -- instantiated with the website instance as a positional
                     argument; a 'respond' attribute is the callable

            instance/module -- a 'respond' attribute is the callable

            function -- the function itself is the callable


        If the object name has no dots, it is imported as a module/package. If
        it does contain dots, then the last name becomes the 'import' target, and
        the remaining dotted portion becomes the 'from' target.

            example.apps.foo => from example.apps import foo


        The comment character for this file is #, and comments can be included
        in-line. Blank lines are ignored, as is initial and trailing whitespace
        per-line.

        Example:

            /foo        example.apps.foo    # will get both /foo and /foo/
            /bar/       example.apps.bar    # /bar will redirect to /bar/
            /bar        example.apps.Bar    # will never be called
            /bar/baz    example.apps.baz    # also never called


        If it doesn't already exist, aspen will place a file called README.aspen
        in each directory mentioned in apps.conf, containing the relevant line
        from apps.conf. If the directory does not exist, we raise AppsConfError.

        """

        # Find a conf file to parse.
        # ==========================

        apps = []

        if self.paths.__ is None:
            return apps

        path = join(self.paths.__, 'etc', 'apps.conf')
        if not isfile(path):
            return apps


        # We have a config file; proceed.
        # ===============================
        # The conditions in the loop below are not in the order found in the
        # file, but are in the order necessary for correct processing.

        fp = open(path)
        lineno = 0

        for line in fp:
            lineno += 1
            original = line # for README.aspen
            line = clean(line)
            if not line:                            # blank line
                continue
            else:                                   # specification
                urlpath, name = line.split(None, 1)
                if not urlpath.startswith('/'):
                    msg = "URL path not specified absolutely: %s" % line
                    raise AppsConfError(msg, lineno)
                fspath = self.static.translate(urlpath)
                if not isdir(fspath):
                    msg = "%s does not point to a directory" % fspath
                    raise AppsConfError(msg, lineno)
                readme = join(fspath, 'README.aspen')
                open(readme, 'w+').write(README_aspen % (lineno, original))

                obj = self.import_(name, AppsConfError, lineno)
                msg = ''
                if inspect.isfunction(obj):
                    obj.respond = obj
                elif not hasattr(obj, 'respond'):
                    msg = "app object at %s has no 'respond' callable" % name
                elif not callable(obj.respond):
                    msg = "'respond' attribute of %s is not callable" % name
                if msg:
                    raise AppsConfError(msg, lineno)

                obj.urlpath = urlpath
                apps.append((urlpath, obj))

        return apps


class ImportHelpers(object):
    """Aids for the loaders.
    """

    def import_(self, name, Err, lineno=None):
        """Given a dotted name and some error helpers, return an object.

        If Err is None then all ImportErrors are swallowed, and None is
        returned. If Err is not None, the lineno should be the line number of
        the file where the bad import name occurs.

        """
        obj = None
        if Err is None:
            try:
                obj = self.import_unsafe(name)
            except ImportError:
                pass
        else:
            try:
                obj = self.import_unsafe(name)
            except ImportError, err:
                raise Err(err.args[0], lineno)
        return obj


    def import_unsafe(self, name):
        """Import w/o error handling.

        If the imported thing is a class, we instantiate it with the website
        instance as a positional argument.

        """
        if not is_valid_identifier(name.replace('.','')):
            raise ImportError('%s is not a valid Python dotted name.' % name)
        if '.' not in name:
            exec 'import %s as obj'
        else:
            modname, objname = name.rsplit('.', 1)
            exec 'from %s import %s as obj' % (modname, objname)
        if inspect.isclass(obj):
            obj = obj(self)
        return obj
