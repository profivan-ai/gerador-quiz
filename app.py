import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# Configuração da Página
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓")
st.title("🎓 Gerador de Quiz Profissional")

# --- BUSCANDO A CHAVE DOS SECRETS ---
# O Streamlit busca automaticamente no arquivo secrets.toml ou nas configurações da nuvem
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("Erro: API Key não encontrada nos Secrets do Streamlit.")
    st.stop() # Interrompe o app se a chave não estiver configurada

# --- Barra Lateral (Configurações) ---
st.sidebar.header("⚙️ Configurações do Quiz")
num_questoes = st.sidebar.slider("Número de questões:", min_value=1, max_value=15, value=5)
dificuldade = st.sidebar.selectbox("Nível de dificuldade:", ["Fácil", "Intermediário", "Difícil"])

# --- Área de Upload ---
arquivo_usuario = st.file_uploader("Suba o arquivo de vídeo ou áudio (MP4, MP3, WAV):", type=["mp4", "mp3", "wav", "m4a"])

if arquivo_usuario:
    if st.button("✨ Gerar Questionário Agora", type="primary"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{arquivo_usuario.name.split('.')[-1]}") as tmp:
                tmp.write(arquivo_usuario.read())
                path_temp = tmp.name

            with st.status("Processando conteúdo com IA...") as status:
                status.update(label="Enviando arquivo para o Google...", state="running")
                file_ai = genai.upload_file(path=path_temp)

                # Loop de verificação de processamento
                while file_ai.state.name == "PROCESSING":
                    time.sleep(2)
                    file_ai = genai.get_file(file_ai.name)
                
                status.update(label=f"Criando {num_questoes} questões ({dificuldade})...", state="running")
                
                prompt = f"""
                Analise o arquivo enviado e crie um quiz em Português:
                - {num_questoes} questões de múltipla escolha.
                - Nível: {dificuldade}.
                - Formato: Markdown (## para perguntas).
                - Gabarito: Resposta correta em **negrito** e uma breve explicação.
                """

                response = model.generate_content([file_ai, prompt])
                status.update(label="Pronto!", state="complete")

            st.markdown("---")
            st.markdown(response.text)
            
            st.download_button("📥 Baixar Quiz (.md)", response.text, file_name="quiz.md")

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
        finally:
            if 'path_temp' in locals() and os.path.exists(path_temp):
                os.remove(path_temp)

st.divider()
st.caption("Segurança: Sua API Key está protegida via Streamlit Secrets.")
