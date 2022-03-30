import random
import constant as const
import re

class Bot:
    """Bot class to create appropriate answer"""
    responses = None
    previous_state = None
    state = None
    information_factor = 0

    def __init__(self, responses):
        self.responses = responses

    def increment_information(self, increment):
        """
        Increments the information factor
        :param increment: number to increment factor by
        """
        self.information_factor += increment

    def calculate_response(self, user_message, keywords, persons, movies):
        """Calculates the answer the bot should type"""
        should_end = False
        answers = []
        user_message = " ".join(user_message)
        user_data = {*keywords, *persons, *movies}
        future_state = ""
        for state in self.responses['states']:
            # If we don't understand the input
            if state['name'] == 'not_understand':
                answers = state['answers']
                future_state = state
                break
            elif state['name'] == 'got_info':
                if len(user_data) > 0:
                    answers = state['answers']
                    future_state = state
                    break
                else:
                    continue

            # Search in possible answers
            for trigger in state['trigger']:
                if re.match(trigger, user_message.lower()):
                    answers = state['answers']
                    future_state = state

                    state_name = state['name']
                    if state_name == 'recommend':
                        if self.information_factor > const.INFORMATION_THRESHOLD_LOW:
                            answers = state['answers']['ok']
                            should_end = True
                        else:
                            answers = state['answers']['few']
            if answers:
                break

        self.previous_state = self.state
        self.state = future_state
        answer = random.choice(answers)
        if "concat" in self.state:
            if random.randrange(0, 99) < self.state['concat_chance']:
                answer += random.choice(self.state['concat'])

        answer = self.complement_message(answer, user_data)
        return answer, should_end

    @staticmethod
    def complement_message(answer, user_data):
        if const.ANY_FIELD in answer:
            # Stubstitute ANY_FIELD with a piece fo data from the user
            return answer.replace(const.ANY_FIELD, random.choice(list(user_data)))
        else:
            return answer
