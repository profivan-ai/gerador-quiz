import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Configuração da Página
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓", layout="centered")

st.title("🎥 YouTube para Questionário")
st.markdown("Gere 5 questões de múltipla escolha a partir de qualquer vídeo com legendas.")

# 1. Configurar API Key (Chave fixa fornecida)
API_KEY = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"

def extrair_video_id(url):
    """Extrai o ID do vídeo de URLs do YouTube"""
    reg_exp = r"(?:v=|\/|embed\/|youtu.be\/)([0-9A-Za-z_-]{11})"
    match = re.search(reg_exp, url)
    return match.group(1) if match else None

def obter_texto_video(video_id):
    """Busca a transcrição ignorando bloqueios de 403 (usa API de legendas)"""
    try:
        # 1. Tenta pegar a lista de todas as legendas
        lista_transcricoes = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 2. Tenta Português, senão Inglês, senão a primeira disponível
        try:
            transcricao = lista_transcricoes.find_transcript(['pt', 'en'])
        except:
            transcricao = next(iter(lista_transcricoes))
            
        # 3. Se a legenda for em outro idioma, tenta traduzir para PT via API do YT
        try:
            transcricao_final = transcricao.translate('pt').fetch()
        except:
            transcricao_final = transcricao.fetch()
            
        return " ".join([t['text'] for t in transcricao_final])
    except Exception as e:
        raise Exception("Não foi possível extrair o texto. O vídeo pode estar sem legendas habilitadas.")

# Configuração da IA
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro na API: {e}")

# Interface
video_url = st.text_input("URL do Vídeo do YouTube:", placeholder="https://www.youtube.com/watch?v=ZYCBFwdekwM")

if st.button("Gerar Questionário"):
    if not video_url:
        st.warning("Insira uma URL.")
    else:
        v_id = extrair_video_id(video_url)
        if not v_id:
            st.error("ID do vídeo não encontrado na URL.")
        else:
            try:
                with st.spinner("Analisando o conteúdo do vídeo..."):
                    texto_completo = obter_texto_video(v_id)

                with st.spinner("Criando questões com IA..."):
                    prompt = f"""
                    Abaixo está a transcrição de um vídeo. Com base nela, crie:
                    1. 05 questões de múltipla escolha em Português.
                    2. 04 alternativas por questão (A, B, C, D).
                    3. Use Markdown: ## para Títulos e ** para a Resposta Correta.
                    
                    Transcrição:
                    {texto_completo}
                    """
                    response = model.generate_content(prompt)

                    st.success("Questionário Gerado!")
                    st.divider()
                    st.markdown(response.text)
                    
                    st.download_button(
                        label="Baixar Questionário (.md)",
                        data=response.text,
                        file_name="quiz.md",
                        mime="text/markdown"
                    )
            except Exception as error:
                st.error(f"Ops! {error}")

st.divider()
st.caption("Nota: Este método usa a API de transcrição para evitar o erro 403 Forbidden.")
