import pandas as pd
import matplotlib.pyplot as plt

print("=== Paso 2: Variables y Operadores ===")
entero = 10           
decimal = 3.141516         
cadena = "Hello world ;)" 
booleano = True        

print("Entero:", entero)
print("Decimal:", decimal)
print("Cadena:", cadena)
print("Booleano:", booleano)

suma = entero + 5
resta = entero - 2
multiplicacion = entero * 3
division = entero / 2

print("\nOperadores Aritméticos:")
print("Suma:", suma, "\nResta:", resta, "\nMultiplicación:", multiplicacion, "\nDivisión:", division)

print("\nOperadores Lógicos y de Comparación:")
print("¿La variable entero > 5?", entero > 5)
print("¿La variable decimal == 3.141516?", decimal == 3.141516)
print("booleano AND (entero > 5):", booleano and (entero > 5))
print("booleano OR (entero < 5):", booleano or (entero < 5))

x = 10
x += 5
print("\nOperador de Asignación (+=):", x)

print("\n=== Paso 3: Condicionales ===")

numero = 8
if numero > 10:
    print("El número es mayor que 10")
elif numero == 10:
    print("El número es igual a 10")
else:
    print("El número es menor que 10")

print("\n=== Paso 4: Ciclos ===")

tabla = int(input("Digite un numero: "))

print("\nCiclo for (Tabla de multiplicar del ", tabla, ")")
for i in range(0, 11):
    print(tabla, " x " , i, " = ", (tabla*i))

print("\n\nCiclo while (contador hasta 5):")
contador = 1
while contador <= 5:
    print(contador, end=" ")
    contador += 1

print("\n\n=== Paso 5: Listas ===")

frutas = ["manzana", "pera", "uva"]
print("Lista inicial:", frutas)
frutas.append("naranja")   
frutas.remove("pera")      
frutas[1] = "sandía"       
print("Lista modificada:", frutas)

print("\nIteración con for y len():")
for i in range(len(frutas)):
    print(f"Índice {i} -> {frutas[i]}")

print("\nIteración con enumerate():")
for i, fruta in enumerate(frutas):
    print(f"Índice {i} -> {fruta}")

print("\n=== Paso 6: Importar CSV con Pandas ===")

datos = pd.read_csv("archivo.csv", encoding="latin1", sep=";")

print("Primeras filas del dataset:")
print(datos.head())

print("\n=== Paso 7: Gráficos con Matplotlib ===")

# 1. Gráfico de línea: evolución de vacunados en sector público y privado
plt.figure(figsize=(8,5))
plt.plot(datos["Año"], datos["Vacunados sector_publico"], marker="o", label="Sector Público")
plt.plot(datos["Año"], datos["Vacunados sector_privado"], marker="s", label="Sector Privado")
plt.title("Vacunados por Año - Sector Público vs Privado")
plt.xlabel("Año")
plt.ylabel("Número de Vacunados")
plt.legend()
plt.show()

# 2. Gráfico de barras: total vacunados en sector público por localidad
plt.figure(figsize=(10,6))
datos.groupby("localidad")["Vacunados sector_publico"].sum().sort_values().plot(kind="barh", color="skyblue")
plt.title("Vacunados en Sector Público por Localidad")
plt.xlabel("Número de Vacunados")
plt.ylabel("Localidad")
plt.show()

# 3. Gráfico de barras comparativo: público vs privado por localidad
plt.figure(figsize=(12,6))
datos.groupby("localidad")[["Vacunados sector_publico","Vacunados sector_privado"]].sum().plot(kind="bar", width=0.7)
plt.title("Vacunados en Sector Público y Privado por Localidad")
plt.xlabel("Localidad")
plt.ylabel("Número de Vacunados")
plt.xticks(rotation=45)
plt.legend(["Sector Público","Sector Privado"])
plt.show()
