import itertools
import random

def augment_team_swap(X, y):
    """Takes in a set of match data and result of said match and returns the same data in a tuple,
    but it adds a new mirror match, where blue and red are swapped and the match result is reversed"""
    augmented_X = []
    augmented_y = []
    for match, result in zip(X, y):
        augmented_X.append(match)
        augmented_y.append(result)

        mid = len(match) // 2
        augmented_X.append(match[mid:] + match[:mid])
        augmented_y.append(-result)
    
    return (augmented_X, augmented_y)

def augment_player_swap(X, y, permutations: int = 6, portion: float = 1.0):
    """
    Augments match data by generating additional training samples through
    random permutations of player order within each team.

    Parameters
    ----------
    X : list[list]
        Feature matrix where each row represents a match.
        Each match contains players grouped sequentially by team.

    y : list[int]
        Match results (e.g., 1 for blue win, -1 for red win).

    permutations : int, optional (default=6)
        Number of random player-order permutations to generate per match.

    portion : float, optional (default=1.0)
        Fraction of dataset to apply augmentation to.
        1.0 = augment all matches, 0.5 = half, etc.

    Returns
    -------
    tuple (augmented_X, augmented_y)
        Augmented dataset including original and permuted versions.
    """
    if portion <= 0 or portion > 1:
        raise ValueError("Value of 'portion' requires a value in range (0.0; 1.0].")
    if permutations < 0 or permutations > 6:
        raise ValueError("Value of 'portion' requires an integer value in range [1; 6].")

    augmented_X = []
    augmented_y = []

    cutoff = int(len(X) * portion)
    for match, result in zip(X[:cutoff], y[:cutoff]):
        data_per_player = len(match) // 6

        # Split the data into a list of 6 lists, where each list contains the info of 1 player
        data = [
            match[i * data_per_player : (i + 1) * data_per_player]
            for i in range(6)
            ]
        
        blue = data[:3]
        red = data[3:]

        blue_perms = list(itertools.permutations(blue))
        red_perms = list(itertools.permutations(red))

        # Unsplit those lists containing the player info
        cleaned_perms = []
        for perm in blue_perms:
            cleaned_perm = []
            for player_data in perm:
                cleaned_perm.extend(player_data)
            cleaned_perms.append(tuple(cleaned_perm))

        blue_perms = cleaned_perms

        cleaned_perms = []
        for perm in red_perms:
            cleaned_perm = []
            for player_data in perm:
                cleaned_perm.extend(player_data)
            cleaned_perms.append(tuple(cleaned_perm))
        
        red_perms = cleaned_perms


        permuted_matches = []
        for blue_perm in blue_perms:
            for red_perm in red_perms:
                permuted_matches.append(list(blue_perm + red_perm))
        
        augmented_X.extend(random.sample(permuted_matches, permutations))
        for i in range(permutations):
            augmented_y.append(result)

    return (augmented_X, augmented_y)


def test_augment_team_swap():
    # One fake match:
    # Blue team: A B C
    # Red team:  D E F
    X = [
        [
            "DOUG", 100, 10, 5000,
            "RICO", 200, 20, 6000,
            "STU", 300, 30, 7000,

            "BULL", 400, 40, 8000,
            "EMZ", 500, 50, 9000,
            "COLT", 600, 60, 10000
        ]
    ]

    # Blue won
    y = [1]

    augmented_X, augmented_y = augment_team_swap(X, y)

    # Check size doubled
    assert len(augmented_X) == 2
    assert len(augmented_y) == 2

    # Original match unchanged
    assert augmented_X[0] == X[0]
    assert augmented_y[0] == 1

    # Check swapped match
    mid = len(X[0]) // 2

    expected_swapped = X[0][mid:] + X[0][:mid]

    assert augmented_X[1] == expected_swapped

    # Check winner flipped
    assert augmented_y[1] == -1

    # Check whole data is correct
    assert augmented_X == [
        [
            "DOUG", 100, 10, 5000,
            "RICO", 200, 20, 6000,
            "STU", 300, 30, 7000,

            "BULL", 400, 40, 8000,
            "EMZ", 500, 50, 9000,
            "COLT", 600, 60, 10000
        ],
        [
            "BULL", 400, 40, 8000,
            "EMZ", 500, 50, 9000,
            "COLT", 600, 60, 10000,

            "DOUG", 100, 10, 5000,
            "RICO", 200, 20, 6000,
            "STU", 300, 30, 7000,
        ]
    ]

    assert augmented_y == [1, -1]

    print("All tests passed!")

def test_augment_player_swap():
    random.seed(42)  # makes sampling deterministic

    X = [[
        "A1", 1,
        "A2", 2,
        "A3", 3,
        "B1", 4,
        "B2", 5,
        "B3", 6
    ]]

    y = [1]

    augmented_X, augmented_y = augment_player_swap(
        X,
        y,
        permutations=3,
        portion=1.0
    )

    # Correct number of outputs
    assert len(augmented_X) == 3
    assert len(augmented_y) == 3

    # All labels identical
    assert augmented_y == [1, 1, 1]

    # Each match still has same structure (6 players × 2 features = 12 values)
    for match in augmented_X:
        assert len(match) == 12

    # Ensure all original values still exist in at least one output
    flat_original = set(X[0])
    flat_augmented = set()
    for match in augmented_X:
        flat_augmented.update(match)

    assert flat_original == flat_augmented

    print(X)
    print(augmented_X)

    print("All tests passed!")

if __name__ == "__main__":
    test_augment_team_swap()
    test_augment_player_swap()