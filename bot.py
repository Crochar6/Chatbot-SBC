import pandas as pd
import random


class Bot:
    """Bot class to create appropriate answer"""
    responses = None
    previous_state = None
    state = None

    def __init__(self, responses):
        self.responses = responses

    def calculate_response(self, user_message, genres, keywords, persons, movies):
        """Calculates the answer the bot should type"""
        next_state = None
        user_message = " ".join(user_message)
        for state in self.responses['states']:
            # If we don't understand the input
            if state['name'] == 'not_understand':
                next_state = state
                break

            # Search in possible answers
            for trigger in state['trigger']:
                if trigger.lower() in user_message:
                    next_state = state
            if next_state:
                break

        self.previous_state = self.state
        self.state = next_state
        return random.choice(next_state['answers'])
