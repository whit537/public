import sys
import traceback
import xmlrpclib

from httpy import Response, mode


class Responder:
    """This responder serves XMLRPC requests.

        >>> import httpy
        >>> class Responder(httpy.responders.XMLRPC):
        ...   protected = ['private']
        ...   def private(self):
        ...     return 'leave me alone!'
        ...   def ping(self):
        ...     return 'pong'
        ...
        >>> responder = Responder()
        >>> coupler = httpy.couplers.StandAlone(responder)
        >>> coupler.go()
        httpy.server     INFO     httpy started on port 8080

    We borrowed some from SimpleXMLRPCDispatcher, but ended up simplifying.

    """

    __protected = ('respond', 'serve_xmlrpc')
    protected = ()

    def respond(self, request):
        return self.serve_xmlrpc(request)

    def serve_xmlrpc(self, request):
        """Serve an XMLRPC request.
        """
        if request.method != 'POST':
            raise Response(501)

        response = Response(200)
        response.headers['Content-Type'] = 'text/xml'
        try:
            params, method = xmlrpclib.loads(request.raw_body)


            # Find a callable.
            # ================

            try:
                protected = (  method.startswith('_')
                            or method in self.__protected
                            or method in self.protected
                              )
                if protected:
                    raise NotImplementedError(method)
                else:
                    func = getattr(self, method, None)
                    if func is None:
                        raise NotImplementedError(method)

            except NotImplementedError:
                fault = xmlrpclib.Fault( 404
                                       , "method '%s' " % method +
                                         "not found"
                                        )
                body = xmlrpclib.dumps(fault)


            else:
                # Call it.
                # ========

                try:
                    body = xmlrpclib.dumps( (func(*params),)
                                          , methodresponse=1
                                          , allow_none=True
                                           )
                except xmlrpclib.Fault, fault:
                    body = xmlrpclib.dumps(fault)
                except:
                    err = (sys.exc_type, sys.exc_value)
                    body = xmlrpclib.dumps(xmlrpclib.Fault(1, "%s:%s" % err))

            response.body = body


        except:     # bug in the module
            traceback.print_exc() # goes to stderr
            raise Response(500)

        else:       # valid XMLRPC response
            return response


XMLRPC = Responder
