import streamlit as st
import pandas as pd
from numbers import Number

from simplex import Simplex
from display import (
    problem_summary,
    build_iteration_views,
    label_tableau,
    pretty_number,
)
from parser_ai import parse_problem


def inject_global_styles() -> None:
    """Estilos globales para el Laboratorio método Simplex."""
    st.markdown(
        """
        <style>
        .simplex-header {
            padding: 0.75rem 0 1.25rem 0;
        }
        .simplex-title {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(90deg, #38bdf8, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .simplex-subtitle {
            font-size: 0.95rem;
            color: #cbd5f5;
        }
        .simplex-badge {
            display: inline-block;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
            background-color: #0f172a;
            color: #e5e7eb;
            border: 1px solid #1f2937;
            margin-right: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def parse_manual_input(c_text: str, constraints_text: str):
    if not c_text.strip():
        raise ValueError("Ingresa los coeficientes de la funcion objetivo.")

    try:
        c = [float(x.strip()) for x in c_text.replace(" ", "").split(",") if x.strip()]
    except ValueError as exc:
        raise ValueError("Revisa el formato de la funcion objetivo (usa comas).") from exc

    if not c:
        raise ValueError("No se detectaron coeficientes para la funcion objetivo.")

    lines = [ln for ln in constraints_text.strip().splitlines() if ln.strip()]
    if not lines:
        raise ValueError("Ingresa al menos una restriccion.")

    allowed_signs = ["<=", ">=", "="]
    A, b = [], []
    for line in lines:
        sign_found = None
        for sign in allowed_signs:
            if sign in line:
                sign_found = sign
                partes = line.split(sign, 1)
                break
        if not sign_found or len(partes) != 2:
            raise ValueError(f"No pude interpretar la restriccion: '{line}'. Usa el formato '1,2 <= 6'.")

        if sign_found != "<=":
            raise ValueError("Por ahora solo se aceptan restricciones '<=' en modo manual.")

        lhs, rhs = partes[0], partes[1]
        try:
            coeficientes = [float(x.strip()) for x in lhs.replace(" ", "").split(",") if x.strip()]
            if len(coeficientes) != len(c):
                raise ValueError
        except ValueError as exc:
            raise ValueError(f"Revisa los coeficientes de la restriccion: '{line}'.") from exc

        try:
            b_i = float(rhs.strip())
        except ValueError as exc:
            raise ValueError(f"No pude interpretar el lado derecho en: '{line}'.") from exc

        A.append(coeficientes)
        b.append(b_i)

    return c, A, b


def style_simplex_table(df: pd.DataFrame, pivot_row=None, pivot_col=None):
    """
    Devuelve un Styler de pandas listo para Streamlit.
    Se convierte todo a texto para evitar problemas de Arrow
    y se aplican colores a fila, columna y elemento pivote.
    """
    df_display = df.copy()

    def _to_display(value):
        if isinstance(value, Number):
            return pretty_number(value, decimals=4)
        return str(value)

    df_display = df_display.applymap(_to_display)

    styled = (
        df_display.style.set_table_styles(
            [
                {"selector": "thead th", "props": [("background-color", "#0f172a"), ("color", "#f8fafc")]},
                {"selector": "tbody td", "props": [("border", "1px solid #1f2937"), ("font-family", "Segoe UI")]},
                {"selector": "tbody th", "props": [("background-color", "#1e293b"), ("color", "#f1f5f9")]},
            ]
        )
    )

    def _highlight(data):
        styles = pd.DataFrame("", index=data.index, columns=data.columns)
        if pivot_col and pivot_col in styles.columns:
            styles.loc[:, pivot_col] = styles.loc[:, pivot_col] + "background-color: rgba(74, 222, 128, 0.35);"
        if pivot_row is not None and pivot_row in styles.index:
            styles.loc[pivot_row, :] = styles.loc[pivot_row, :] + "background-color: rgba(56, 189, 248, 0.35);"
        if (
            pivot_row is not None
            and pivot_col
            and pivot_col in styles.columns
            and pivot_row in styles.index
        ):
            styles.loc[pivot_row, pivot_col] = "background-color: #f97316; color: #0f172a; font-weight: 600;"
        return styles

    return styled.apply(_highlight, axis=None)


def run_simplex(c, A, b, sense="max"):
    steps, solution = Simplex(c, A, b, sense=sense)
    return {
        "c": c,
        "A": A,
        "b": b,
        "sense": sense,
        "steps": steps,
        "solution": solution,
    }


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def render_solution(solution, n_vars):
    st.subheader("Solucion optima (metodo Simplex)")
    vars_sorted = [f"x{i+1}" for i in range(n_vars)]
    valores = [pretty_number(solution.get(var, 0), decimals=4) for var in vars_sorted]

    for grupo in chunked(list(zip(vars_sorted, valores)), 3):
        cols = st.columns(len(grupo))
        for col, (var, val) in zip(cols, grupo):
            col.metric(label=var, value=val)
    st.metric(label="Z", value=pretty_number(solution.get("Z", 0), decimals=4))


def show_iterations(result):
    c, A, b, steps, sense = result["c"], result["A"], result["b"], result["steps"], result["sense"]
    views = build_iteration_views(steps, c, A, b, sense=sense)

    if not views:
        st.info("No se detectaron iteraciones intermedias; se mostro la tabla final directamente.")
        final_df = label_tableau(steps[-1], len(c), len(b))
        st.table(style_simplex_table(final_df))
        return

    st.subheader("Iteraciones del metodo")
    st.caption(f"Se realizaron {len(views)} iteraciones de pivoteo.")

    if len(views) == 1:
        idx = 1
    else:
        idx = st.slider("Selecciona la iteracion a visualizar", 1, len(views), 1)
    view = views[idx - 1]

    st.markdown(f"#### Iteracion {view['index']}")
    if view.get("entering") and view.get("leaving"):
        col1, col2, col3 = st.columns([1, 1, 2])
        col1.markdown(
            "<span class='simplex-badge'>VB entra</span><br><b>{}</b>".format(view["entering"]),
            unsafe_allow_html=True,
        )
        col2.markdown(
            "<span class='simplex-badge'>VB sale</span><br><b>{}</b>".format(view["leaving"]),
            unsafe_allow_html=True,
        )
        if view.get("pivot_row") is not None and view.get("pivot_col_name"):
            col3.markdown(
                "<span class='simplex-badge'>Elemento pivote</span><br>fila {}, columna {}".format(
                    view["pivot_row"] + 1, view["pivot_col_name"]
                ),
                unsafe_allow_html=True,
            )

    st.caption("Tabla antes del pivote")
    st.table(
        style_simplex_table(
            view["before_df"],
            pivot_row=view.get("pivot_row"),
            pivot_col=view.get("pivot_col_name"),
        )
    )
    st.caption("Resultado despues del pivote")
    st.table(style_simplex_table(view["after_df"]))

    with st.expander("Ver todas las iteraciones (tabla despues del pivote)"):
        for v in views:
            st.markdown(f"**Iteracion {v['index']}**")
            st.table(style_simplex_table(v["after_df"]))


def main():
    st.set_page_config(page_title="Laboratorio metodo Simplex", layout="wide")
    inject_global_styles()

    st.markdown(
        """
        <div class="simplex-header">
            <div class="simplex-title">Laboratorio metodo Simplex</div>
            <div class="simplex-subtitle">
                Construye el modelo, observa cada iteracion de pivoteo y analiza la solucion optima paso a paso.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "result" not in st.session_state:
        st.session_state["result"] = None
    if "error" not in st.session_state:
        st.session_state["error"] = None
    if "ia_model" not in st.session_state:
        st.session_state["ia_model"] = None
    if "manual_c" not in st.session_state:
        st.session_state["manual_c"] = "3,5"
    if "manual_constraints" not in st.session_state:
        st.session_state["manual_constraints"] = "1,2 <= 6\n3,2 <= 12"

    st.sidebar.title("Panel del laboratorio")
    st.sidebar.markdown(
        "- Elige el modo de ingreso (manual o IA).\n"
        "- Ajusta la iteracion para seguir el pivoteo.\n"
        "- Revisa la solucion optima al final."
    )

    tab_manual, tab_ia = st.tabs(["Ingreso manual", "Lenguaje natural (IA)"])

    with tab_manual:
        st.markdown("Ingresa los coeficientes separados por comas. Ejemplo funcion objetivo: `3,5`.")
        with st.form("manual_form"):
            c_text = st.text_input(
                "Funcion objetivo Z =",
                key="manual_c",
                value=st.session_state["manual_c"],
            )
            constraints_text = st.text_area(
                "Restricciones (una por linea, formato `1,2 <= 6`)",
                key="manual_constraints",
                value=st.session_state["manual_constraints"],
                height=120,
            )
            sense = st.selectbox(
                "Tipo de problema",
                options=["max", "min"],
                format_func=lambda x: "Maximizar" if x == "max" else "Minimizar",
            )
            submitted = st.form_submit_button("Resolver problema")

        if submitted:
            try:
                st.session_state["manual_c"] = c_text
                st.session_state["manual_constraints"] = constraints_text
                c, A, b = parse_manual_input(c_text, constraints_text)
                st.session_state["result"] = run_simplex(c, A, b, sense=sense)
                st.session_state["error"] = None
            except Exception as exc:
                st.session_state["error"] = str(exc)
                st.session_state["result"] = None

    with tab_ia:
        with st.form("ia_form"):
            texto = st.text_area("Describe el problema en lenguaje natural", height=160)
            submitted_ia = st.form_submit_button("Proponer modelo con IA")
        if submitted_ia:
            try:
                c, A, b = parse_problem(texto.strip())
                st.session_state["ia_model"] = {"c": c, "A": A, "b": b}
                st.session_state["error"] = None
            except Exception as exc:
                st.session_state["error"] = f"No se pudo interpretar el problema: {exc}"
                st.session_state["ia_model"] = None
                st.session_state["result"] = None

        ia_model = st.session_state.get("ia_model")
        if ia_model:
            st.markdown("#### Modelo propuesto por la IA")
            resumen_ia = problem_summary(ia_model["c"], ia_model["A"], ia_model["b"], sense="max")
            st.code(resumen_ia)

            df_A = pd.DataFrame(ia_model["A"])
            df_A["RHS"] = ia_model["b"]
            st.caption("Matriz de restricciones A y vector b")
            st.dataframe(df_A, use_container_width=True)

            col_copiar, col_resolver = st.columns(2)
            with col_copiar:
                if st.button("Copiar modelo al modo manual"):
                    st.session_state["manual_c"] = ",".join(str(ci) for ci in ia_model["c"])
                    lines = []
                    for row, rhs in zip(ia_model["A"], ia_model["b"]):
                        coef_str = ",".join(str(aij) for aij in row)
                        lines.append(f"{coef_str} <= {rhs}")
                    st.session_state["manual_constraints"] = "\n".join(lines)
                    st.info("Modelo copiado. Revisa y resuelve desde la pestaña 'Ingreso manual'.")

            with col_resolver:
                if st.button("Resolver este modelo (IA)"):
                    st.session_state["result"] = run_simplex(ia_model["c"], ia_model["A"], ia_model["b"], sense="max")

    if st.session_state["error"]:
        st.error(st.session_state["error"])

    result = st.session_state["result"]
    if result:
        st.divider()
        st.subheader("Modelo del problema")
        resumen = problem_summary(result["c"], result["A"], result["b"], result["sense"])
        st.code(resumen)

        show_iterations(result)
        render_solution(result["solution"], n_vars=len(result["c"]))


if __name__ == "__main__":
    main()

