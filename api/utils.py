def generate_analysis_and_tips(user_input, context=None):
    """
    Stub — analysis and tips LLM calls have been removed to reduce latency.
    The answer is now generated in a single call inside retrieval.py.
    Returns empty strings immediately with zero network calls.
    """
    class MockGeneration:
        def __init__(self, text):
            self.text = text

    class MockGenerations:
        def __init__(self, text):
            self.generations = [[MockGeneration(text)]]

    return MockGenerations(""), MockGenerations("")
