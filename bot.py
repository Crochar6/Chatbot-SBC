import random
import constant as const


class Bot:
    """Bot class to create appropriate answer"""
    responses = None
    previous_state = None
    state = None
    information_factor = 0

    def __init__(self, responses):
        self.responses = responses

    def calculate_response(self, user_message, keywords, persons, movies):
        """Calculates the answer the bot should type"""
        should_end = False
        answers = []
        user_message = " ".join(user_message)
        user_data = {*keywords, *persons, *movies}
        for state in self.responses['states']:
            # If we don't understand the input
            if state['name'] == 'not_understand':
                answers = state['answers']
                break
            elif state['name'] == 'got_info':
                if len(user_data) > 0:
                    answers = state['answers']
                    self.information_factor += len(user_data)
                    break
                else:
                    continue

            # Search in possible answers
            for trigger in state['trigger']:
                if trigger.lower() in user_message:
                    answers = state['answers']

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
        self.state = answers
        answer = random.choice(answers)
        answer = self.complement_message(answer, user_data)
        return answer, should_end

    @staticmethod
    def complement_message(answer, user_data):
        if const.ANY_FIELD in answer:
            # Stubstitute ANY_FIELD with a piece fo data from the user
            return answer.replace(const.ANY_FIELD, random.choice(list(user_data)))
