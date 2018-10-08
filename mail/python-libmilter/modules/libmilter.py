#!/usr/bin/python

# This file is part of python-libmilter.
# 
# python-libmilter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# python-libmilter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with python-libmilter.  If not, see <http://www.gnu.org/licenses/>.

import struct , sys , select , threading , socket , time , os , signal

# Turn debugging on or off
DEBUG = 0
if DEBUG:
    import traceback

__version__ = '1.0.3'

#
# Standard Sendmail Constants
#
# These are flags stating what, we, the client will want to do (SMFIF_*) {{{
SMFIF_ADDHDRS = 0x01            # We may add headers
SMFIF_CHGBODY = 0x02            # We may replace body
SMFIF_ADDRCPT = 0x04            # We may add recipients
SMFIF_DELRCPT = 0x08            # We may delete recipients
SMFIF_CHGHDRS = 0x10            # We may change/delete headers
SMFIF_QUARANTINE = 0x20         # We may quarantine envelope
# End version 2
SMFIF_CHGFROM = 0x40            # We may replace the sender
SMFIF_ADDRCPT_PAR = 0x80        # We may add recipients + args
SMFIF_SETSYMLIST = 0x100        # We may send macro names CURRENTLY UNSUPPORTED

SMFIF_ALLOPTS_V2 = SMFIF_ADDHDRS | SMFIF_CHGBODY | SMFIF_ADDRCPT | \
    SMFIF_DELRCPT | SMFIF_CHGHDRS | SMFIF_QUARANTINE
SMFIF_ALLOPTS_V6 = SMFIF_CHGFROM | SMFIF_ADDRCPT_PAR | SMFIF_SETSYMLIST
SMFIF_ALLOPTS = SMFIF_ALLOPTS_V2 | SMFIF_ALLOPTS_V6

SMFIF_OPTS = {
    SMFIF_ADDHDRS: 'addhdrs' ,
    SMFIF_CHGBODY: 'chgbody' ,
    SMFIF_ADDRCPT: 'addrcpt' ,
    SMFIF_DELRCPT: 'delrcpt' ,
    SMFIF_CHGHDRS: 'chghdrs' ,
    SMFIF_QUARANTINE: 'quarantine' ,
    SMFIF_CHGFROM: 'chgfrom' ,
    SMFIF_ADDRCPT_PAR: 'addrcpt_wargs' ,
    SMFIF_SETSYMLIST: 'setsymlist' ,
}
# }}}

# These are mainly flags to be sent during option negotiation (SMFIP_*) {{{
SMFIP_NOCONNECT = 0x01      # We don't want connect info
SMFIP_NOHELO = 0x02         # We don't want HELO info
SMFIP_NOMAIL = 0x04         # We don't want MAIL info
SMFIP_NORCPT = 0x08         # We don't want RCPT info
SMFIP_NOBODY = 0x10         # We don't want the body
SMFIP_NOHDRS = 0x20         # We don't want the headers
SMFIP_NOEOH = 0x40          # We don't want the EOH
# End version 2
SMFIP_NR_HDR = 0x80         # We won't reply to the headers
SMFIP_NOHREPL = SMFIP_NR_HDR
SMFIP_NOUNKNOWN = 0x100     # We don't want any unknown cmds
SMFIP_NODATA = 0x200        # We don't want the DATA cmd
SMFIP_SKIP = 0x400          # MTA supports the SMFIS_SKIP
SMFIP_RCPT_REJ = 0x800      # We want rejected RCPTs
SMFIP_NR_CONN = 0x1000      # We don't reply to connect info
SMFIP_NR_HELO = 0x2000      # We don't reply to HELO info
SMFIP_NR_MAIL = 0x4000      # We don't reply to MAIL info
SMFIP_NR_RCPT = 0x8000      # We don't reply to RCPT info
SMFIP_NR_DATA = 0x10000     # We don't reply to DATA info
SMFIP_NR_UNKN = 0x20000     # We don't reply to UNKNOWN
SMFIP_NR_EOH = 0x40000      # We don't reply to eoh
SMFIP_NR_BODY = 0x80000     # We don't reply for a body chunk
SMFIP_HDR_LEADSPC = 0x100000    # header value has leading space

# All protos
SMFIP_ALLPROTOS_V2 = SMFIP_NOCONNECT | SMFIP_NOHELO | SMFIP_NOMAIL | \
    SMFIP_NORCPT | SMFIP_NOBODY | SMFIP_NOHDRS | SMFIP_NOEOH
SMFIP_ALLPROTOS_V6 = SMFIP_NR_HDR | SMFIP_NOUNKNOWN | SMFIP_NODATA | \
    SMFIP_SKIP | SMFIP_RCPT_REJ | SMFIP_NR_CONN | SMFIP_NR_HELO | \
    SMFIP_NR_MAIL | SMFIP_NR_RCPT | SMFIP_NR_DATA | SMFIP_NR_UNKN | \
    SMFIP_NR_EOH | SMFIP_NR_BODY | SMFIP_HDR_LEADSPC
SMFIP_ALLPROTOS = SMFIP_ALLPROTOS_V2 | SMFIP_ALLPROTOS_V6

SMFIP_PROTOS = {
    SMFIP_NOCONNECT: 'noconnect',
    SMFIP_NOHELO: 'nohelo' ,
    SMFIP_NOMAIL: 'nomail' ,
    SMFIP_NORCPT: 'norcpt' ,
    SMFIP_NOBODY: 'nobody' ,
    SMFIP_NOHDRS: 'nohdrs' ,
    SMFIP_NOEOH: 'noeoh' ,
    SMFIP_NOUNKNOWN: 'nounknown' ,
    SMFIP_NODATA: 'nodata' ,
    SMFIP_SKIP: 'skip' ,
    SMFIP_RCPT_REJ: 'wantrej' ,
    SMFIP_NR_HDR: 'noreplhdr' ,
    SMFIP_NR_CONN: 'noreplconn' ,
    SMFIP_NR_HELO: 'noreplhelo' ,
    SMFIP_NR_MAIL: 'noreplmail' ,
    SMFIP_NR_RCPT: 'noreplrcpt' ,
    SMFIP_NR_DATA: 'norepldata' ,
    SMFIP_NR_UNKN: 'noreplunkn' ,
    SMFIP_NR_EOH: 'norepleoh' ,
    SMFIP_NR_BODY: 'noreplbody' ,
    SMFIP_HDR_LEADSPC: 'hdrleadspc' ,
}
# }}}

