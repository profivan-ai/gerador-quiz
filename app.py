import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re
import os
import time

# Configuração
st.set_page_config(page_title="Gerador de Quiz IA Pro", page_icon="🎓")
st.title("🎥 Vídeo para Questionário (Modo Híbrido)")

# API Key fixa (como solicitado)
API_KEY = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def extrair_id(url):
    match = re.search(r"(?:v=|\/|embed\/|youtu.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def obter_transcricao(v_id):
    """Tenta obter a legenda do YouTube"""
    try:
        t_list = YouTubeTranscriptApi.list_transcripts(v_id)
        try:
            t = t_list.find_transcript(['pt', 'en'])
        except:
            t = next(iter(t_list))
        return " ".join([i['text'] for i in t.fetch()])
    except:
        return None

def baixar_audio_e_processar(url):
    """Baixa o áudio se não houver legenda"""
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# Interface
url = st.text_input("Cole a URL do YouTube:")

if st.button("Gerar Questionário"):
    v_id = extrair_id(url)
    if not v_id:
        st.error("URL Inválida.")
    else:
        try:
            # PASSO 1: Tentar Legenda (Rápido)
            with st.spinner("Tentando ler legendas..."):
                texto = obter_transcricao(v_id)
            
            conteudo_para_ia = None

            if texto:
                st.info("Legendas encontradas! Processando texto...")
                conteudo_para_ia = texto
            else:
                # PASSO 2: Se não tem legenda, baixar áudio (Lento, mas garantido)
                st.warning("Vídeo sem legendas. Extraindo áudio para análise (isso pode demorar)...")
                path_audio = baixar_audio_e_processar(url)
                
                with st.spinner("Enviando áudio para o Gemini..."):
                    audio_file = genai.upload_file(path=path_audio)
                    while audio_file.state.name == "PROCESSING":
                        time.sleep(2)
                        audio_file = genai.get_file(audio_file.name)
                    conteudo_para_ia = audio_file
                
                # Remover arquivo local após upload
                os.remove(path_audio)

            # PASSO 3: Gerar Quiz
            if conteudo_para_ia:
                with st.spinner("Gerando questões..."):
                    prompt = "Crie 5 questões de múltipla escolha (A, B, C, D) em Markdown sobre este conteúdo, com a resposta correta em negrito."
                    response = model.generate_content([conteudo_para_ia, prompt] if not isinstance(conteudo_para_ia, str) else [prompt + "\n\n" + conteudo_para_ia])
                    
                    st.success("Concluído!")
                    st.markdown(response.text)
                    st.download_button("Baixar MD", response.text, file_name="quiz.md")

        except Exception as e:
            st.error(f"Erro crítico: {e}")

st.divider()
st.caption("Este app usa legendas primeiro. Se não houver, ele 'ouve' o áudio do vídeo.")
