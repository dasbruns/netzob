__author__ = 'dsmp'

import os

import time
from socket import error as socket_error

from netzob.Import.PrismaImporter.PrismaImporter import PrismaImporter
from netzob.Common.Utils.Decorators import typeCheck, NetzobLogger
from netzob.Common.Models.Vocabulary.Messages.RawMessage import RawMessage

@NetzobLogger
class PrismaTest(object):
    def __init__(self):
        self.pi = PrismaImporter()

    def run(self, init=False):
        try:
            l = self.pi.getLayer()
            l.reInit()
            try:
                l.openChannel()
            except socket_error:
                try:
                    # maybe channel still blocked?
                    l.closeChannel()
                    time.sleep(.1)
                    l.openChannel()
                except socket_error:
                    # probably killed target -> restart it
                    print 'watch out, target may be gone?! Trying to restart..'
                    if not init:
                        self.pi.getLayer().sesSym[-1].append('CRASH')
                        self.pi.getLayer().sesSta[-1].append('CRASH')
                    time.sleep(11)
                    err = os.system("/home/dsmp/work/xbmc/bin/kodi &")
                    time.sleep(7.5)
                    # if err == 0:
                    #     return True
            s = self.pi.getInitial()
            sPre = None
            while sPre != s:
                sPre = s
                s = s.executeAsInitiator(l)
                if s =='cycle':
                    self._logger.critical('cycle detected')
                    time.sleep(0.3)
                    l.closeChannel()
                    return True
            l.closeChannel()
            time.sleep(1)
            return True
        # probably one cycle ended in the target not responding
        # causing an excaption to be thrown
        # causing us to catch it
        except Exception, e:
            return True

    def toast(self, count=0):
        self.fuzzyLearn(count)

    def fuzzyLearn(self, count=0):
        ret = True
        init = True
        self.pi.getLayer().reset()
        while ret:
            ret = self.run(init)
            init = False
            count += 1
            if not count % 100:
                self._logger.critical('=== {} === \r\n\r\n'.format(count))
                self.dot(count)
            # find good value here
            if count == 200000:
                ret = False

    def dot(self, count):
        try:
            os.makedirs('{}/graphs2'.format(self.pi.getPath()))
        except OSError:
            pass
        dot = self.pi.getAutomaton().generateDotCode()
        f = open('{}/graphs2/{}'.format(self.pi.getPath(), count), 'w')
        f.write(dot)
        f.close()
        return

    def test(self, dot=True, check=False):
        self.pi.setPath('/home/dsmp/work/pulsar/src/models/myPlay')
        self.pi.setDestinationIp('127.0.0.1')
        self.pi.setDestinationPort(36666)
        self.pi.setSourceIp('127.0.0.1')
        self.pi.setSourcePort(51337)

        print self.pi.isInitialized()
        # enhance maybe is a poor idea (at least at learning lvl)
        self.pi.create(enhance=False)
        # there seems to be a problem specializing some Symbols?
        if check:
            self._logger.info('testing generated Symbols')
            for sym in self.pi.Symbols.values():
                remake(sym)
        if dot:
            self.dot('initial')
        return


def remake(sym, rerun=False):
        if sym.role == 'client':
            try:
                sym.getCells()
                sym.specialize(noRules=True)
            except Exception:
                if rerun:
                    print 'deleting entire symbol {}'.format(sym.name)
                    # self._logger.error('problem with symbol No.{} --> removing it'.format(sym.name))
                else:
                    sym.messages = [RawMessage(sym.specialize())]
                    remake(sym, True)