# Network protocol families (SMFIA_*) {{{
SMFIA_UNKNOWN = 'U'         # Unknown
SMFIA_UNIX = 'L'            # Unix/local
SMFIA_INET = '4'            # inet - ipv4
SMFIA_INET6 = '6'           # inet6 - ipv6
# }}}

# Macros sent from the MTA (SMFIC_*) {{{
SMFIC_ABORT = 'A'           # Abort
SMFIC_BODY = 'B'            # Body chunk
SMFIC_CONNECT = 'C'         # Connection info
SMFIC_MACRO = 'D'           # Define macro
SMFIC_BODYEOB = 'E'         # Final body chunk
SMFIC_HELO = 'H'            # HELO
SMFIC_HEADER = 'L'          # Header
SMFIC_MAIL = 'M'            # MAIL from
SMFIC_EOH = 'N'             # eoh
SMFIC_OPTNEG = 'O'          # Option negotiation
SMFIC_QUIT = 'Q'            # QUIT
SMFIC_RCPT = 'R'            # RCPT to
# End Version 2
SMFIC_DATA = 'T'            # DATA
SMFIC_UNKNOWN = 'U'         # Any unknown command
SMFIC_QUIT_NC = 'K'         # Quit + new connection

# My shortcut for body related macros
SMFIC_BODY_MACS = (SMFIC_DATA , SMFIC_HEADER , SMFIC_EOH , SMFIC_BODY)
# }}}

# Responses/commands that we send to the MTA (SMFIR_*) {{{ 
SMFIR_ADDRCPT = '+'         # Add recipient 
SMFIR_DELRCPT = '-'         # Remove recipient 
SMFIR_ACCEPT = 'a'          # Accept 
SMFIR_REPLBODY = 'b'        # Replace body (chunk)
SMFIR_CONTINUE = 'c'        # Continue
SMFIR_DISCARD = 'd'         # Discard
SMFIR_ADDHEADER = 'h'       # Add header
SMFIR_CHGHEADER = 'm'       # Change header
SMFIR_PROGRESS = 'p'        # Progress
SMFIR_QUARANTINE = 'q'      # Quarantine
SMFIR_REJECT = 'r'          # Reject
SMFIR_TEMPFAIL = 't'        # Tempfail
SMFIR_REPLYCODE = 'y'       # For setting the reply code
# End Version 2
SMFIR_CONN_FAIL = 'f'       # Cause a connection failure
SMFIR_SHUTDOWN = '4'        # 421: shutdown (internal to MTA)
SMFIR_INSHEADER = 'i'       # Insert header
SMFIR_SKIP = 's'            # Skip further events of this type
SMFIR_CHGFROM = 'e'         # Change sender (incl. ESMTP args)
SMFIR_ADDRCPT_PAR = '2'     # Add recipient (incl. ESMTP args)
SMFIR_SETSYMLIST = 'l'      # Set list of symbols
# }}}

# Macro Class Numbers {{{
#
# Version 6 only
# Macro class numbers, to identify the optional macro name lists that
# may be sent after the initial negotiation header
SMFIM_CONNECT = 0           # Macros for connect
SMFIM_HELO = 1              # Macros for HELO
SMFIM_ENVFROM = 2           # Macros for MAIL from
SMFIM_ENVRCPT = 3           # Macros for RCPT to
SMFIM_DATA = 4              # Macros for DATA
SMFIM_EOM = 5               # Macros for end of message
SMFIM_EOH = 6               # Macros for end of header
# }}}

MILTER_CHUNK_SIZE = 65536

# My Constants -- tables and helpers {{{

# Optional callbacks
optCBs = {
    'connect': (SMFIP_NOCONNECT , SMFIP_NR_CONN) ,
    'helo': (SMFIP_NOHELO , SMFIP_NR_HELO) ,
    'mailFrom': (SMFIP_NOMAIL , SMFIP_NR_MAIL) ,
    'rcpt': (SMFIP_NORCPT , SMFIP_NR_RCPT) ,
    'header': (SMFIP_NOHDRS , SMFIP_NR_HDR) ,
    'eoh': (SMFIP_NOEOH , SMFIP_NR_EOH) ,
    'data': (SMFIP_NODATA , SMFIP_NR_DATA) ,
    'body': (SMFIP_NOBODY , SMFIP_NR_BODY) ,
    'unknown': (SMFIP_NOUNKNOWN , SMFIP_NR_UNKN) ,
}

protoMap = {
    SMFIC_CONNECT: 'connect' ,
    SMFIC_HELO: 'helo' ,
    SMFIC_MAIL: 'mailFrom' ,
    SMFIC_RCPT: 'rcpt' ,
    SMFIC_HEADER: 'header' ,
    SMFIC_EOH: 'eoh' ,
    SMFIC_DATA: 'data' ,
    SMFIC_BODY: 'body' ,
    SMFIC_UNKNOWN: 'unknown' ,
}

# Milter version global for use by the decorators during init
_milterVersion = 2
# }}}

# The register for deferreds
DEFERRED_REG = set()

#
# Exceptions {{{
#
class InvalidPacket(Exception):
    def __init__(self , partialPacket , cmds , *args , **kwargs):
        Exception.__init__(self , *args , **kwargs)
        self.pp = partialPacket
        self.partialPacket = self.pp
        self.cmds = cmds

class UnsupportedError(Exception):
    pass

class UnknownError(Exception):
    pass

class RequiredCallbackError(Exception):
    pass
# }}}

#
# Deferreds {{{
#
class Deferred(object):
    pass

