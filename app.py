import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from pytubefix import YouTube
import re
import os
import time

# Configuração
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓")
st.title("🎥 YouTube para Questionário")

# API Key fixa
API_KEY = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def extrair_id(url):
    match = re.search(r"(?:v=|\/|embed\/|youtu.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def obter_via_legenda(v_id):
    """Tenta obter o texto das legendas"""
    try:
        t_list = YouTubeTranscriptApi.list_transcripts(v_id)
        try:
            t = t_list.find_transcript(['pt', 'en'])
        except:
            t = next(iter(t_list))
        return " ".join([i['text'] for i in t.fetch()])
    except:
        return None

def baixar_audio_pytube(url):
    """Baixa apenas o áudio usando pytubefix (mais resistente ao 403)"""
    yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
    audio = yt.streams.filter(only_audio=True).first()
    out_file = audio.download(filename="temp_audio.mp4")
    return out_file

# Interface
video_url = st.text_input("Cole a URL do YouTube:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Gerar Questionário"):
    v_id = extrair_id(video_url)
    if not v_id:
        st.error("URL Inválida.")
    else:
        try:
            conteudo_para_ia = None
            
            # PASSO 1: Tentar Legendas (Super Rápido)
            with st.spinner("Buscando legendas..."):
                texto = obter_via_legenda(v_id)
            
            if texto:
                st.info("Legendas encontradas! Processando...")
                conteudo_para_ia = [f"Baseado nesta transcrição, crie o quiz:\n\n{texto}"]
            else:
                # PASSO 2: Se não tem legenda, baixa o áudio (Fallback)
                st.warning("Vídeo sem legendas. Extraindo áudio para análise da IA...")
                path_audio = baixar_audio_pytube(video_url)
                
                with st.spinner("Fazendo upload do áudio para o Gemini..."):
                    audio_file = genai.upload_file(path=path_audio)
                    while audio_file.state.name == "PROCESSING":
                        time.sleep(2)
                        audio_file = genai.get_file(audio_file.name)
                    
                    conteudo_para_ia = [audio_file, "Analise este áudio e crie o questionário."]
                
                os.remove(path_audio) # Limpa o servidor

            # PASSO 3: Gerar com Gemini
            if conteudo_para_ia:
                with st.spinner("Gerando 5 questões..."):
                    prompt = """
                    Crie um questionário com:
                    - 05 questões de múltipla escolha (A, B, C, D).
                    - Formato Markdown com ## para cada pergunta.
                    - Resposta correta em negrito ao final de cada questão.
                    """
                    # Adiciona o prompt à lista de conteúdo
                    if isinstance(conteudo_para_ia, list):
                        conteudo_para_ia.append(prompt)
                    
                    response = model.generate_content(conteudo_para_ia)
                    
                    st.success("Pronto!")
                    st.markdown(response.text)
                    st.download_button("Baixar Quiz (.md)", response.text, file_name="quiz.md")

        except Exception as e:
            st.error(f"Erro ao processar este vídeo: {e}")
            st.info("Dica: Alguns vídeos têm restrições de idade ou direitos autorais que impedem o download em servidores.")

st.divider()
st.caption("Sistema Híbrido: Prioriza legendas e usa áudio como plano B.")
