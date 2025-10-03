import numpy as np

def Simplex(coeficentsObjetiveFunction, constraintMatrix, rightOfRestrictions, sense="max", constraints=None):
    steps = []
    coeficentsObjetiveFunction = np.array(coeficentsObjetiveFunction, dtype=float)
    constraintMatrix = np.array(constraintMatrix, dtype=float)
    rightOfRestrictions = np.array(rightOfRestrictions, dtype=float)
    
    if sense == "min":
        coeficentsObjetiveFunction = -coeficentsObjetiveFunction
        
    variablesNumber = len(coeficentsObjetiveFunction)
    constraintsNumber = len(rightOfRestrictions)
    tableau = np.zeros((constraintsNumber+1, variablesNumber + constraintsNumber + 1))
    tableau[:constraintsNumber, :variablesNumber] = constraintMatrix
    tableau[:constraintsNumber, variablesNumber:variablesNumber+constraintsNumber] = np.eye(constraintsNumber)
    tableau[:constraintsNumber, -1] = rightOfRestrictions
    tableau[-1, :variablesNumber] = -coeficentsObjetiveFunction
    
    steps.append(tableau.copy())
    
    while any(tableau[-1,:-1]<0):
        col = np.argmin(tableau[-1,:-1])
        
        ratios = [tableau[i, -1] / tableau[i, col] if tableau[i, col] > 0 else np.inf for i in range(constraintsNumber)]
        row = np.argmin(ratios)
        
        pivot = tableau[row, col]
        tableau[row, :] /= pivot
        for i in range(constraintsNumber+1):
            if i != row:
                tableau[i, :] -= tableau[i, col] * tableau[row, :]

        steps.append(tableau.copy())
        
    solution = {"Z": float(tableau[-1, -1])}
    for j in range(variablesNumber):
        col = tableau[:, j]
        if list(col[:-1]).count(0) == (constraintsNumber-1) and 1 in col:
            row = np.where(col == 1)[0][0]
            solution[f"x{j+1}"] = float(tableau[row, -1])
        else:
            solution[f"x{j+1}"] = 0

    return steps, solution