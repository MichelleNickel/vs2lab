import random
import logging
from enum import Enum

import stablelog

# coordinator messages
from const3PC import PREPARE_COMMIT, READY_COMMIT, VOTE_REQUEST, GLOBAL_COMMIT, GLOBAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT
# misc constants
from const3PC import TIMEOUT

class State(Enum):
    INIT = "INIT"
    WAIT = "WAIT"
    PRECOMMIT = "PRECOMMIT"
    ABORT = "ABORT"
    COMMIT = "COMMIT"

class Coordinator:
    """
    Implements a two phase commit coordinator.
    - state written to stable log (but recovery is not considered)
    - simulates possible crash failure after vote request
    """

    def __init__(self, chan):
        self.channel = chan
        self.coordinator = self.channel.join('coordinator')
        self.participants = []  # list of all participants
        self.log = stablelog.create_log("coordinator-" + self.coordinator)
        self.stable_log = stablelog.create_log("coordinator-"
                                               + self.coordinator)
        self.logger = logging.getLogger("vs2lab.lab6.2pc.Coordinator")
        self.state: State = None

    def _enter_state(self, state: State):
        self.stable_log.info(state)  # Write to recoverable persistant log file
        self.logger.info("Coordinator {} entered state {}."
                         .format(self.coordinator, state))
        self.state = state

    def init(self):
        self.channel.bind(self.coordinator)
        self._enter_state(State.INIT)  # Start in INIT state.

        # Prepare participant information.
        self.participants = self.channel.subgroup('participant')

    def run(self):
        #if random.random() > 3/4:  # simulate a crash
        #    return "Coordinator crashed in state INIT."

        # Request local votes from all participants
        self._enter_state(State.WAIT)
        self.channel.send_to(self.participants, VOTE_REQUEST)

        #if random.random() > 2/3:  # simulate a crash
        #    return "Coordinator crashed in state WAIT."

        # Collect votes from all participants
        yet_to_receive = list(self.participants)
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(self.participants, TIMEOUT)

            if (not msg) or (msg[1] == VOTE_ABORT):
                reason = "timeout" if not msg else "local_abort from " + msg[0]
                self._enter_state(State.ABORT)
                # Inform all participants about global abort
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return "Coordinator {} terminated in state ABORT. Reason: {}."\
                    .format(self.coordinator, reason)

            else:
                assert msg[1] == VOTE_COMMIT
                yet_to_receive.remove(msg[0])


        self._enter_state(State.PRECOMMIT)
        self.channel.send_to(self.participants, PREPARE_COMMIT)

        yet_to_receive = list(self.participants)
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(self.participants, TIMEOUT)

            if msg and msg[1] != READY_COMMIT:
                reason = "local_abort from " + msg[0]
                self._enter_state(State.ABORT)
                # Inform all participants about global abort
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return "Coordinator {} terminated in state ABORT. Reason: {}."\
                    .format(self.coordinator, reason)

            elif msg:
                yet_to_receive.remove(msg[0])
            else:
                break

        self._enter_state(State.COMMIT)
        self.channel.send_to(self.participants, GLOBAL_COMMIT)

        return "Coordinator {} terminated in state COMMIT."\
            .format(self.coordinator)
