import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Configuração da Página
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓", layout="centered")

st.title("🎥 YouTube para Questionário")
st.markdown("Cole o link de um vídeo para gerar 5 questões de múltipla escolha com o Gemini.")

# 1. Configurar API Key
# DICA: Em produção, use st.secrets para esconder sua chave
api_key_input = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"

def extrair_video_id(url):
    """Extrai o ID do vídeo de URLs do YouTube"""
    # Aceita links normais, curtos (youtu.be) e de embed
    reg_exp = r"(?:v=|\/|embed\/|youtu.be\/)([0-9A-Za-z_-]{11})"
    match = re.search(reg_exp, url)
    return match.group(1) if match else None

def buscar_legenda(video_id):
    """Busca a legenda usando o método mais estável da biblioteca"""
    try:
        # Tenta buscar primeiro em português, depois em inglês
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        return " ".join([t['text'] for t in transcript_list])
    except Exception as e:
        try:
            # Se falhar, tenta listar as disponíveis e pegar a primeira (qualquer idioma)
            # Aqui usamos a instância da classe para evitar o erro de 'type object'
            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = next(iter(transcript_list_obj))
            data = transcript.fetch()
            return " ".join([t['text'] for t in data])
        except Exception as final_e:
            raise Exception("Este vídeo não possui legendas disponíveis (nem automáticas). Tente outro vídeo.")

# Fluxo Principal
if api_key_input:
    try:
        genai.configure(api_key=api_key_input)
        # CORRIGIDO: gemini-1.5-flash é o modelo estável atual
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erro na configuração da IA: {e}")

    video_url = st.text_input("URL do Vídeo do YouTube:", placeholder="https://www.youtube.com/watch?v=...")

    if st.button("Gerar Questionário"):
        if not video_url:
            st.warning("Por favor, insira uma URL.")
        else:
            v_id = extrair_video_id(video_url)
            if not v_id:
                st.error("URL Inválida! Não conseguimos encontrar o ID do vídeo.")
            else:
                try:
                    with st.spinner("Extraindo texto do vídeo..."):
                        texto_video = buscar_legenda(v_id)

                    with st.spinner("Gemini gerando as questões..."):
                        prompt = f"""
                        Analise a transcrição abaixo e crie:
                        1. Exatamente 05 questões de múltipla escolha em Português.
                        2. Exatamente 04 alternativas por questão (A, B, C, D).
                        3. Formatação Markdown (Use ## para cada questão).
                        4. Indique a alternativa correta em negrito abaixo das opções.
                        
                        Transcrição:
                        {texto_video}
                        """
                        response = model.generate_content(prompt)

                        st.success("Questionário Gerado!")
                        st.divider()
                        st.markdown(response.text)
                        
                        st.download_button(
                            label="Baixar Questionário (.md)",
                            data=response.text,
                            file_name="quiz_video.md",
                            mime="text/markdown"
                        )

                except Exception as error:
                    st.error(f"Erro: {error}")
else:
    st.info("💡 API Key não detectada.")

st.divider()
st.caption("Aviso: O vídeo precisa ter a função de legendas habilitada no YouTube.")
