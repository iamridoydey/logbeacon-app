from app.config import Config


def calculate_cost(input_tokens, output_tokens):
    """
    Calculate the price based on input_tokens and output_tokens.
    """
    total_tokens = input_tokens + output_tokens
    cost = (total_tokens / 1_000_000) * Config.PRICE_PER_MILLION_TOKENS
    return f"{cost:.6f}"