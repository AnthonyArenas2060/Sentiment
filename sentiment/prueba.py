import pandas as pd
import streamlit as st
import facebook
import requests
from transformers import pipeline
import matplotlib.pyplot as plt
import numpy as np

import streamlit as st
import streamlit_authenticator as stauth

#import yaml
#from yaml.loader import SafeLoader

#with open('C:\\Users\\anthony.arenas\\Downloads\\config.yaml') as file:
#    config = yaml.load(file, Loader=SafeLoader)

# Pre-hashing all plain text passwords once
# stauth.Hasher.hash_passwords(config['credentials'])

#authenticator = stauth.Authenticate(
#    config['credentials'],
#    config['cookie']['name'],
#    config['cookie']['key'],
#    config['cookie']['expiry_days']
#)

#try:
#    a = authenticator.login()
#    st.write(a)
#except Exception as e:
#    st.error(e)




st.markdown("""
    <style>
        /* Cambiar color de fondo */
        .stApp {
            background-color: #f4f4f9;
        }

        /* Estilo para títulos */
        h1, h2, h3 {
            color: #2c3e50;
            font-family: 'Poppins', sans-serif;
        }

        /* Tarjetas o contenedores personalizados */
        .card {
            background-color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 Sentiment Analysis App - Facebook Pages")

token = st.text_input("Introduce tu token de acceso (short-lived):", type="password")


if token:
    try:
        app_id = '547202674255200'
        app_secret = 'db55118786d51381d1a3af93bc031b67'

        # 2️⃣ Intercambiar el token corto por uno largo
        url = 'https://graph.facebook.com/oauth/access_token'
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'fb_exchange_token': token
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        response_json = response.json()

        user_long_token = response_json.get('access_token')
        graph = facebook.GraphAPI(access_token=user_long_token, version="3.1")

        # 3️⃣ Inputs de fecha
        date_ini = st.date_input("Selecciona la fecha inicial")
        date_fin = st.date_input("Selecciona la fecha final")

        # 4️⃣ Obtener información de las páginas asociadas
        page_data = graph.get_object('/me/accounts')
        info = pd.DataFrame(page_data['data'])

        st.subheader("📋 Páginas asociadas a tu cuenta")
        st.dataframe(info['name'])

        # 5️⃣ Permitir seleccionar un número (por ejemplo, el índice de una fila)
        if not info.empty:
            indice = st.number_input(
                "Selecciona el número de fila que deseas usar:",
                min_value=0,
                max_value=len(info) - 1,
                step=1
            )
            if indice:
                st.write("Seleccionaste la página:")
                st.write(info['name'][indice])
                permanent_page_token = page_data['data'][indice]['access_token']
                page_id = page_data['data'][indice]['id']

                graph = facebook.GraphAPI(access_token=permanent_page_token, version=3.1)
                graph.get_object(id=page_id, fields='name')

                posts = graph.get_connections(id=page_id, connection_name="feed", since=date_ini, until=date_fin)
                posteos = pd.DataFrame(posts['data'])
                if not posteos.empty:
                    posteos = posteos.iloc[:, :3]
                    posteos.columns = ['Fecha', 'Mensaje', 'id']
 
                    posteos['Fecha'] = pd.to_datetime(posteos['Fecha'])
                    posteos['Fecha'] = posteos['Fecha'].dt.strftime('%Y-%m-%d')

                    st.subheader("📋 Post asociadas a tu cuenta")
                    st.dataframe(posteos)


                    post_id = posteos['id']

                    def get_comments_recursive(object_id, graph, level=0):
                        """
                        Obtiene comentarios (y replies) de un objeto de Facebook (post o comentario).
                        """
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

                                # Llamada recursiva para traer replies de este comentario
                                replies = get_comments_recursive(c["id"], graph, level=level+1)
                                comments_data.extend(replies)

                            # Paginación: revisa si hay más páginas
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
                    coments_gente = []
                    total_comments_all_posts = 0
                    for i in post_id:
                        st.markdown(f"### 📌 Comentarios del post: `{i}`")
                        st.markdown("----------------------------------")

                        all_comments = get_comments_recursive(i, graph)

                        count = 0
                        for c in all_comments:
                            if c.get("message"):  # solo cuenta si hay texto
                                st.markdown("  " * c["level"] + f"- {c['from']}: {c['message']}")
                                count += 1    
                                #st.markdown(type(c['from']))
                                if c['from'] is None:
                                    coments_gente.append(c['message'])

                        st.markdown("-"*60)
                        st.info(f"Total de comentarios (incluyendo replies) en este post: {count}")
                        st.markdown("=================================================================")
                        total_comments_all_posts += count
                        
                    st.markdown("\n📊 RESUMEN GENERAL")
                    st.markdown("=================================================================")
                    st.success(f"Total de comentarios en TODOS los posts: {total_comments_all_posts}")

                    

                    a = pipeline("sentiment-analysis", model=r"pysentimiento/robertuito-sentiment-analysis", tokenizer=r"pysentimiento/robertuito-sentiment-analysis")
                    df = pd.DataFrame({"comentario": coments_gente})    

                    resultados = a(df["comentario"].tolist(),  truncation=True,  max_length=128)

                    df_resultados = pd.DataFrame(resultados)

                    df_final = pd.concat([df, df_resultados], axis=1)

                    df_final = df_final.rename(columns={"label": "sentimiento", "score": "confianza"})

                    df_final = df_final.sort_values(by="sentimiento")

                    negativo = df_final[df_final['sentimiento'] == 'NEG']['comentario'].count()
                    neutro = df_final[df_final['sentimiento'] == 'NEU']['comentario'].count()
                    positivo = df_final[df_final['sentimiento'] == 'POS']['comentario'].count()

                    tabla = df_final["sentimiento"].value_counts().rename_axis("sentimiento").reset_index(name="Facebook")

                    orden = ["POS", "NEU", "NEG"] 

                    tabla = tabla.set_index("sentimiento").reindex(orden).reset_index()
                    st.dataframe(tabla)
                    y = np.array([positivo, neutro, negativo])
                    mylabels = ["Positivo", "Neutro", "Negativo"]

                    # Crear figura y ejes
                    fig, ax = plt.subplots()

                    # Generar gráfico de pastel
                    ax.pie(y, labels=mylabels, colors=['green', 'gray', 'red'], autopct='%1.1f%%')
                    st.pyplot(fig)

                    csv = df_final.to_csv(index=False).encode('utf-8')
                    st.markdown("""
                                <style>
                                div.stDownloadButton > button {
                                    background-color: #1E90FF;
                                    color: white;
                                    padding: 0.6em 1.2em;
                                    border-radius: 10px;
                                    border: none;
                                    font-size: 16px;
                                    font-weight: bold;
                                    cursor: pointer;
                                    transition: all 0.3s ease;
                                }
                                div.stDownloadButton > button:hover {
                                    background-color: #0073e6;
                                    transform: scale(1.05);
                                    box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
                                }
                                </style>
                            """, unsafe_allow_html=True)
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name='sentiment.csv',
                        mime='text/csv')
                else:
                    st.write("No se encontraron publicaciones en el rango de fechas seleccionado.")


    except Exception as e:
        st.error(f"Ocurrió un error: {e}")

