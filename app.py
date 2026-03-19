import streamlit as st
import google.generativeai as genai
import yt_dlp
import os
import time

# Configuração da Página
st.set_page_config(page_title="Gerador de Quiz de Vídeo", page_icon="🎓")
st.title("🎥 Vídeo para Questionário")
st.markdown("Cole a URL do vídeo e receba 5 questões em Markdown.")

# 1. Configurar API (Pega das 'Secrets' do ambiente de hospedagem)
API_KEY = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 2. Input do Usuário
    video_url = st.text_input("URL do Vídeo (YouTube, etc.):")

    if st.button("Gerar Questionário"):
        if not video_url:
            st.error("Por favor, insira uma URL.")
        else:
            with st.spinner("Baixando áudio e processando..."):
                try:
                    # Configuração para baixar apenas o áudio (mais rápido)
                    ydl_opts = {
                        'format': 'm4a/bestaudio/best',
                        'outtmpl': 'temp_audio.%(ext)s',
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        audio_filename = ydl.prepare_filename(info)

                    # 3. Upload para o Gemini
                    video_file = genai.upload_file(path=audio_filename)

                    while video_file.state.name == "PROCESSING":
                        time.sleep(3)
                        video_file = genai.get_file(video_file.name)

                    # 4. Prompt
                    prompt = """
                    Analise este vídeo e crie um questionário:
                    - 05 questões de múltipla escolha.
                    - 04 alternativas por questão.
                    - Formato Markdown.
                    - Indique a resposta correta em negrito.
                    """

                    response = model.generate_content([video_file, prompt])

                    # 5. Resultado
                    st.markdown("### ✅ Questionário Gerado")
                    st.markdown(response.text)
                    
                    # Limpeza
                    os.remove(audio_filename)

                except Exception as e:
                    st.error(f"Erro: {e}")
else:
    st.info("Aguardando API Key para começar...")
