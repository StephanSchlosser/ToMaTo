'''
Created on Nov 20, 2014

@author: Tim Gerhard
'''
from error import Error, UserError, InternalError #@UnresolvedImport
from django.shortcuts import render, redirect
import xmlrpclib, json, socket
from django.http import HttpResponse
from . import AuthError

def interpretError(error):
    debuginfos = []
    errormsg = "Message: "+error.message+" | Module: "+error.module+' | Data: '+str(error.data)
    typemsg = error.type+" ("+error.code+")"
    ajaxinfos = {}
    
    
    #TODO: insert some magic here.
    
    
    return (typemsg, errormsg, debuginfos, ajaxinfos)







def renderError(request, error):
    typemsg, errormsg, debuginfos, _ = interpretError(error)
    return render(request, "error/error.html", {'typemsg': typemsg, 'errormsg': errormsg, 'debuginfos': debuginfos}, status=500)

def renderFault (request, fault):
    import traceback
    traceback.print_exc()
    if isinstance(fault, Error):
        return renderError(request, fault)
    if isinstance(fault, socket.error):
        import os
        etype = "Socket error"
        ecode = fault.errno
        etext = os.strerror(fault.errno)
    elif isinstance(fault, AuthError):
        request.session['forward_url'] = request.build_absolute_uri()
        return redirect("tomato.main.login")
    elif isinstance(fault, xmlrpclib.ProtocolError):
        etype = "RPC protocol error"
        ecode = fault.errcode
        etext = fault.errmsg
        if ecode in [401, 403]:
            request.session['forward_url'] = request.build_absolute_uri()
            return redirect("tomato.main.login")
    elif isinstance(fault, xmlrpclib.Fault):
        etype = "RPC call error"
        ecode = fault.faultCode
        etext = fault.faultString
    else:
        etype = fault.__class__.__name__
        ecode = ""
        etext = fault.message
    return render(request, "error/fault.html", {'type': etype, 'code': ecode, 'text': etext}, status=500)
        



def ajaxError(error):
    typemsg, errormsg, debuginfos, ajaxinfos = interpretError(error)
    return HttpResponse(
                        json.dumps(
                                   {"success": False, 
                                    "error": {'raw': error.raw(), 
                                              'typemsg': typemsg, 
                                              'errormsg': errormsg, 
                                              'debuginfos': debuginfos, 
                                              'ajaxinfos': ajaxinfos}
                                    }
                                   )
                        )
    

def ajaxFault (fault): # stuff that happens in the actual function call
    if isinstance(fault, Error):
        return ajaxError(fault)
    elif isinstance(fault, xmlrpclib.Fault):
        return HttpResponse(json.dumps({"success": False, "error": fault.faultString}))
    elif isinstance(fault, xmlrpclib.ProtocolError):
        return HttpResponse(json.dumps({"success": False, "error": 'Error %s: %s' % (fault.errcode, fault.errmsg)}), status=fault.errcode if fault.errcode in [401, 403] else 200)                
    elif isinstance(fault, Exception):
        return HttpResponse(json.dumps({"success": False, "error": '%s:%s' % (fault.__class__.__name__, fault)}))
