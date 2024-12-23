import random
import logging

import stablelog

# coordinator messages
from const3PC import PREPARE_COMMIT, READY_COMMIT, VOTE_REQUEST, GLOBAL_COMMIT, GLOBAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT
# misc constants
from const3PC import TIMEOUT

from const3PC import CoordinatorState

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
        self.state: CoordinatorState = None

    def _enter_state(self, state: CoordinatorState):
        self.stable_log.info(state)  # Write to recoverable persistant log file
        self.logger.info("Coordinator {} entered state {}."
                         .format(self.coordinator, state))
        self.state = state

    def init(self):
        self.channel.bind(self.coordinator)
        self._enter_state(CoordinatorState.INIT)  # Start in INIT state.

        # Prepare participant information.
        self.participants = self.channel.subgroup('participant')

    def run(self):
        allow_crash = True

        # Request local votes from all participants
        self._enter_state(CoordinatorState.WAIT)
        self.channel.send_to(self.participants, VOTE_REQUEST)

        if random.random() > 2/3 and allow_crash:  # simulate a crash
            return f"Coordinator {self.coordinator} crashed in state {self.state}."

        # Collect votes from all participants
        yet_to_receive = list(self.participants)
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(self.participants, TIMEOUT)

            if (not msg) or (msg[1] == VOTE_ABORT):
                reason = "timeout" if not msg else "local_abort from " + msg[0]
                self._enter_state(CoordinatorState.ABORT)
                # Inform all participants about global abort
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return "Coordinator {} terminated in state ABORT. Reason: {}."\
                    .format(self.coordinator, reason)

            else:
                assert msg[1] == VOTE_COMMIT
                yet_to_receive.remove(msg[0])


        self._enter_state(CoordinatorState.PRECOMMIT)
        self.channel.send_to(self.participants, PREPARE_COMMIT)

        if random.random() > 2/3 and allow_crash:  # simulate a crash
            return f"Coordinator {self.coordinator} crashed in state {self.state}."

        yet_to_receive = list(self.participants)
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(self.participants, TIMEOUT)

            if msg and msg[1] != READY_COMMIT:
                reason = "local_abort from " + msg[0]
                self._enter_state(CoordinatorState.ABORT)
                # Inform all participants about global abort
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return "Coordinator {} terminated in state ABORT. Reason: {}."\
                    .format(self.coordinator, reason)

            elif msg:
                yet_to_receive.remove(msg[0])
            else:
                break

        self._enter_state(CoordinatorState.COMMIT)
        self.channel.send_to(self.participants, GLOBAL_COMMIT)

        return "Coordinator {} terminated in state COMMIT."\
            .format(self.coordinator)
