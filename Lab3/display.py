import pandas as pd

def  ShowTable(tableau, num_vars, num_constraints, titulo="Tabla"):
    
    cols = [f"x{i+1}" for i in range(num_vars)] + [f"s{i+1}" for i in range(num_constraints)] + ["RHS"]

    df = pd.DataFrame(tableau, columns=cols)

    print(f"\n{titulo}:")
    print(df)
    return df