class DeferToThread(Deferred):
    def __init__(self , cb , *args , **kwargs):
        global DEFERRED_REG
        self.result = None
        self.completed = False
        self.error = None
        self.callbacks = []
        self.errbacks = []
        t = threading.Thread(target=self._wrapper , args=(cb , args , kwargs))
        t.daemon = True
        t.start()
        DEFERRED_REG.add(self)

    def _wrapper(self , cb , args , kwargs):
        try:
            self.result = cb(*args , **kwargs)
        except Exception , e:
            self.error = e
        self.completed = True

    def addCallback(self , cb , *args , **kwargs):
        self.callbacks.append((cb , args , kwargs))

    def addErrback(self , eb , *args , **kwargs):
        self.errbacks.append((eb , args , kwargs))

    def callCallbacks(self):
        if not self.completed: return
        for cb , a , kw in self.callbacks:
            cb(self.result , *a , **kw)
        del self.callbacks
        del self.errbacks

    def callErrbacks(self):
        if not self.completed: return
        for cb , a , kw in self.errbacks:
            cb(self.error , *a , **kw)
        del self.callbacks
        del self.errbacks
# }}}

#
# Utility functions {{{
#
idCounter = 0
def getId():
    global idCounter
    idCounter += 1
    return idCounter

def pack_uint32(i):
    return struct.pack('!I' , i)

def pack_uint16(i):
    return struct.pack('!H' , i)

def unpack_uint32(s):
    return struct.unpack('!I' , s)[0]

def unpack_uint16(s):
    return struct.unpack('!H' , s)[0]

def parse_packet(p):
    ret = []
    remaining = 0
    while p:
        if len(p) < 4:
            raise InvalidPacket(p , ret , 'The packet is too small to '
                'contain any info (%d): %r' % (len(p) , p))
        length = unpack_uint32(p[:4])
        pend = length + 4
        contents = p[4:pend]
        if len(contents) < length:
            remaining = length - len(contents)
        ret.append(contents)
        p = p[pend:]
    return (ret , remaining)

def readUntilNull(s):
    """
    Read a string until a null is encountered

    returns (string up to null , remainder after null)
    """
    item = s.split('\0' , 1)
    if len(item) == 1:
        return (item[0] , None)
    else:
        return (item[0] , item[1])

def checkData(data , macro):
    if not data[0] == macro:
        raise UnknownError('Command does not start with correct '
                'MACRO: %s (%s) should be %s' % (data[0] , data , macro))

def dictFromCmd(cmd):
    d = {}
    while cmd and len(cmd) > 1:
        key , rem = readUntilNull(cmd)
        key = key.strip('{}')
        if rem:
            val , rem = readUntilNull(rem)
        else:
            val = None
        d[key] = val
        cmd = rem
    return d

def debug(msg , level=1 , protId=0):
    if not DEBUG: return
    if level <= DEBUG:
        out = '[%s] DEBUG: ' % time.strftime('%H:%M:%S')
        if protId:
            out += 'ID: %d ; ' % protId
        out += msg
        print >> sys.stderr , out
# }}}

# Response Constants {{{
#
# Constants for responses back to the MTA.  You should use these actions
# at the end of each callback.  If none of these are specified,
# CONTINUE is used as the default
#
ACCEPT = pack_uint32(1) + SMFIR_ACCEPT
CONTINUE = pack_uint32(1) + SMFIR_CONTINUE
REJECT = pack_uint32(1) + SMFIR_REJECT
TEMPFAIL = pack_uint32(1) + SMFIR_TEMPFAIL
DISCARD = pack_uint32(1) + SMFIR_DISCARD
CONN_FAIL = pack_uint32(1) + SMFIR_CONN_FAIL
SHUTDOWN = pack_uint32(1) + SMFIR_SHUTDOWN
# }}}

#
# Decorators {{{
#
def callInThread(f):
    def newF(*args , **kwargs):
        inst = args[0]
        defrd = DeferToThread(f , *args , **kwargs)
        defrd.addCallback(_onCITSuccess , inst)
        defrd.addErrback(_onCITFail , inst)
        return defrd
    return newF

# callInThread success callback
def _onCITSuccess(res , inst):
    if res:
        inst.send(res)

# callInThread fail callback
def _onCITFail(fail , inst):
    inst.log(str(fail))

# Use this decorator when the callback should not be sent from the MTA
def noCallback(f):
    global _milterVersion
    fname = f.__name__
    if not fname in optCBs:
        raise RequiredCallbackError('function %s is NOT an optional callback' %
            fname)
    def newF(*args , **kwargs):
        pass
    newF.protos = optCBs[fname][0]
    return newF

# Use this decorator when the callback response is not necessary
def noReply(f):
    global _milterVersion
    fname = f.__name__
    if not fname in optCBs:
        raise RequiredCallbackError('function %s is NOT an optional callback' %
            fname)
    _milterVersion = 6
    def newF(*args , **kwargs):
        return f(*args , **kwargs)
    newF.protos = optCBs[fname][1]
    return newF
# }}}

# Dummy lock for use with a ThreadFactory
# class DummyLock {{{
class DummyLock(object):
    def acquire(self):
        return True

    def release(self):
        return True
#}}}

#
# Start implementation stuff
#
# class ThreadMixin {{{
class ThreadMixin(threading.Thread):
    def run(self):
        self._sockLock = DummyLock()
        while True:
            buf = ''
            try:
                buf = self.transport.recv(MILTER_CHUNK_SIZE)
            except AttributeError:
                # Socket has been closed
                pass
            except socket.error:
                pass
            except socket.timeout:
                pass
            if not buf:
                try:
                    self.transport.close()
                except:
                    pass
                self.connectionLost()
                break
            try:
                self.dataReceived(buf)
            except Exception , e:
                self.log('AN EXCEPTION OCCURED IN %s: %s' % (self.id , e))
                if DEBUG:
                    traceback.print_exc()
                    debug('AN EXCEPTION OCCURED: %s' % e , 1 , self.id)
                self.connectionLost()
                break
