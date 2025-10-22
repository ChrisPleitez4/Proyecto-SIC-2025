# 🧾 Proyecto-SIC-2025
Repositorio oficial del proyecto de la materia **Sistemas Contables – Ciclo II, Año 2025**.

---

## ⚙️ Instrucciones para inicializar el entorno de desarrollo

### 🧱 PASO 1: Crear el entorno virtual
Ejecutar el siguiente comando en la raíz del proyecto:

```bash
python -m venv venv 
```
### PASO 2: Activar el entorno virtual
En windows
```bash
venv\Scripts\activate
```

En linux
```bash
source venv/bin/activate
```
Deberia salir en consola 
```bash
(venv) C:\ruta\de\tu\proyecto>
```
### 📦 PASO 3: Instalar dependencias
Instala todas las librerías necesarias desde el archivo requirements.txt:
```bash
pip install -r requirements.txt
```
### 🧾 PASO 4: Crear el archivo .env
En la ruta raíz del proyecto (\Proyecto-SIC-2025\.env), crear el archivo .env con el siguiente contenido:
```bash
# Configuración del entorno Django
DEBUG=True
SECRET_KEY=ProyectDjangoSIC2025
ALLOWED_HOSTS=127.0.0.1,localhost
```
### 🗃️ PASO 5: Crear la base de datos y aplicar migraciones
```bash
python manage.py migrate
```

### ⚡ Versión rápida (resumen de comandos)

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear archivo .env
# (copiar el contenido del ejemplo anterior)

# 5. Migrar la base de datos
python manage.py migrate

# 6. Ejecutar servidor
python manage.py runserver
```

### Flujo para tus compañeros
Cuando un compañero baje cambios del repo:
```bash
git pull origin main
```
Luego, para actualizar su base de datos:
```bash
python manage.py migrate
```