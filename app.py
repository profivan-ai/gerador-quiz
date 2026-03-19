import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# Configuração da Página
st.set_page_config(page_title="Gerador de Quiz IA", page_icon="🎓")
st.title("🎓 Gerador de Quiz por Arquivo")
st.markdown("Suba um vídeo ou áudio para que a IA crie um questionário personalizado.")

# --- Barra Lateral (Configurações) ---
st.sidebar.header("⚙️ Configurações do Quiz")

# Input da API Key (Segurança)
api_key_input = st.sidebar.text_input("Gemini API Key:", type="password", help="Pegue sua chave em aistudio.google.com")

# Parâmetros do Quiz
num_questoes = st.sidebar.slider("Número de questões:", min_value=1, max_value=15, value=5)
dificuldade = st.sidebar.selectbox("Nível de dificuldade:", ["Fácil", "Intermediário", "Difícil"])

# --- Área de Upload ---
st.info("💡 Formatos suportados: MP4, MP3, WAV, M4A")
arquivo_usuario = st.file_uploader("Escolha o arquivo de vídeo ou áudio:", type=["mp4", "mp3", "wav", "m4a"])

if arquivo_usuario:
    if not api_key_input:
        st.error("⚠️ Por favor, insira sua API Key na barra lateral para continuar.")
    else:
        # Configura a IA
        genai.configure(api_key=api_key_input)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Botão para Iniciar Processamento
        if st.button("✨ Gerar Questionário", type="primary"):
            try:
                # 1. Salva arquivo temporário
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{arquivo_usuario.name.split('.')[-1]}") as tmp:
                    tmp.write(arquivo_usuario.read())
                    path_temp = tmp.name

                with st.status("Processando conteúdo...") as status:
                    # 2. Upload para o Google
                    status.update(label="Fazendo upload para o servidor da IA...", state="running")
                    file_ai = genai.upload_file(path=path_temp)

                    # 3. Aguarda processamento do arquivo
                    while file_ai.state.name == "PROCESSING":
                        time.sleep(2)
                        file_ai = genai.get_file(file_ai.name)
                    
                    if file_ai.state.name == "FAILED":
                        raise Exception("Falha no processamento do arquivo pelo Google.")

                    # 4. Geração do conteúdo
                    status.update(label=f"Criando {num_questoes} questões nível {dificuldade}...", state="running")
                    
                    prompt = f"""
                    Analise o arquivo de áudio/vídeo enviado e crie um questionário:
                    - Idioma: Português.
                    - Quantidade: {num_questoes} questões de múltipla escolha.
                    - Dificuldade: Nível {dificuldade}.
                    - Formato: Markdown com '##' para perguntas e opções A, B, C, D.
                    - Gabarito: Indique a resposta correta em **negrito** ao final de cada questão com uma breve explicação do porquê.
                    """

                    response = model.generate_content([file_ai, prompt])
                    
                    status.update(label="Quiz gerado com sucesso!", state="complete")

                # Exibição do Resultado
                st.markdown("---")
                st.markdown(response.text)
                
                # Botão de Download
                st.download_button(
                    label="📥 Baixar Questionário (.md)",
                    data=response.text,
                    file_name=f"quiz_{dificuldade}.md",
                    mime="text/markdown"
                )

            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")
            
            finally:
                # Limpeza de segurança
                if 'path_temp' in locals() and os.path.exists(path_temp):
                    os.remove(path_temp)

st.divider()
st.caption("Nota: O tempo de geração depende do tamanho do arquivo enviado.")
