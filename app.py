import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import tempfile
import os
import time

# Configuração
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓")
st.title("🎥 De Vídeo para Questionário")

# EXPLICAÇÃO SOBRE A CHAVE:
# Para rodar localmente, substitua 'SUA_NOVA_CHAVE' pela nova chave que você gerar.
# Se for subir no Streamlit Cloud, use: API_KEY = st.secrets["GEMINI_KEY"]
API_KEY = st.text_input("Insira sua nova Gemini API Key:", type="password")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

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
                        conteudo_para_ia = [f"Baseado nesta transcrição em português, crie o quiz:\n\n{texto}"]
                    else:
                        st.warning("Vídeo sem legendas disponíveis. Use a aba de Upload.")

    with aba_upload:
        arquivo_video = st.file_uploader("Suba o vídeo ou áudio (MP4, MP3, WAV):", type=["mp4", "mp3", "wav", "m4a"])
        if arquivo_video:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{arquivo_video.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(arquivo_video.read())
                path_temp = tmp_file.name

            with st.spinner("Enviando para o Gemini (isso pode demorar dependendo do tamanho)..."):
                try:
                    file_upload = genai.upload_file(path=path_temp)
                    # Aguarda o processamento do arquivo no Google
                    while file_upload.state.name == "PROCESSING":
                        time.sleep(2)
                        file_upload = genai.get_file(file_upload.name)
                    
                    conteudo_para_ia = [file_upload, "Analise este arquivo e crie um quiz em português."]
                    st.success("Arquivo pronto para processamento!")
                except Exception as e:
                    st.error(f"Erro no upload: {e}")
                finally:
                    if os.path.exists(path_temp):
                        os.remove(path_temp)

    # --- Botão de Geração ---
    if st.button("✨ Gerar Questionário", type="primary"):
        if not conteudo_para_ia:
            st.error("Adicione um link com legendas ou faça upload de um arquivo.")
        else:
            with st.spinner("IA Gerando questões..."):
                prompt = """
                Crie um questionário com:
                - 05 questões de múltipla escolha (A, B, C, D).
                - Use Markdown: ## para perguntas.
                - Resposta correta em negrito ao final de cada questão.
                - Tudo em PORTUGUÊS.
                """
                try:
                    # Unifica o conteúdo (seja texto ou arquivo) com o prompt
                    final_content = conteudo_para_ia + [prompt] if isinstance(conteudo_para_ia, list) else [conteudo_para_ia, prompt]
                    response = model.generate_content(final_content)
                    
                    st.markdown("---")
                    st.markdown(response.text)
                    st.download_button("📥 Baixar Quiz", response.text, file_name="quiz.md")
                except Exception as e:
                    st.error(f"Erro ao gerar: {e}")
else:
    st.info("Aguardando API Key para iniciar...")

st.divider()
st.caption("Nota: Se o vídeo do YouTube não tiver legendas, baixe-o e use a aba de Upload.")
