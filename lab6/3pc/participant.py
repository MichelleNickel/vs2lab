import random
import logging
from enum import Enum

# coordinator messages
from const3PC import PREPARE_COMMIT, READY_COMMIT, VOTE_REQUEST, GLOBAL_COMMIT, GLOBAL_ABORT
# participant decissions
from const3PC import LOCAL_SUCCESS, LOCAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT, NEED_DECISION
# misc constants
from const3PC import TIMEOUT

import stablelog


class State(Enum):
    INIT = "INIT"
    READY = "READY"
    PRECOMMIT = "PRECOMMIT"
    ABORT = "ABORT"
    COMMIT = "COMMIT"

class Participant:
    """
    Implements a two phase commit participant.
    - state written to stable log (but recovery is not considered)
    - in case of coordinator crash, participants mutually synchronize states
    - system blocks if all participants vote commit and coordinator crashes
    - allows for partially synchronous behavior with fail-noisy crashes
    """

    def __init__(self, chan):
        self.channel = chan
        self.participant = self.channel.join('participant')
        self.stable_log = stablelog.create_log(
            "participant-" + self.participant)
        self.logger = logging.getLogger("vs2lab.lab6.2pc.Participant")
        self.coordinator = {}
        self.all_participants = {}
        self.state: State = None

    @staticmethod
    def _do_work():
        # Simulate local activities that may succeed or not
        return LOCAL_SUCCESS
        #return LOCAL_ABORT if random.random() > 2/3 else LOCAL_SUCCESS

    def _enter_state(self, state: State):
        self.stable_log.info(state)  # Write to recoverable persistant log file
        self.logger.info("Participant {} entered state {}."
                         .format(self.participant, state))
        self.state = state

    def init(self):
        self.channel.bind(self.participant)
        self.coordinator = self.channel.subgroup('coordinator')
        self.all_participants = self.channel.subgroup('participant')
        self._enter_state(State.INIT)  # Start in local INIT state.
            
    def run(self):
        if random.random() > 3/4:  # simulate a crash
            return f"Participant {self.participant} crashed in state {self.state}."

        # Wait for start of joint commit
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg:  # Crashed coordinator - give up entirely
            # decide to locally abort (before doing anything)
            decision = LOCAL_ABORT

        else:  # Coordinator requested to vote, joint commit starts
            assert msg[1] == VOTE_REQUEST

            # Firstly, come to a local decision
            decision = self._do_work()  # proceed with local activities

            # If local decision is negative,
            # then vote for abort and quit directly
            if decision == LOCAL_ABORT:
                self.channel.send_to(self.coordinator, VOTE_ABORT)

            # If local decision is positive,
            # we are ready to proceed the joint commit
            else:
                assert decision == LOCAL_SUCCESS
                self._enter_state(State.READY)

                # Notify coordinator about local commit vote
                self.channel.send_to(self.coordinator, VOTE_COMMIT)

                # Wait for coordinator to notify the final outcome
                msg = self.channel.receive_from(self.coordinator, TIMEOUT)

                if not msg:  # Crashed coordinator
                    # Ask all processes for their decisions
                    self.channel.send_to(self.all_participants, NEED_DECISION)
                    while True:
                        msg = self.channel.receive_from_any()
                        # If someone reports a final decision,
                        # we locally adjust to it
                        if msg[1] in [
                                GLOBAL_COMMIT, GLOBAL_ABORT, LOCAL_ABORT]:
                            decision = msg[1]
                            break

                else:  # Coordinator came to a decision
                    decision = msg[1]

        # Change local state based on the outcome of the joint commit protocol
        # Note: If the protocol has blocked due to coordinator crash,
        # we will never reach this point

        if decision == PREPARE_COMMIT:
            self._enter_state(State.PRECOMMIT)

            if random.random() > 3/4:  # simulate a crash
                return f"Participant {self.participant} crashed in state {self.state}."

            self.channel.send_to(self.coordinator, READY_COMMIT)

            msg = self.channel.receive_from(self.coordinator, TIMEOUT)

            if not msg:  # Crashed coordinator
                # Ask all processes for their decisions
                self.channel.send_to(self.all_participants, NEED_DECISION)
                while True:
                    msg = self.channel.receive_from_any()
                    # If someone reports a final decision,
                    # we locally adjust to it
                    if msg[1] in [
                            GLOBAL_COMMIT, GLOBAL_ABORT, LOCAL_ABORT]:
                        decision = msg[1]
                        break

            else:  # Coordinator came to a decision
                decision = msg[1]


        if decision == GLOBAL_COMMIT:
            self._enter_state(State.COMMIT)
        else:
            assert decision in [GLOBAL_ABORT, LOCAL_ABORT]
            self._enter_state(State.ABORT)

        # Help any other participant when coordinator crashed
        num_of_others = len(self.all_participants) - 1
        while num_of_others > 0:
            num_of_others -= 1
            msg = self.channel.receive_from(self.all_participants, TIMEOUT * 2)
            if msg and msg[1] == NEED_DECISION:
                self.channel.send_to({msg[0]}, decision)

        return "Participant {} terminated in state {} due to {}.".format(
            self.participant, self.state, decision)
