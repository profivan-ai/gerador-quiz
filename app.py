




import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Configuração da Página
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓", layout="centered")

st.title("🎥 YouTube para Questionário")
st.markdown("Cole o link de um vídeo para gerar 5 questões de múltipla escolha com o Gemini.")

# 1. Configurar API Key na barra lateral
st.sidebar.header("Configurações de IA")
api_key_input = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"


def extrair_video_id(url):
    """Extrai o ID do vídeo de URLs do YouTube (curtas ou longas)"""
    reg_exp = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(reg_exp, url)
    return match.group(1) if match else None

def buscar_legenda(video_id):
    """Busca a melhor legenda disponível (Manual ou Automática)"""
    try:
        # Tenta listar todas as legendas disponíveis para o vídeo
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Tenta buscar em Português (pt), senão Inglês (en)
        try:
            transcript = transcript_list.find_transcript(['pt', 'en'])
        except:
            # Se não achar pt/en, pega a primeira disponível (qualquer idioma)
            transcript = next(iter(transcript_list))
            
        data = transcript.fetch()
        return " ".join([t['text'] for t in data])
    except Exception as e:
        raise Exception(f"Não foi possível obter a legenda: {str(e)}")

# Fluxo Principal
if api_key_input:
    genai.configure(api_key=api_key_input)
    # Modelo Flash: Rápido e perfeito para processar texto de legendas
    model = genai.GenerativeModel('gemini-2.5-flash')

    video_url = st.text_input("URL do Vídeo do YouTube:", placeholder="https://www.youtube.com/watch?v=...")

    if st.button("Gerar Questionário"):
        if not video_url:
            st.warning("Por favor, insira uma URL.")
        else:
            v_id = extrair_video_id(video_url)
            if not v_id:
                st.error("URL Inválida! Verifique o link do YouTube.")
            else:
                try:
                    with st.spinner("Lendo conteúdo do vídeo..."):
                        texto_video = buscar_legenda(v_id)

                    with st.spinner("Gemini elaborando questões..."):
                        prompt = f"""
                        Baseado na transcrição abaixo, crie um questionário:
                        1. Exatamente 05 questões de múltipla escolha.
                        2. Exatamente 04 alternativas por questão (A, B, C, D).
                        3. Formatação Markdown (## para Questões).
                        4. Indique a alternativa correta em negrito abaixo das opções.
                        
                        Transcrição:
                        {texto_video}
                        """
                        response = model.generate_content(prompt)

                        st.success("Pronto!")
                        st.markdown("---")
                        st.markdown(response.text)
                        
                        # Opção de download
                        st.download_button(
                            label="Baixar Questionário",
                            data=response.text,
                            file_name="questionario_video.md",
                            mime="text/markdown"
                        )

                except Exception as error:
                    st.error(f"Erro no processamento: {error}")
else:
    st.info("💡 Digite sua API Key na barra lateral para ativar o gerador.")

st.divider()
st.caption("Nota: Este app depende de legendas disponíveis no vídeo.")
