def split_args(condition):
    open_parenthesis = 0
    comma_index = 0
    for i in range(len(condition) - 1, -1, -1):
        char = condition[i]
        if char == "(": open_parenthesis += 1
        elif char == ")": open_parenthesis -= 1
        if char == "," and open_parenthesis == 0:
            comma_index = i
            break

    return [condition[:comma_index], condition[comma_index + 2:]]


def clean_condition(condition):
    condition = condition[1:-1]
    operation, condition = condition.split(" ", 1)
    condition_parts = split_args(condition)
    for i, condition_part in enumerate(condition_parts):
        if "(" in condition_part and ")" in condition_part:
            condition_parts[i] = f"({clean_condition(condition_part)})"
        elif "#" in condition_part:
            condition_parts[i] = condition_part.split("#")[0]

    return f" {operation} ".join(condition_parts)