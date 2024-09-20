import pandas as pd

matrix = [
    [
        62307.6923076923,
        -15000,
        -23076.9230769231,
        7500,
        -8076.92307692307,
        7500,
        0,
        -7500,
        -22500,
    ],
    [
        -15000,
        62307.6923076923,
        7500,
        -8076.92307692307,
        7500,
        -23076.9230769231,
        -7500,
        0,
        -22500,
    ],
    [
        -23076.9230769231,
        7500,
        31153.8461538461,
        -7500,
        0,
        0,
        -4038.46153846154,
        3461.53846153846,
        -1730.76923076923,
    ],
    [
        7500,
        -8076.92307692307,
        -7500,
        31153.8461538461,
        0,
        0,
        4038.46153846154,
        -11538.4615384615,
        -22500,
    ],
    [
        -8076.92307692307,
        7500,
        0,
        0,
        31153.8461538461,
        -7500,
        -11538.4615384615,
        4038.46153846154,
        -22500,
    ],
    [
        7500,
        -23076.9230769231,
        0,
        0,
        -7500,
        31153.8461538461,
        3461.53846153846,
        -4038.46153846154,
        -1730.76923076923,
    ],
    [
        0,
        -7500,
        -4038.46153846154,
        4038.46153846154,
        -11538.4615384615,
        3461.0,
        53846153846,
        15576.9230769231,
        46730.7692307692,
    ],
    [
        -7500,
        0,
        3461.53846153846,
        -11538.4615384615,
        4038.46153846154,
        -4038.46153846154,
        0,
        15576.9230769231,
        46730.7692307692,
    ],
]

# matrix_df = pd.Dataframe(matrix)
# print(matrix_df.head())
# matrix_df.drop()


def eliminate(matrix, column):
    top_row = matrix[column]
    # base_value = top_row[column - 1]
    for row in range(column + 1, len(matrix)):
        if matrix[row][column] != 0:
            multi = matrix[row][column] / top_row[column]
            print(multi)
            top_row_temp = [value * multi for value in top_row]
            for ii in range(0, len(matrix[row])):
                new_value = matrix[row][ii] - top_row_temp[ii]
                matrix[row][ii] = round(new_value, 6)

    return matrix


def solve(matix, results):
    result = matrix[-1][1] / matrix[-1][-2]
    results.append(result)
    return matrix, results


for i in range(0, len(matrix)):
    matrix = eliminate(matrix, i)

for row in matrix:
    print(row)
