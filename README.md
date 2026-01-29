# Análisis de Sentimiento de Comentarios en Páginas de Facebook

Este proyecto automatiza la **extracción de publicaciones y comentarios de páginas de Facebook** mediante la **Meta Graph API** y aplica **análisis de sentimiento en español** para clasificar la percepción de los usuarios en **positiva, neutral o negativa**.

El flujo integra autenticación, recolección de datos, procesamiento, análisis de lenguaje natural y generación de métricas agregadas.

---

## Tecnologías utilizadas

- **Python 3.9+**
- **Meta Graph API**
- **facebook-sdk**
- **pandas**
- **requests**
- **transformers**
- **numpy**
- **matplotlib**

---

## Instalación de dependencias

Se recomienda el uso de un entorno virtual.

```bash
pip install facebook-sdk pandas requests transformers numpy matplotlib
```

## Flujo general del análisis

1. Autenticación con la Meta Graph API utilizando un token de usuario.

2. Intercambio del token de corta duración por un token de larga duración.

3. Obtención del token permanente de la página seleccionada.

4. Consulta de publicaciones dentro de un rango de fechas definido.

5. Extracción recursiva de comentarios y respuestas (replies) asociados a cada publicación.

6. Limpieza y estructuración de los datos en DataFrames.

7. Aplicación de un modelo de análisis de sentimiento en español.

8. Agregación de resultados y cálculo de métricas.

9. Generación de tablas y visualizaciones para su análisis.

## Autenticación con Meta Graph API
Token de usuario

```python
import facebook
import requests

app_id = 'TU_APP_ID'
app_secret = 'TU_APP_SECRET'
user_token = 'TU_TOKEN_CORTO'

url = 'https://graph.facebook.com/oauth/access_token'
params = {
    'grant_type': 'fb_exchange_token',
    'client_id': app_id,
    'client_secret': app_secret,
    'fb_exchange_token': user_token
}

response = requests.get(url, params=params)
user_long_token = response.json()['access_token']

graph = facebook.GraphAPI(
    access_token=user_long_token,
    version="3.1"
)
````

## Token de página
```python
page_data = graph.get_object('/me/accounts')

page_id = page_data['data'][#Numero de pagina]['id']
page_token = page_data['data'][#Numero de pagina]['access_token']

graph = facebook.GraphAPI(
    access_token=page_token,
    version="3.1"
)
```
## Obtención de publicaciones
```python
posts = graph.get_connections(
    id=page_id,
    connection_name="feed",
    since="2026-01-01",
    until="2026-01-12"
)
```

## Extracción de comentarios
```python
def get_comments_recursive(object_id, graph, level=0):
    comments_data = []
    comments = graph.get_connections(
        id=object_id,
        connection_name="comments",
        fields="id,from,message,created_time"
    )

    while True:
        for c in comments["data"]:
            comments_data.append({
                "id": c["id"],
                "from": c.get("from", {}).get("name"),
                "message": c.get("message"),
                "created_time": c.get("created_time"),
                "level": level
            })

            replies = get_comments_recursive(c["id"], graph, level + 1)
            comments_data.extend(replies)

        if "paging" in comments and "next" in comments["paging"]:
            comments = graph.get_connections(
                id=object_id,
                connection_name="comments",
                after=comments["paging"]["cursors"]["after"],
                fields="id,from,message,created_time"
            )
        else:
            break

    return comments_data
```
## Análisis de sentimiento
Se utiliza un modelo preentrenado en español basado en transformers.
```python
from transformers import pipeline
import pandas as pd

sentiment_model = pipeline(
    "sentiment-analysis",
    model="pysentimiento/robertuito-sentiment-analysis"
)

df = pd.DataFrame({"comentario": comentarios})
resultados = sentiment_model(df["comentario"].tolist(), truncation=True, max_length=128)

df_resultados = pd.DataFrame(resultados)
```
## Métricas y visualización

Los resultados se agregan para obtener la distribución de sentimientos y facilitar su análisis mediante tablas y gráficos.
![Screenshot of a pie chart.](https://raw.githubusercontent.com/AnthonyArenas2060/Sentiment/refs/heads/main/img/graf.png)

Además, se muestra la clasificación de cada comentario con su porcentaje de confianza
![Screenshot of a table.](https://raw.githubusercontent.com/AnthonyArenas2060/Sentiment/refs/heads/main/img/tabla.png)


