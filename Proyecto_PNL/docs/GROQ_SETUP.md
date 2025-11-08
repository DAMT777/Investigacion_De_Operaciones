Instalación del cliente Groq
============================

Para habilitar el módulo de IA con Groq:

1) Instala la librería de Python

   pip install groq

   (Opcional) añade a tu requirements:

   groq>=0.10.0

2) Configura la clave de API en tu entorno (Windows PowerShell):

   setx GROQ_API_KEY "TU_CLAVE_AQUI"

   Luego cierra y vuelve a abrir la terminal.

3) Variables opcionales:

   - GROQ_MODEL (por defecto: llama3-8b-8192)
   - AI_TEMPERATURE (por defecto: 0.2)
   - AI_MAX_TOKENS (por defecto: 2048)
   - AI_PROMPT_PATH (ruta alternativa al prompt contextual)

