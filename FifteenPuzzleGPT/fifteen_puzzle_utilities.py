# Utilities to operate on 4x4 Rubik's cube and to address representation of cube state and action/permutation.
# For representation details, see "CubeGPT/README.md".

# Utilities to operate on 3x3 Rubik's cube and to address representation of cube state and action/permutation.
# For representation details, see "CubeGPT/README.md".

# uses names with cube so as to allow train_15 to just be a copy paste of train cube.

import random
from math import ceil, log10
size = 4
action_space = ["l", "r", "d", "u", "DONE"]
action_space_strict = ["l", "r", "d", "u"]
action_dict = {
    "l": (0, 1),
    "r": (0, -1),
    "u": (1, 0),
    "d": (-1, 0)
}


empty_space_char = 0
color_repr_separator = " "


# def internal_to_external(state):
def internal_to_color(state):
    """
    Input: (list[list[int]]) state as nested lists
    Output: (str) state as string (concatenated, with color_repr_separator separators) , with the 0 replaced by x)
    """
    lines = []
    for row in state:
        ind = -1
        if 0 in row:
            ind = row.index(0)
            row[ind] = empty_space_char
        line = color_repr_separator.join(row)
        if ind != -1:
            row[ind] = 0

    return color_repr_separator.join(lines)

# def external_to_internal(state):


def color_to_internal(state):
    """
    Input: (str) state as string (concatenated, with "," separators) , with the 0 replaced by x)
    Output: (list[list[int]]) state as nested lists
    """
    state = state.split(",")
    puzzle = []
    for i in range(size):
        row = []
        for j in range(size):
            cell = state[i*size + j]
            if cell == empty_space_char:
                cell = 0
            row.append(cell)
        puzzle.append(row)
    return puzzle


def internal_cube_permute(starting_state: list, moves: str):
    """
    - Assuming internal representation of puzzle state (added for convenience)
    - Input:
        - An starting state to start from.
        - A sequence of moves (no separator)
    - Output:
        - An arrived final state.
    """
    starting_state = [row.copy() for row in starting_state]
    empty_r, empty_c = -2, -2
    size = len(starting_state)
    for i in range(size):
        if 0 in starting_state[i]:
            empty_r = i
            empty_c = starting_state[i].index(0)
            break

    for i in range(len(moves)):
        action = moves[i]
        move_r, move_c = action_dict[action]
        new_r, new_c = empty_r + move_r, empty_c + move_c
        if 0 <= new_r < size and 0 <= new_c < size:
            starting_state[empty_r][empty_c] = starting_state[new_r][new_c]
            starting_state[new_r][new_c] = 0
            empty_r, empty_c = new_r, new_c

    return starting_state


def cube_permute(starting_state: str, moves: str):
    """
    - Assuming color representation of puzzle state
    - Input:
        - An starting state to start from.
        - A sequence of moves (no separator)
    - Output:
        - An arrived final state.
    """
    state = color_to_internal(starting_state)
    permuted_state = internal_cube_permute(state, moves)
    return internal_to_color(permuted_state)


def init_state(repr: str):
    state = [[i*size+j for j in range(size)] for i in range(size)]
    if repr == 'color_repr':
        return internal_to_color(state)
    return state


def is_done(state):
    """
    - Input: (str) A state in the internal representation that
    - Output: (bool) Whether it is the end state
    """
    size = len(state)
    return all(state[i][j] == i*size+j for i in range(size) for j in range(size))


def challenge_generator(n: int, repr_mode: str):
    """
    - Input:
        - Number of moves to permute.
        - Representation mode (color repr or internal repr).
        - Whether starting state is random or not. Otherwise, start from initial state.
    - Output:
        - A (internal or color representation) sequence of states and actions, where randomness from actions.
    """
    curr_state = init_state('internal_repr')  # Keep this as color_repr

    actions_for_record = random.choices(action_space_strict, k=n)
    record = [""] * (2 * n + 1)
    record[0] = curr_state
    for i in range(n):
        record[2 * i + 1] = actions_for_record[i]
        record[2 * i +
               2] = internal_cube_permute(record[2 * i], [actions_for_record[i]])

    # Reverse
    empty_r, empty_c = 0, 0
    size = len(record[0])
    inverse_actions = {"l": "r", "r": "l", "u": "d", "d": "u"}

    for i in range(n):  # Invert actions in list.
        action = record[2 * i + 1]
        move_r, move_c = action_dict[record[2 * i + 1]]
        if 0 <= empty_r + move_r < size and 0 <= empty_c + move_c < size:
            # if this doesn't hold, then action did notihng
            # so before and after state are same and inverse action is the original action
            record[2 * i + 1] = inverse_actions[action]

    record.reverse()

    # convert representation
    for i in range(n):
        record[2 * i + 1] = " " + record[2 * i + 1] + " "

    if repr_mode == "internal_repr":
        for i in range(n+1):
            state = record[2*i]
            record[2*i] = "I_SB " + \
                " ".join([str(cell)
                         for row in state for cell in row]) + " I_SE"
    elif repr_mode == "color_repr":
        for i in range(n+1):
            record[2 * i] = "I_SB " + \
                internal_to_color(record[2 * i]) + " I_SE"

    return record


def cube_visualize(state: str):
    state = color_to_internal(state)
    size = len(state)
    width = ceil(log10(size*size))
    char_sep = " | "
    line_sep_char = "-"

    line_width = width*size + \
        len(char_sep)*size + len(char_sep.strip())
    line_width = ceil(line_width / (len(line_sep_char)))
    line_sep = line_sep_char * line_width

    lines = [line_sep]
    for row in state:
        line = char_sep.join(
            [str(cell if cell != 0 else empty_space_char).ljust(width) for cell in row])
        line = char_sep + line + char_sep
        line = line.strip()
        lines.append(line, line_sep)
    print('\n'.join(lines))


def challenge_format(challenge: list[str]):
    """
    To put a challenge into the format for writing to training file.
    """
    return " " + "".join(challenge) + " " + "DONE" + " " + "\n"


def puzzle_generate_training_file(num_examples: int, num_permute: int):
    """
    - num_examples: How many problem-solutions to generate.
    - seq_len: One file contains same action length solution.
    """
    with open("./data/puzzle_structure/input.txt", "a") as file:
        file.truncate(0)
        for _ in range(num_examples):
            # Insert strings backwards so to not mess up with indexing.
            challenge = challenge_generator(num_permute, "internal_repr")
            formatted_challenge = challenge_format(challenge)
            file.write(formatted_challenge)


if __name__ == "__main__":
    puzzle_generate_training_file(500, 50)
