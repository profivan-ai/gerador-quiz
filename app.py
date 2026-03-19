import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import tempfile
import os

# Configuração
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓")
st.title("🎥 De Vídeo para Questionário")
st.markdown("Transforme vídeos do YouTube ou arquivos locais em questões de estudo.")

# API Key (Substitua pela sua ou use st.secrets)
API_KEY = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def extrair_id(url):
    pattern = r"(?:v=|\/|embed\/|youtu.be\/|v\/|watch\?v=|&v=|^)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def obter_legendas(v_id):
    try:
        t_list = YouTubeTranscriptApi.list_transcripts(v_id)
        try:
            t = t_list.find_transcript(['pt', 'en'])
        except:
            t = next(iter(t_list))
        return " ".join([i['text'] for i in t.fetch()])
    except:
        return None

# --- Interface em Abas ---
aba_link, aba_upload = st.tabs(["🔗 Link do YouTube", "📁 Upload de Arquivo"])

conteudo_para_ia = None

with aba_link:
    video_url = st.text_input("URL do Vídeo:", placeholder="https://www.youtube.com/watch?v=...")
    if video_url:
        v_id = extrair_id(video_url)
        if v_id:
            with st.spinner("Buscando legendas..."):
                texto = obter_legendas(v_id)
                if texto:
                    st.success("Legendas encontradas!")
                    conteudo_para_ia = [f"Baseado nesta transcrição, crie o quiz:\n\n{texto}"]
                else:
                    st.warning("Este vídeo não possui legendas disponíveis. Use a aba de Upload.")

with aba_upload:
    arquivo_video = st.file_uploader("Suba o vídeo ou áudio (MP4, MP3, WAV):", type=["mp4", "mp3", "wav", "m4a"])
    if arquivo_video:
        # Salva temporariamente para enviar ao Gemini
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{arquivo_video.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(arquivo_video.read())
            path_temp = tmp_file.name

        with st.spinner("Enviando arquivo para a IA analisar..."):
            try:
                # Upload para a API do Google (suporta vídeo/áudio nativamente)
                video_file_ai = genai.upload_file(path=path_temp)
                conteudo_para_ia = [video_file_ai, "Analise o conteúdo deste arquivo e crie o questionário."]
                st.success("Arquivo processado com sucesso!")
            except Exception as e:
                st.error(f"Erro no upload: {e}")
            finally:
                if os.path.exists(path_temp):
                    os.remove(path_temp)

# --- Processamento Final ---
if st.button("✨ Gerar Questionário Agora", type="primary"):
    if not conteudo_para_ia:
        st.error("Por favor, forneça um vídeo via link ou upload primeiro.")
    else:
        with st.spinner("A IA está elaborando as questões..."):
            prompt = """
            Crie um questionário com:
            - 05 questões de múltipla escolha (A, B, C, D).
            - Formato Markdown: ## para cada pergunta.
            - Resposta correta em negrito ao final de cada questão.
            - O questionário deve ser em Português.
            """
            
            try:
                # O Gemini 1.5 Flash aceita tanto texto quanto arquivos na mesma lista
                response = model.generate_content(conteudo_para_ia + [prompt])
                
                st.markdown("---")
                st.markdown(response.text)
                
                st.download_button(
                    label="📥 Baixar Quiz (.md)",
                    data=response.text,
                    file_name="quiz_gerado.md",
                    mime="text/markdown"
                )
            except Exception as e:
                st.error(f"Erro ao gerar conteúdo: {e}")

st.divider()
st.caption("Dica: O upload de arquivo funciona melhor para vídeos sem legenda ou conteúdos privados.")
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
