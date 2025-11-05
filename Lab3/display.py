import numpy as np
import pandas as pd


def _basis_labels(tableau: np.ndarray, n_vars: int, n_cons: int, cols_names):
    labels = []
    for r in range(n_cons):
        name = "—"
        for j in range(n_vars + n_cons):
            col = tableau[:n_cons, j]
            if np.isclose(tableau[r, j], 1.0) and np.allclose(np.delete(col, r), 0.0):
                name = cols_names[j]
                break
        labels.append(name)
    labels.append("Z")
    return labels


def label_tableau(tableau: np.ndarray, n_vars: int, n_cons: int) -> pd.DataFrame:
    """
    Produce a labeled DataFrame for a tableau without changing any values.
    Adds 'VB' (variable básica) and a helper 'Z' column for didactic display.
    """
    cols = [f"x{i+1}" for i in range(n_vars)] + [f"s{i+1}" for i in range(n_cons)] + ["RHS"]
    df = pd.DataFrame(tableau.copy(), columns=cols)

    vb = _basis_labels(tableau, n_vars, n_cons, cols)
    df.insert(0, "VB", vb)

    # Add a didactic Z column (0 in constraints rows, 1 in last row)
    z_col = [0.0] * n_cons + [1.0]
    df.insert(1, "Z", z_col)

    return df


def compute_pivot_indices(tableau: np.ndarray):
    """Return (row, col) for the pivot based on current tableau. If optimal, returns (None, None)."""
    last_row = tableau[-1, :-1]
    if np.all(last_row >= -1e-12):  # numerical tolerance
        return None, None
    col = int(np.argmin(last_row))
    ratios = [
        tableau[i, -1] / tableau[i, col] if tableau[i, col] > 0 else np.inf
        for i in range(tableau.shape[0] - 1)
    ]
    row = int(np.argmin(ratios)) if len(ratios) > 0 else None
    return row, col


def pretty_number(x, decimals: int = 4):
    try:
        xf = float(x)
        # Use general format for compactness but with a cap on decimals
        return (f"{xf:.{decimals}f}").rstrip("0").rstrip(".") if not np.isclose(xf, 0) else "0"
    except Exception:
        return x


def annotate_pivot(df: pd.DataFrame, pivot_row: int, pivot_col_name: str) -> pd.DataFrame:
    """Return a copy of df where the pivot cell is bracketed for visual emphasis."""
    # Cast to object to allow string annotation without dtype warnings
    df2 = df.copy().astype(object)
    if pivot_row is None or pivot_col_name is None:
        return df2
    if pivot_col_name not in df2.columns:
        return df2
    try:
        val = df2.loc[pivot_row, pivot_col_name]
        df2.loc[pivot_row, pivot_col_name] = f"[{pretty_number(val)}]"
    except Exception:
        pass
    return df2


def dataframe_to_text(df: pd.DataFrame) -> str:
    # Format numeric cells nicely for text output
    df_fmt = df.copy()
    for c in df_fmt.columns:
        if c in ("VB",):
            continue
        df_fmt[c] = df_fmt[c].map(lambda v: pretty_number(v) if isinstance(v, (int, float, np.floating)) or str(v).replace('.', '', 1).lstrip('-').isdigit() else v)
    return df_fmt.to_string(index=False)


def problem_summary(c, A, b, sense: str = "max") -> str:
    # Build a human-friendly summary of the LP
    s_obj = "Maximizar" if sense == "max" else "Minimizar"
    obj = " + ".join([f"{pretty_number(ci)} x{i+1}" for i, ci in enumerate(c)])
    lines = [f"{s_obj}: Z = {obj}", "Sujeto a:"]
    for i, row in enumerate(A):
        cons = " + ".join([f"{pretty_number(aij)} x{j+1}" for j, aij in enumerate(row)])
        lines.append(f"  {cons} <= {pretty_number(b[i])}")
    lines.append(f"Variables: x1..x{len(c)} >= 0")
    return "\n".join(lines)


def ShowTable(tableau, num_vars, num_constraints, titulo="Tabla"):
    # Backwards-compatible function kept for external calls. Prints a plain table.
    df = label_tableau(np.array(tableau, dtype=float), num_vars, num_constraints)
    print(f"\n{titulo}:")
    print(dataframe_to_text(df))
    return df


def build_iteration_views(steps, c, A, b, sense="max"):
    """
    From a list of raw tableaux, create a list of dicts representing each pivot iteration.
    Each dict contains:
      - index: iteration number (1-based)
      - before_df: labeled DataFrame before pivot (with pivot cell marked)
      - after_df: labeled DataFrame after pivot
      - entering: entering variable name (e.g., x2)
      - leaving: leaving variable name (e.g., s1)
    """
    n_vars = len(c)
    n_cons = len(b)
    views = []
    total_pivots = max(0, len(steps) - 1)
    col_names = [f"x{i+1}" for i in range(n_vars)] + [f"s{i+1}" for i in range(n_cons)]

    for k in range(total_pivots):
        t_before = np.array(steps[k], dtype=float)
        t_after = np.array(steps[k + 1], dtype=float)
        # Compute pivot on the tableau BEFORE the pivot
        prow, pcol = compute_pivot_indices(t_before)

        before_df = label_tableau(t_before, n_vars, n_cons)
        entering = col_names[pcol] if pcol is not None else None
        leaving = before_df.loc[prow, "VB"] if prow is not None else None

        if entering is not None:
            before_df = annotate_pivot(before_df, prow, entering)

        after_df = label_tableau(t_after, n_vars, n_cons)

        views.append(
            {
                "index": k + 1,
                "before_df": before_df,
                "after_df": after_df,
                "entering": entering,
                "leaving": leaving,
            }
        )
    return views
