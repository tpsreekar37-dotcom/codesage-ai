def process_data(user_input):
    # Smell: eval usage & unused variable
    unused_var = 42
    eval(user_input)
    for i in range(10):
        for j in range(10):
            # Nested loops
            print(i, j)
    api_key = "AIzaSyFakeKey123" # Hardcoded secret
