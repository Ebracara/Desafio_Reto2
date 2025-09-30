![Bootcamp-logo](logo_bbk_bootcamps_thebridge.jpg)

# **Desafío Tripulaciones**
## Reto 2 - Data Science: Modelos básicos de consumo y predicción de gasto mensual.

### Obtención de datos
Los datos se han obtenido mediante **Web Scraping** y **APIs** de páginas web oficiales.

### Entorno de desarrollo
Hemos utilizado **UV** para la creación y gestión del entorno virtual de Python.

### Base de datos
Utilizamos **PostgreSQL** alojada en **Aiven** y **DBeaver** para establecer y gestionar las conexiones con la base de datos.

### Modelos de predicción
Implementamos dos modelos predictivos de machine learning:

**(1) Modelo 1 - Consumo:** Se consideró el tipo de vehículo y las rutas realizadas, incluyendo los kilómetros recorridos y el tiempo empleado.

**(2) Modelo 2 - Gastos:** Se predijo el precio del carburante. El gasto final se obtuvo multiplicando el consumo medio obtenido en el modelo 1 por la predicción del precio del modelo 2.

### Desarrollo
+ Utilizamos **FastAPI** para gestionar las peticiones y servir las predicciones de los modelos.

+ Desarrollamos una interfaz interactiva con **Streamlit** para facilitar la interacción con los modelos de forma intuitiva y visual.

### Despliegue
Para el despliegue, contenerizamos la aplicación usando **Docker**, incluyendo tanto [FastAPI](https://desafio-reto2.onrender.com/) como (Streamlit)[https://desafio-reto2-1.onrender.com/] en el mismo contenedor. El contenedor Docker fue desplegado en la nube utilizando [Render](https://render.com/).

### Equipo
+ [Esther Begoña](https://www.linkedin.com/in/estherbego%C3%B1a/)
+ [Jaime Relea](https://www.linkedin.com/in/jrsmf/)
+ [Omar Mourabit](https://www.linkedin.com/in/8xbit/)
+ [Jhon Anthohy Quiliche](https://www.linkedin.com/in/anthonyquili/)
+ [Isa Escribano](https://www.linkedin.com/in/isa-escribano-g%C3%B3mez-a215a611b/)
