import pandas as pd

matrix = [
    [
        62307.6923076923,
        -15000,
        -23076.9230769231,
        7500,
        -8076.92307692307,
        7500,
        -22500,
    ],
    [
        -15000,
        62307.6923076923,
        7500,
        -8076.92307692307,
        7500,
        -23076.9230769231,
        -22500,
    ],
    [-23076.9230769231, 7500, 31153.8461538461, -7500, 0, 0, -1730.76923076923],
    [7500, -8076.92307692307, -7500, 31153.8461538461, 0, 0, -22500],
    [-8076.92307692307, 7500, 0, 0, 31153.8461538461, -7500, -22500],
    [7500, -23076.9230769231, 0, 0, -7500, 31153.8461538461, -1730.76923076923],
]

matrix_test = [[3, 4, 2, 45], [6, 2, 3, 59], [2, 7, 4, 66]]

matrix_k = [i[:-1] for i in matrix]
matrix_f = [i[-1] for i in matrix]

print(matrix_k)
print(matrix_f)


index = ["5u", "5v", "6u", "6v", "8u", "8v"]
# index = ["x1", "x2", "x3"]


matrix_k_df = pd.DataFrame(matrix_k, index=index, columns=index)
# print(matrix_k_df.head())
# test = matrix_k_df.iloc[0] * 2
# print(test.head())
# test_np = test.to_numpy()


# matrix_k_df.iloc[0] = matrix_k_df.iloc[0] - test
# print(matrix_k_df.head())


# print(test_np)
# print(test_np + 1)
# df[df["location"] == "c"].squeeze()
matrix_f_df = pd.Series(matrix_f, index=index)
# print(matrix_f_df.head())


def eliminate_df(stiffness, force, column):
    base_row = stiffness.iloc[column]
    # for index, row in stiffness.iterrows():
    for row in range(column + 1, len(stiffness)):
        # if row.iloc[column] != 0:
        if stiffness.iloc[row, column] != 0:
            # multi = row.iloc[column] / base_row.iloc[column]
            # print(stiffness.iloc[row, column], base_row.iloc[column])
            multi = stiffness.iloc[row, column] / base_row.iloc[column]
            # print("***", multi)
            base_row_temp = base_row * multi
            stiffness.iloc[row] = (stiffness.iloc[row] - base_row_temp).round(9)
            # print(force.iloc[row], force.iloc[column])
            force.iloc[row] = (force.iloc[row] - (force.iloc[column] * multi)).round(9)
            # print(force.iloc[row])

    return stiffness, force


def solve_unknowns(stiffness, force):
    disp = pd.Series(0, index=stiffness.index)
    print(stiffness.head)
    print(force.head)
    for row in range(len(disp) - 1, -1, -1):
        disp.iloc[row] = force.iloc[row] / stiffness.iloc[row, -1]
        stiffness.drop(stiffness.index[row], inplace=True)
        print("disp", disp.head())
        force.drop(force.index[row], inplace=True)
        for row_ in range(len(stiffness)):
            force.iloc[row_] = force.iloc[row_] - (
                stiffness.iloc[row_, -1] * disp.iloc[row]
            )
        stiffness.drop(stiffness.columns[row], axis=1, inplace=True)
        print(stiffness.head())
        print(force.head())
    return disp


def eliminate(matrix, column):
    top_row = matrix[column]
    for row in range(column + 1, len(matrix)):
        if matrix[row][column] != 0:
            multi = matrix[row][column] / top_row[column]
            top_row_temp = [value * multi for value in top_row]
            for ii in range(0, len(matrix[row])):
                new_value = matrix[row][ii] - top_row_temp[ii]
                matrix[row][ii] = round(new_value, 9)

    return matrix


def solve(matix, results):
    result = matrix[-1][1] / matrix[-1][-2]
    results.append(result)
    return matrix, results


# for i in range(0, len(matrix)):
#    matrix = eliminate(matrix, i)

# for row in matrix:
#    print(row)

for i in range(0, len(matrix_k_df)):
    matrix_k_df, matrix_f_df = eliminate_df(matrix_k_df, matrix_f_df, i)

# print(matrix_k_df.head())
# print(matrix_k_df.tail())
# print(matrix_f_df.head())
disp = solve_unknowns(matrix_k_df, matrix_f_df)
print(disp.head())
print(disp.tail())
