#!/usr/bin/env python

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

#
# This is a basic milter for testing
#

import libmilter as lm
import sys , time

#
# We are going to use an example of a forking version of our milter.  This is
# something not even possible with a regular libmilter implementation
#

# Create our milter class with the forking mixin and the regular milter
# protocol base classes
class TestMilter(lm.ForkMixin , lm.MilterProtocol):
    def __init__(self , opts=0 , protos=0):
        # We must init our parents here
        lm.MilterProtocol.__init__(self , opts , protos)
        lm.ForkMixin.__init__(self)
        # You can initialize more stuff here

    def log(self , msg):
        t = time.strftime('%H:%M:%S')
        print '[%s] %s' % (t , msg)
        sys.stdout.flush()

    @lm.noReply
    def connect(self , hostname , family , ip , port , cmdDict):
        self.log('Connect from %s:%d (%s) with family: %s' % (ip , port ,
            hostname , family))
        return lm.CONTINUE

    @lm.noReply
    def helo(self , heloname):
        self.log('HELO: %s' % heloname)
        return lm.CONTINUE

    @lm.noReply
    def mailFrom(self , frAddr , cmdDict):
        self.log('MAIL: %s' % frAddr)
        return lm.CONTINUE

    @lm.noReply
    def rcpt(self , recip , cmdDict):
        self.log('RCPT: %s' % recip)
        return lm.CONTINUE

    @lm.noReply
    def header(self , key , val , cmdDict):
        self.log('%s: %s' % (key , val))
        return lm.CONTINUE

    @lm.noReply
    def eoh(self , cmdDict):
        self.log('EOH')
        return lm.CONTINUE

    def data(self , cmdDict):
        self.log('DATA')
        return lm.CONTINUE

    @lm.noReply
    def body(self , chunk , cmdDict):
        self.log('Body chunk: %d' % len(chunk))
        return lm.CONTINUE

    def eob(self , cmdDict):
        self.log('EOB')
        #self.setReply('554' , '5.7.1' , 'Rejected because I said so')
        return lm.CONTINUE

    def close(self):
        self.log('Close called. QID: %s' % self._qid)

def runTestMilter():
    import signal , traceback
    # We can set our milter opts here
    opts = lm.SMFIF_CHGFROM | lm.SMFIF_ADDRCPT | lm.SMFIF_QUARANTINE

    # We initialize the factory we want to use (you can choose from an 
    # AsyncFactory, ForkFactory or ThreadFactory.  You must use the
    # appropriate mixin classes for your milter for Thread and Fork)
    f = lm.ForkFactory('inet:127.0.0.1:5000' , TestMilter , opts)
    def sigHandler(num , frame):
        f.close()
        sys.exit(0)
    signal.signal(signal.SIGINT , sigHandler)
    try:
        # run it
        f.run()
    except Exception , e:
        f.close()
        print >> sys.stderr , 'EXCEPTION OCCURED: %s' % e
        traceback.print_tb(sys.exc_traceback)
        sys.exit(3)

if __name__ == '__main__':
    runTestMilter()
