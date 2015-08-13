from netzob.Common.Models.Grammar.Transitions.Transition import Transition
from netzob.Common.Models.Simulator.AbstractionLayer import AbstractionLayer
from netzob.Common.Models.Vocabulary.Messages.RawMessage import RawMessage
from netzob.Common.Utils.Decorators import typeCheck, NetzobLogger

import uuid
import random
import time
import copy


@NetzobLogger
class PrismaTransition(Transition):

    TYPE = "PrismaTransition"

    def __init__(self, startState, endState, inputSymbol=None, outputSymbols=[], _id=uuid.uuid4(), name=None):
        super(PrismaTransition, self).__init__(startState, endState, inputSymbol, outputSymbols, _id, name)
        # uniqSym = []
        # for s in self.outputSymbols:
        #     uniqSym.append(copy.copy(s))
        self.emitted = []
        self.invalid = False
        self.active = False
        if 'UAC' in startState.name.split('|')[-1]:
            self.ROLE = 'client'
        else:
            self.ROLE = 'server'

    @typeCheck(AbstractionLayer)
    def executeAsInitiator(self, abstractionLayer):
        try:
            if len(abstractionLayer.sesSta[-1]) > 29 and len(set(abstractionLayer.sesSta[-1][-10:])) < 7:  # len shortest cycle in graph..
                # maybe we are cycling?
                abstractionLayer.sesSta.append([])
                abstractionLayer.sesSym.append([])
                return 'cycle'
        except Exception:
            print 'what the hell'
            exit()
        if abstractionLayer is None:
            raise TypeError("Abstraction layer cannot be None")

        if self.startState.name.split('|')[-1] == 'START':
            abstractionLayer.sesSta[-1].append(self.endState.name)
            return self.endState

        if not self.outputSymbols:
            abstractionLayer.sesSta[-1].append(self.endState.name)
            return self.endState

        self.active = True
        # manage outputStates
        if self.ROLE == 'client':
            pickedSymbol = self.__pickOutputSymbol()

            if pickedSymbol is None:
                self._logger.debug("Something is wrong here. Got outState without outSymbol..")
                abstractionLayer.sesSta[-1].append(self.endState.name)
                return self.endState

            # Emit the symbol
            abstractionLayer.writeSymbol(pickedSymbol)
            # we gonna sleep here for a while..
            time.sleep(0.1)

            # Return the endState
            self.active = False
            abstractionLayer.sesSta[-1].append(self.endState.name)
            return self.endState
        # handle inputStates
        else:
            self._logger.info("Expecting Symbol(s): {}".format(map(lambda x: x.name, self.outputSymbols)))
            # Waits for the reception of a symbol
            (receivedSymbol, receivedMessage) = abstractionLayer.readSymbol()
            # we gonna sleep here for a while..
            time.sleep(0.1)

            # hopefully we did a good job at learning
            if receivedSymbol in self.outputSymbols:
                self.active = False
                receivedSymbol.messages = [RawMessage(receivedMessage)]
                abstractionLayer.sesSta[-1].append(self.endState.name)
                return self.endState
            # hopefully we then did a semi-good job at learning
            elif receivedSymbol in abstractionLayer.symbols:
                self.active = False
                self._logger.warning("Received symbol No.{} was not excepted. Try to keep session going..".format(
                    receivedSymbol.name))
                abstractionLayer.sesSta[-1].append(self.endState.name)
                return self.endState
            # unfortunately we did not at all
            else:
                self.active = False
                self._logger.warning("Received Symbol entire unknown; still trying to go on")
                abstractionLayer.sesSta[-1].append(self.endState.name)
                return self.endState

    def __pickOutputSymbol(self):
        # if len(self.outputSymbols) == 1:
        #     return self.outputSymbols[0]
        self._logger.info("picking symbol")
        pos = list(set(self.outputSymbols)-set(self.emitted))
        c = random.choice(pos)
        # kill too faulty Symbols
        if (c.faulty >= 9 and c.faulty*1.0/c.emitted > 0.75) or (c.emitted >= 29 and c.faulty*1.0/c.emitted > 0.05):
            self._logger.critical("picked symbol{} too faulty".format(c.name))
            if c in self.outputSymbols:
                self.outputSymbols.remove(c)
            # no emitable Symbols left? -> invalidate transition
            if len(self.outputSymbols) == 0:
                self._logger.critical("invalidating trans")
                self.invalid = True
        self.emitted.append(c)
        if len(self.emitted) >= len(self.outputSymbols):
            self.emitted = []
        return c
