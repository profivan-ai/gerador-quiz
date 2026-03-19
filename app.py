import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Configuração da Página
st.set_page_config(page_title="Gerador de Quiz de Vídeo", page_icon="🎓")
st.title("🎥 Vídeo para Questionário (Via Transcrição)")
st.markdown("Transforme vídeos do YouTube em 5 questões de múltipla escolha instantaneamente.")

# 1. Configurar API Key (Na barra lateral)
st.sidebar.header("Configurações")
api_key_input = "AIzaSyBxuQS66hAUkl_pg7Ozx28rup3r6BAODUA"

def extrair_video_id(url):
    """Extrai o ID do vídeo de diversos formatos de URL do YouTube"""
    padrao = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    resultado = re.search(padrao, url)
    return resultado.group(1) if resultado else None

if api_key_input:
    genai.configure(api_key=api_key_input)
    # Usando o modelo Flash que é rápido e ótimo para textos
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 2. Input do Usuário
    video_url = st.text_input("Cole a URL do vídeo do YouTube aqui:")

    if st.button("Gerar Questionário"):
        if not video_url:
            st.error("Por favor, insira uma URL válida.")
        else:
            video_id = extrair_video_id(video_url)
            
            if not video_id:
                st.error("Não foi possível identificar o ID do vídeo. Verifique a URL.")
            else:
                try:
                    with st.spinner("Buscando transcrição do vídeo..."):
                        # Tenta buscar em Português, senão tenta Inglês ou Automática
                        try:
                            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
                        except:
                            # Fallback para qualquer legenda disponível (inclusive gerada automaticamente)
                            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id).find_transcript(['pt', 'en']).fetch()
                        
                        full_text = " ".join([t['text'] for t in transcript_list])

                    with st.spinner("O Gemini está elaborando as questões..."):
                        # Prompt otimizado para texto
                        prompt = f"""
                        Com base na transcrição do vídeo abaixo, crie um questionário:
                        1. Gere exatamente 05 questões de múltipla escolha.
                        2. Cada questão deve ter exatamente 04 alternativas (A, B, C, D).
                        3. Use formatação Markdown clara (## para perguntas).
                        4. Indique a alternativa correta em negrito logo abaixo das opções de cada questão.
                        
                        Transcrição:
                        {full_text}
                        """
                        
                        response = model.generate_content(prompt)

                        # Exibição do Resultado
                        st.success("Questionário Gerado com Sucesso!")
                        st.markdown("---")
                        st.markdown(response.text)
                        
                        # Botão para copiar/baixar o texto
                        st.download_button("Baixar Questionário (.md)", response.text, file_name="quiz.md")

                except Exception as e:
                    if "Subtitles are disabled" in str(e):
                        st.error("Este vídeo não possui legendas/transcrição habilitadas. Tente outro vídeo.")
                    else:
                        st.error(f"Ocorreu um erro: {e}")
else:
    st.warning("⚠️ Insira sua Gemini API Key na barra lateral para começar.")

st.markdown("---")
st.caption("Desenvolvido para fins educacionais usando Google Gemini 1.5 Flash.")