# }}}

# class ForkMixin {{{
class ForkMixin(object):
    def start(self):
        # Fork and run
        if not os.fork():
            self.run()
            os._exit(0)
        else:
            return

    def run(self):
        self._sockLock = DummyLock()
        while True:
            buf = ''
            try:
                buf = self.transport.recv(MILTER_CHUNK_SIZE)
            except AttributeError:
                # Socket has been closed
                pass
            except socket.error:
                pass
            except socket.timeout:
                pass
            if not buf:
                try:
                    self.transport.close()
                except:
                    pass
                self.connectionLost()
                break
            try:
                self.dataReceived(buf)
            except Exception , e:
                self.log('AN EXCEPTION OCCURED IN %s: %s' % (self.id , e))
                if DEBUG:
                    traceback.print_exc()
                    debug('AN EXCEPTION OCCURED: %s' % e , 1 , self.id)
                self.connectionLost()
                break
        #self.log('Exiting child process')
# }}}

# class MilterProtocol {{{
class MilterProtocol(object):
    """
    A replacement for the C libmilter library, all done in pure Python.
    Subclass this and implement the overridable callbacks.
    """
    # Class vars and __init__() {{{
    def __init__(self , opts=0 , protos=0):
        """
        Initialize all the instance variables
        """
        self.id = getId()
        self.transport = None
        self._opts = opts        # Milter options (SMFIF_*)
        self.milterVersion = _milterVersion     # Default milter version
        self.protos = protos      # These are the SMFIP_* options
        if self._opts & SMFIF_ALLOPTS_V6:
            self.milterVersion = 6
        for fname in optCBs:
            f = getattr(self , fname)
            p = getattr(f , 'protos' , 0)
            self.protos |= p
        self.closed = False
        self._qid = None         # The Queue ID assigned by the MTA       
        self._mtaVersion = 0
        self._mtaOpts = 0
        self._mtaProtos = 0
        self._sockLock = threading.Lock()
        # The next 4 vars are temporary state buffers for the 3 ways
        # a packet can be split
        self._partial = None
        self._partialHeader = None
        self._lastMacro = None
        self._MACMAP = {
            SMFIC_CONNECT: self._connect ,
            SMFIC_HELO: self._helo ,
            SMFIC_MAIL: self._mailFrom ,
            SMFIC_RCPT: self._rcpt ,
            SMFIC_HEADER: self._header ,
            SMFIC_EOH: self._eoh ,
            SMFIC_DATA: self._data ,
            SMFIC_BODY: self._body ,
            SMFIC_BODYEOB: self._eob ,
            SMFIC_ABORT: self._abort ,
            SMFIC_QUIT: self._close ,
            SMFIC_UNKNOWN: self._unknown ,
        }
    # }}}

    #
    # Twisted method implementations {{{
    #
    def connectionLost(self , reason=None):
        """
        The connection is lost, so we call the close method if it hasn't
        already been called
        """
        self._close()

    def dataReceived(self , buf):
        """
        This is the raw data receiver that calls the appropriate
        callbacks based on what is received from the MTA
        """
        remaining = 0
        cmds = []
        pheader = ''
        debug('raw buf: %r' % buf , 4 , self.id)
        if self._partialHeader:
            pheader = self._partialHeader
            debug('Working a partial header: %r ; cmds: %r' % (pheader , cmds) ,
                4 , self.id)
            buf = pheader + buf
            self._partialHeader = None
        if self._partial:
            remaining , pcmds = self._partial
            self._partial = None
            buflen = len(buf)
            pcmds[-1] += buf[:remaining]
            buf = buf[remaining:]
            cmds.extend(pcmds)
            debug('Got a chunk of a partial: len: %d ; ' % buflen +
                'end of prev buf: %r ; ' % cmds[-1][-10:] +
                'start of new buf: %r ; ' % buf[:10] +
                'qid: %s ; ' % self._qid , 4 , self.id)
            if buflen < remaining:
                remaining -= buflen
                self._partial = (remaining , cmds)
                return
            remaining = 0
        if buf:
            curcmds = []
            try:
                curcmds , remaining = parse_packet(buf)
            except InvalidPacket , e:
                debug('Found a partial header: %r; cmdlen: %d ; buf: %r' % 
                    (e.pp , len(e.cmds) , buf) , 2 , self.id)
                cmds.extend(e.cmds)
                self._partialHeader = e.pp
            else:
                cmds.extend(curcmds)
        debug('parsed packet, %d cmds , %d remaining: cmds: %r ; qid: %s' % 
            (len(cmds) , remaining , cmds , self._qid) , 2 , self.id)
        if remaining:
            self._partial = (remaining , cmds[-1:])
            cmds = cmds[:-1]
        if cmds:
            self._procCmdAndData(cmds)
    # }}}

    #
    # Utility functions {{{
    #
    def _procCmdAndData(self , cmds):
        skipNum = 0
        toSend = ''
        for i , cmd in enumerate(cmds):
            toSend = ''
            mtype = ''
            firstLet = cmd[0]
            if skipNum:
                skipNum -= 1
                continue
            elif firstLet == SMFIC_OPTNEG:
                debug('MTA OPTS: %r' % cmd , 4 , self.id)
                toSend = self._negotiate(cmd)
            elif firstLet == SMFIC_ABORT:
                self._abort()
                continue
            elif firstLet == SMFIC_QUIT or \
                    firstLet == SMFIC_QUIT_NC:
                self._close()
                continue
            elif firstLet == SMFIC_MACRO:
                # We have a command macro.  We just store for when the
                # command comes back up
                self._lastMacro = cmd
                continue
            elif firstLet in self._MACMAP:
                mtype = cmd[0]
            if toSend and not mtype:
                # Basically, we just want to send something back
                pass
            elif mtype not in self._MACMAP:
                raise UnsupportedError('Unsupported MACRO in '
                    '%d: %s (%s)' % (self.id , mtype , cmd))
            else:
                lmtype = None
                if self._lastMacro is not None and len(self._lastMacro) > 1:
                    lmtype = self._lastMacro[1:2]
                d = [cmd]
                macro = None
                if lmtype == mtype:
                    macro = self._lastMacro
                if mtype in protoMap:
                    nc = optCBs[protoMap[mtype]][0]
                    nr = optCBs[protoMap[mtype]][1]
                    if self.protos & nc:
                        debug('No callback set for %r' % self._MACMAP[mtype] ,
                            4 , self.id)
                        # There is a nocallback set for this, just continue
                        continue
                    elif self.protos & nr:
                        # No reply for this, just run it and discard 
                        # the response
                        debug('No response set for %r' % self._MACMAP[mtype] ,
                            4 , self.id)
                        self._MACMAP[mtype](macro , d)
                        continue
                # Run it and send back to the MTA
                debug('Calling %r for qid: %s' % (self._MACMAP[mtype] , 
                    self._qid) , 4 , self.id)
                toSend = self._MACMAP[mtype](macro , d)
                if not toSend:
                    # If there was not a return value and we get here, toSend
                    # should be set to CONTINUE
                    toSend = CONTINUE
            if toSend and not isinstance(toSend , Deferred):
                self.send(toSend)
    
    def _getOptnegPkt(self):
        """
        This is a simple convenience function to create an optneg
        packet -- DO NOT OVERRIDE UNLESS YOU KNOW WHAT YOU ARE DOING!!
        """
        self._opts = self._opts & self._mtaOpts
        self.protos = self.protos & self._mtaProtos
        s = SMFIC_OPTNEG + pack_uint32(self._mtaVersion) + \
                pack_uint32(self._opts) + pack_uint32(self.protos)
        s = pack_uint32(len(s)) + s
        return s

    def log(self , msg):
        """
        Override this in a subclass to display messages
        """
        pass

    def send(self , msg):
        """
        A simple wrapper for self.transport.sendall
        """
        self._sockLock.acquire()
        try:
            debug('Sending: %r' % msg , 4 , self.id)
            self.transport.sendall(msg)
        except AttributeError , e:
            emsg = 'AttributeError sending %s: %s' % (msg , e)
            self.log(emsg)
            debug(emsg)
        except socket.error , e:
            emsg = 'Socket Error sending %s: %s' % (msg , e)
            self.log(emsg)
            debug(emsg)
        self._sockLock.release()
    # }}}

    #
    # Raw data callbacks {{{
    # DO NOT OVERRIDE THESE UNLESS YOU KNOW WHAT YOU ARE DOING!!
    #
    def _negotiate(self , cmd):
        """
        Handles the opening optneg packet from the MTA
        """
        cmd = cmd[1:]
        v , mtaOpts , mtaProtos = struct.unpack('!III' , cmd)
        self._mtaVersion = v
        self._mtaOpts = mtaOpts
        self._mtaProtos = mtaProtos
        return self._getOptnegPkt()

    def _connect(self , cmd , data):
        """
        Parses the connect info from the MTA, calling the connect()
        method with (<reverse hostname> , <ip family> , <ip addr> , 
            <port> , <cmdDict>)
        """
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        data = data[0]
        hostname = ''
        family = ''
        port = -1
        ip = ''
        if data:
            checkData(data , SMFIC_CONNECT)
            hostname , rem = readUntilNull(data[1:])
            family = rem[0]
            if family != SMFIA_UNKNOWN:
                port = unpack_uint16(rem[1:3])
                ip = rem[3:-1]
        return self.connect(hostname , family , ip , port , md)

    def _helo(self , cmd , data):
        """
        Parses the helo info from the MTA and calls helo() with 
        (<helo name>)
        """
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        data = data[0]
        heloname = ''
        if data:
            checkData(data , SMFIC_HELO)
            heloname = data[1:-1]
        return self.helo(heloname)

    def _mailFrom(self , cmd , data):
        """
        Parses the MAIL FROM info from the MTA and calls mailFrom()
        with (<from addr> , <cmdDict>)
        """
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        data = data[0]
        mfrom = ''
        if data:
            mfrom = data[1:-1]
        # Return the mail from address parsed by the MTA, if possible
        if md.has_key('mail_addr'):
            mfrom = md['mail_addr']
        if md.has_key('i'):
            self._qid = md['i']
        return self.mailFrom(mfrom , md)

    def _rcpt(self , cmd , data):
        """
        Parses the RCPT TO info from the MTA and calls rcpt()
        with (<rcpt addr> , <cmdDict>)
        """
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        data = data[0]
        rcpt = ''
        if data:
            rcpt = data[1:-1]
        elif md.has_key('rcpt_addr'):
            rcpt = md['rcpt_addr']
        if md.has_key('i'):
            self._qid = md['i']
        return self.rcpt(rcpt , md)

    def _header(self , cmd , data):
        """
        Parses the header from the MTA and calls header() with
        (<header name> , <header value> , <cmdDict>)
        """
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        data = data[0]
        key = ''
        val = ''
        if md.has_key('i'):
            self._qid = md['i']
        if data:
            key , rem = readUntilNull(data[1:])
            val , rem = readUntilNull(rem)
            if rem:
                raise UnknownError('Extra data for header: %s=%s (%s)' % (key , 
                    val , data))
        return self.header(key , val , md)

    def _eoh(self , cmd , data):
        """
        Parses the End Of Header from the MTA and calls eoh() with
        (<cmdDict>)
        """
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        if md.has_key('i'):
            self._qid = md['i']
        return self.eoh(md)

    def _data(self , cmd , data):
        """
        Parses the DATA call from the MTA and calls data() with (<cmdDict>)
        """
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        if md.has_key('i'):
            self._qid = md['i']
        return self.data(md)

    def _body(self , cmd , data):
        """
        Parses the body chunk from the MTA and calls body() with
        (<body chunk> , <cmdDict>) 
        """
        data = data[0]
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        chunk = ''
        if md.has_key('i'):
            self._qid = md['i']
        if data:
            chunk = data[1:]
        return self.body(chunk , md)

    def _eob(self , cmd , data):
        """
        Parses the End Of Body from the MTA and calls eob() with
        (<cmdDict>)
        """
        md = {}
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        if md.has_key('i'):
            self._qid = md['i']
        ret = self.eob(md)
        return ret

    def _close(self , cmd=None , data=None):
        """
        This is a wrapper for close() that checks to see if close()
        has already been called and calls it if it has not.  This
        will also close the transport's connection.
        """
        if not self.closed:
            self.closed = True
            self.transport = None
            self.close()

    def _abort(self):
        """
        This is called when an ABORT is received from the MTA.  It
        calls abort() and then _close()
        """
        self._qid = None
        self.abort()

    def _unknown(self , cmd , data):
        """
        Unknown command sent.  Call unknown() with (<cmdDict> , <data>)
        """
        if cmd is not None:
            md = dictFromCmd(cmd[2:])
        md = dictFromCmd(cmd[2:])
        return self.unknown(md , data)
    # }}}

    #
    # Message modification methods {{{
    # NOTE: These can ONLY be called from eob()
    #
    def addRcpt(self , rcpt , esmtpAdd=''):
        """
        This will tell the MTA to add a recipient to the email
        
        NOTE: This can ONLY be called in eob()
        """
        if esmtpAdd:
            if not SMFIF_ADDRCPT_PAR & self._opts & self._mtaopts:
                print 'Add recipient par called without the proper opts set'
                return
            req = '%s%s\0%s\0' % (SMFIR_ADDRCPT_PAR , rcpt , esmtpAdd)
            req = pack_uint32(len(req)) + req
        else:
            if not SMFIF_ADDRCPT & self._opts & self._mtaOpts:
                print 'Add recipient called without the proper opts set'
                return
            req = '%s%s\0' % (SMFIR_ADDRCPT , rcpt)
            req = pack_uint32(len(req)) + req
        self.send(req)

    def delRcpt(self , rcpt):
        """
        This will tell the MTA to delete a recipient from the email

        NOTE: This can ONLY be called in eob()
        NOTE: The recipient address must be EXACTLY the same as one
        of the addresses received in the rcpt() callback'
        """
        if not SMFIF_DELRCPT & self._opts & self._mtaOpts:
            print 'Delete recipient called without the proper opts set'
            return
        req = '%s%s\0' % (SMFIR_DELRCPT , rcpt)
        req = pack_uint32(len(req)) + req
        self.send(req)

    def replBody(self , body):
        """
        This will replace the body of the email with a new body
        
        NOTE: This can ONLY be called in eob()
        """
        if not SMFIF_CHGBODY & self._opts & self._mtaOpts:
            print 'Tried to change the body without setting the proper option'
            return
        req = '%s%s' % (SMFIR_REPLBODY , body)
        req = pack_uint32(len(req)) + req
        self.send(req)

    def addHeader(self , key , val):
        """
        This will add a header to the email in the form:
            key: val
        
        NOTE: This can ONLY be called in eob()
        """
        if not SMFIF_ADDHDRS & self._opts & self._mtaOpts:
            print 'Add header called without the proper opts set'
            return
        req = '%s%s\0%s\0' % (SMFIR_ADDHEADER , key.rstrip(':') , val)
        req = pack_uint32(len(req)) + req
        self.send(req)

    def chgHeader(self , key , val='' , index=1):
        """
        This will change a header in the email.  The "key" should be
        exactly what was received in header().  If "val" is empty (''),
        the header will be removed.  "index" refers to which header to
        remove in the case that there are multiple headers with the
        same "key" (Received: is one example)
        
        NOTE: This can ONLY be called in eob()
        """
        if not SMFIF_CHGHDRS & self._opts & self._mtaOpts:
            print 'Change headers called without the proper opts set'
            return
        req = '%s%s%s\0%s\0' % (SMFIR_CHGHEADER , pack_uint32(index) , 
                key.rstrip(':') , val)
        req = pack_uint32(len(req)) + req
        self.send(req)

    def quarantine(self , msg=''):
        """
        This tells the MTA to quarantine the message (put it in the HOLD
        queue in Postfix).
        
        NOTE: This can ONLY be called in eob()
        """
        if not SMFIF_QUARANTINE & self._opts & self._mtaOpts:
            print 'Quarantine called without the proper opts set'
            return
        req = '%s%s\0' % (SMFIR_QUARANTINE , msg)
        req = pack_uint32(len(req)) + req
        self.send(req)

    def setReply(self , rcode , xcode , msg):
        """
        Sets the reply that the MTA will use for this message.
        The "rcode" is the 3 digit code to use (ex. 554 or 250).
        The "xcode" is the xcode part of the reply (ex. 5.7.1 or 2.1.0).
        The "msg" is the text response.
        """
        msg = msg.replace('%' , '%%')
        req = '%s%s %s %s\0' % (SMFIR_REPLYCODE , rcode , xcode , msg)
        req = pack_uint32(len(req)) + req
        self.send(req)

    def chgFrom(self , frAddr , esmtpAdd=''):
        """
        This tells the MTA to change the from address, with optional
        ESMTP extensions
        
        NOTE: This can ONLY be called in eob()
        """
        if not SMFIF_CHGFROM & self._opts & self._mtaOpts:
            print 'Change from called without the proper opts set'
            return
        req = '%s%s\0%s\0' % (SMFIR_CHGFROM , frAddr , esmtpAdd)
        req = pack_uint32(len(req)) + req
        self.send(req)

    def skip(self):
        """
        This tells the MTA that we don't want any more of this type of
        callback.

        This option must be set as well

        THIS CAN ONLY BE CALLED FROM THE body() callback!!
        """
        if not SMFIP_SKIP & self.protos & self._mtaProtos:
            print 'Skip called without the proper opts set'
            return
        req = pack_uint32(1) + SMFIR_SKIP
        self.send(req)
    # }}}

    ###################
    # Info callbacks  {{{
    # Override these in a subclass
    ###################
    @noCallback
    def connect(self , hostname , family , ip , port , cmdDict): 
        """
        This gets the connection info:

        str:hostname    The reverse hostname of the connecting ip
        str:family      The IP family (L=unix , 4=ipv4 , 6=ipv6 , U=unknown)
        str:ip          The IP of the connecting client
        int:port        The port number of the connecting client
        dict:cmdDict    The raw dictionary of items sent by the MTA

        Override this in a subclass.
        """
        self.log('Connect from %s:%d (%s) with family: %s' % (ip , port ,
            hostname , family))
        return CONTINUE

    @noCallback
    def helo(self , heloname):
        """
        This gets the HELO string sent by the client

        str:heloname    What the client HELOed as

        Override this in a subclass.
        """
        self.log('HELO: %s' % heloname)
        return CONTINUE

    @noCallback
    def mailFrom(self , frAddr , cmdDict):
        """
        This gets the MAIL FROM envelope address

        str:frAddr      The envelope from address
        dict:cmdDict    The raw dictionary of items sent by the MTA

        Override this in a subclass.
        """
        self.log('MAIL: %s' % frAddr)
        return CONTINUE

    @noCallback
    def rcpt(self , recip , cmdDict):
        """
        This gets the RCPT TO envelope address

        str:recip       The envelope recipient address
        dict:cmdDict    The raw dictionary of items sent by the MTA

        Override this in a subclass.
        """
        self.log('RCPT: %s' % recip)
        return CONTINUE

    @noCallback
    def header(self , key , val , cmdDict):
        """
        This gets one header from the email at a time.  The "key" is the
        LHS of the header and the "val" is RHS.
        ex.: key="Subject" , val="The subject of my email"

        str:key         The header name
        str:val         The header value
        dict:cmdDict    The raw dictionary of items sent by the MTA

        Override this in a subclass.
        """
        self.log('%s: %s' % (key , val))
        return CONTINUE

    @noCallback
    def eoh(self , cmdDict):
        """
        This tells you when all the headers have been received

        dict:cmdDict    The raw dictionary of items sent by the MTA

        Override this in a subclass.
        """
        self.log('EOH')
        return CONTINUE

    @noCallback
    def data(self , cmdDict):
        """
        This is called when the client sends DATA

        dict:cmdDict    The raw dictionary of items sent by the MTA

        Override this in a subclass.
        """
        self.log('DATA')
        return CONTINUE

    @noCallback
    def body(self , chunk , cmdDict):
        """
        This gets a chunk of the body of the email from the MTA.
        This will be called many times for a large email
        
        str:chunk       A chunk of the email's body
        dict:cmdDict    The raw dictionary of items sent by the MTA

        Override this in a subclass.
        """
        self.log('Body chunk: %d' % len(chunk))
        return CONTINUE

    def eob(self , cmdDict):
        """
        This signals that the MTA has sent the entire body of the email.
        This is the callback where you can use modification methods,
        such as addHeader(), delRcpt(), etc.  If you return CONTINUE
        from this method, it will be the same as an returning ACCEPT.

        dict:cmdDict    The raw dictionary of items sent by the MTA

        Override this in a subclass.
        """
        self.log('Body finished')
        return CONTINUE

    def close(self):
        """
        Here, you can close any open resources.
        NOTE: this method is ALWAYS called when everything is complete.
        """
        self.log('Close called.  QID: %s' % self._qid)

    def abort(self):
        """
        This is called when an ABORT is received from the MTA.
        NOTE: Postfix will send an ABORT at the end of every message.
        """
        pass

    @noCallback
    def unknown(self , cmdDict , data):
        return CONTINUE
    # }}}
