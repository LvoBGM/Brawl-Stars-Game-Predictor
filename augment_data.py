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

if __name__ == "__main__":
    test_augment_team_swap()