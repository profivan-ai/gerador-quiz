import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Configuração da Página
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓", layout="centered")

st.title("🎥 YouTube para Questionário")
st.markdown("Cole o link de um vídeo para gerar 5 questões de múltipla escolha com o Gemini.")

# 1. Configurar API Key
# IMPORTANTE: Deixei a variável fixa como você fez, mas corrigi o fluxo
api_key_input = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"

def extrair_video_id(url):
    """Extrai o ID do vídeo de URLs do YouTube (curtas ou longas)"""
    reg_exp = r"(?:v=|\/|embed\/|youtu.be\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(reg_exp, url)
    return match.group(1) if match else None

def buscar_legenda(video_id):
    """Busca a melhor legenda disponível (Manual ou Automática)"""
    try:
        # Tenta obter a lista de transcrições
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            # Tenta buscar especificamente em Português ou Inglês
            transcript = transcript_list.find_transcript(['pt', 'en'])
        except:
            # Se não houver as acima, tenta encontrar uma tradução para português
            try:
                transcript = transcript_list.find_transcript(['en']).translate('pt')
            except:
                # Fallback final: pega a primeira da lista (geralmente a original)
                transcript = next(iter(transcript_list))
            
        data = transcript.fetch()
        return " ".join([t['text'] for t in data])
    except Exception as e:
        raise Exception(f"Este vídeo não possui legendas disponíveis ou estão desativadas. Erro: {str(e)}")

# Fluxo Principal
if api_key_input:
    try:
        genai.configure(api_key=api_key_input)
        # CORREÇÃO: O nome correto do modelo é 'gemini-1.5-flash'
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erro na configuração da API: {e}")

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
                    with st.spinner("Lendo conteúdo do vídeo (transcrição)..."):
                        texto_video = buscar_legenda(v_id)

                    with st.spinner("Gemini elaborando questões..."):
                        prompt = f"""
                        Baseado na transcrição abaixo, crie um questionário:
                        1. Exatamente 05 questões de múltipla escolha.
                        2. Exatamente 04 alternativas por questão (A, B, C, D).
                        3. Formatação Markdown (Use ## para o título de cada questão).
                        4. Indique a alternativa correta em negrito logo abaixo das opções de cada questão.
                        
                        Transcrição:
                        {texto_video}
                        """
                        response = model.generate_content(prompt)

                        st.success("Questionário Gerado!")
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
                    st.error(f"{error}")
else:
    st.info("💡 API Key não configurada corretamente.")

st.divider()
st.caption("Nota: Este app depende de legendas (mesmo que automáticas) disponíveis no vídeo.")