# }}}

# class AsyncFactory {{{
class AsyncFactory(object):
    # __init__() {{{
    def __init__(self , sockstr , protocol , opts=0 , listenq=50 , 
            sockChmod=0666):
        self.sock = None
        self.opts = opts
        self.protocol = protocol
        self.listenq = int(listenq)
        self.sockChmod = sockChmod
        self.sockStr = sockstr
        self.poll = select.poll()
        self.emask = select.POLLIN | select.POLLPRI
        self.regLock = threading.Lock()
        self.sockMap = {}
        self.protoMap = {}
        self._close = threading.Event()
    # }}}

    # runAccepts() {{{
    def runAccepts(self):
        while True:
            if self._close.isSet():
                break
            sock , addr = self.sock.accept()
            p = self.protocol(self.opts)
            p.transport = sock
            self.register(sock , p)
    # }}}
    
    # register() {{{
    def register(self , sock , proto):
        fileno = sock.fileno()
        self.regLock.acquire()
        self.sockMap[fileno] = sock
        self.protoMap[fileno] = proto
        self.poll.register(fileno , self.emask)
        self.regLock.release()
    # }}}

    # unregister() {{{
    def unregister(self , fileno):
        self.regLock.acquire()
        self.poll.unregister(fileno)
        del self.sockMap[fileno]
        del self.protoMap[fileno]
        self.regLock.release()
    # }}}

    # run() {{{
    def run(self):
        global DEFERRED_REG
        if self.sockStr.lower().startswith('inet:'):
            ip = self.sockStr[5:self.sockStr.rfind(':')]
            port = self.sockStr[self.sockStr.rfind(':')+1:]
            (family, socktype, proto, canonname, sockaddr)=socket.getaddrinfo(ip, None)[0]
            self.sock = socket.socket(family , socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((ip , int(port)))
        else:
            if os.path.exists(self.sockStr):
                os.unlink(self.sockStr)
            self.sock = socket.socket(socket.AF_UNIX , socket.SOCK_STREAM)
            self.sock.bind(self.sockStr)
            os.chmod(self.sockStr , self.sockChmod)
        self.sock.listen(self.listenq)
        t = threading.Thread(target=self.runAccepts)
        t.daemon = True
        t.start()
        while True:
            if self._close.isSet(): break
            # Check for, accept and register any new connections
            # Poll for waiting data
            try:
                l = self.poll.poll(1)
            except select.error:
                # This is usually just do to a HUP, just start the loop again
                continue
            for fd , ev in l:
                s = self.sockMap[fd]
                p = self.protoMap[fd]
                buf = ''
                try:
                    buf = s.recv(MILTER_CHUNK_SIZE)
                except socket.error:
                    # Close the connection on an error since buf == ''
                    pass
                if not buf:
                    s.close()
                    p.connectionLost()
                    self.unregister(fd)
                else:
                    try:
                        p.dataReceived(buf)
                    except Exception , e:
                        p.log('AN EXCEPTION OCCURED IN %s: %s' % (p.id , e))
                        if DEBUG:
                            traceback.print_exc()
                        print >> sys.stderr , 'AN EXCEPTION OCCURED IN ' \
                            '%s: %s' % (p.id , e)
                        p.connectionLost()
                        self.unregister(fd)
            # Check the deferreds
            toRem = []
            for d in DEFERRED_REG:
                if d.completed:
                    toRem.append(d)
                    if d.error:
                        d.callErrbacks()
                    else:
                        d.callCallbacks()
            # Remove finished deferreds
            for d in toRem:
                DEFERRED_REG.discard(d)
           
    # }}}

    # close() {{{
    def close(self):
        self._close.set()
        for i , s in self.sockMap.items():
            self.poll.unregister(i)
            s.close()
            del self.sockMap[i]
        for i , p in self.protoMap.items():
            p.connectionLost()
            del self.protoMap[i]
        self.sock.close()
    # }}}
# }}}

# class ThreadFactory {{{
class ThreadFactory(object):
    def __init__(self , sockstr , protocol , opts=0 , listenq=50 , 
            sockChmod=0666 , cSockTimeout=1200):
        self.sock = None
        self.opts = opts
        self.protocol = protocol
        self.listenq = int(listenq)
        self.sockChmod = sockChmod
        self.sockStr = sockstr
        self.cSockTimeout = cSockTimeout
        self._close = threading.Event()

    def _setupSock(self):
        if self.sockStr.lower().startswith('inet:'):
            junk , ip , port = self.sockStr.split(':')
            self.sock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((ip , int(port)))
        else:
            if os.path.exists(self.sockStr):
                os.unlink(self.sockStr)
            self.sock = socket.socket(socket.AF_UNIX , socket.SOCK_STREAM)
            self.sock.bind(self.sockStr)
            os.chmod(self.sockStr , self.sockChmod)
        self.sock.settimeout(3)
        self.sock.listen(self.listenq)

    def log(self , msg):
        """
        Override in subclass to implement logging
        """
        pass

    def run(self):
        self._setupSock()
        while True:
            if self._close.isSet():
                break
            try:
                sock , addr = self.sock.accept()
            except socket.timeout:
                debug('Accept socket timed out' , 4 , -1)
                continue
            except socket.error , e:
                emsg = 'ERROR IN ACCEPT(): %s' % e
                self.log(emsg)
                debug(emsg , 1 , -1)
                continue
            sock.settimeout(self.cSockTimeout)
            p = self.protocol(self.opts)
            p.transport = sock
            p.daemon = True
            try:
                p.start()
            except Exception , e:
                emsg = 'An error occured starting the thread for ' + \
                    'connect from: %r: %s' % (addr , e)
                self.log(emsg)
                debug(emsg , 1 , -1)
                p.transport = None
                sock.close()
    
    def close(self):
        self._close.set()
        self.sock.close()

# }}}

# class ForkFactory {{{
class ForkFactory(object):
    def __init__(self , sockstr , protocol , opts=0 , listenq=50 , 
            sockChmod=0666 , cSockTimeout=300):
        self.sock = None
        self.opts = opts
        self.protocol = protocol
        self.listenq = int(listenq)
        self.sockChmod = sockChmod
        self.sockStr = sockstr
        self.cSockTimeout = cSockTimeout
        self._close = threading.Event()
        t = threading.Thread(target=self._handleChildren)
        t.daemon = True
        t.start()

    def _handleChildren(self):
        while not self._close.isSet():
            try:
                os.wait()
            except:
                time.sleep(0.5)

    def _setupSock(self):
        if self.sockStr.lower().startswith('inet:'):
            junk , ip , port = self.sockStr.split(':')
            self.sock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((ip , int(port)))
        else:
            if os.path.exists(self.sockStr):
                os.unlink(self.sockStr)
            self.sock = socket.socket(socket.AF_UNIX , socket.SOCK_STREAM)
            self.sock.bind(self.sockStr)
            os.chmod(self.sockStr , self.sockChmod)
        self.sock.settimeout(3)
        self.sock.listen(self.listenq)

    def log(self , msg):
        """
        Override in subclass to implement logging
        """
        pass

    def run(self):
        self._setupSock()
        while True:
            if self._close.isSet():
                break
            try:
                sock , addr = self.sock.accept()
            except socket.timeout:
                debug('Accept socket timed out' , 4 , -1)
                continue
            except socket.error , e:
                emsg = 'ERROR IN ACCEPT(): %s' % e
                self.log(emsg)
                debug(emsg , 1 , -1)
                continue
            sock.settimeout(self.cSockTimeout)
            p = self.protocol(self.opts)
            p.transport = sock
            try:
                p.start()
            except Exception , e:
                emsg = 'An error occured starting the thread for ' + \
                    'connect from: %r: %s' % (addr , e)
                self.log(emsg)
                debug(emsg , 1 , -1)
                p.transport = None
                sock.close()
    
    def close(self):
        self._close.set()
        self.sock.close()

# }}}

# def test() {{{
def test():
    import signal
    t = AsyncFactory('inet:127.0.0.1:5000' , MilterProtocol)
    def sigHandler(num , frame):
        t.close()
        sys.exit(0)
    signal.signal(signal.SIGINT , sigHandler)
    t.run()
# }}}

if __name__ == '__main__':
    # Test it
    test()
