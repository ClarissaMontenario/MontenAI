

import streamlit as st

import os
import json

from pathlib import Path

import textwrap



from src.document_loader import load_pdf

from src.text_splitter import split_documents

from src.document_manager import save_uploaded_file

from src.vector_store import (

          add_documents,

          list_documents,

          delete_document,

          get_collection_count

)

from src.rag_pipeline import ask_question





# ==================================================

# CONFIGURAÇÃO

# ==================================================



PROJECT_ROOT = Path(__file__).resolve().parent

LOGO_PATH = PROJECT_ROOT / "assets" / "montenai_logo.png"



st.set_page_config(

          page_title="MontenAI | Intelligent Document Assistant",

          page_icon="✦",

          layout="wide",

          initial_sidebar_state="expanded"

)




# ==================================================
# LANGUAGE PREFERENCE
# ==================================================
LANGUAGES = {
    "Português (Brasil)": "pt",
    "English": "en",
    "Español": "es",
    "Français": "fr",
}
LANGUAGE_INSTRUCTIONS = {
    "pt": "Portuguese (Brazil)", "en": "English",
    "es": "Spanish", "fr": "French"
}
SETTINGS_PATH = PROJECT_ROOT / "montenai_settings.json"

def load_saved_language():
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
                saved = json.load(file)
            for label, code in LANGUAGES.items():
                if code == saved.get("language", "pt"):
                    return label
    except Exception:
        pass
    return "Português (Brasil)"

if "language_choice" not in st.session_state:
    st.session_state.language_choice = load_saved_language()

def save_language():
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as file:
            json.dump({"language": LANGUAGES[st.session_state.language_choice]},
                      file, ensure_ascii=False, indent=2)
    except Exception:
        pass

TRANSLATIONS = {'Navigation': {'pt': 'Navegação', 'es': 'Navegación', 'fr': 'Navigation'}, 'Chat': {'pt': 'Conversa', 'es': 'Chat', 'fr': 'Discussion'}, 'Document Library': {'pt': 'Biblioteca de documentos', 'es': 'Biblioteca de documentos', 'fr': 'Bibliothèque de documents'}, 'Evaluation Dashboard': {'pt': 'Painel de avaliação', 'es': 'Panel de evaluación', 'fr': 'Tableau d’évaluation'}, 'Settings': {'pt': 'Configurações', 'es': 'Configuración', 'fr': 'Paramètres'}, 'Language': {'pt': 'Idioma', 'es': 'Idioma', 'fr': 'Langue'}, 'Choose your language': {'pt': 'Escolha seu idioma', 'es': 'Elige tu idioma', 'fr': 'Choisissez votre langue'}, 'UPLOAD DOCUMENTS': {'pt': 'ENVIAR DOCUMENTOS', 'es': 'SUBIR DOCUMENTOS', 'fr': 'IMPORTER DES DOCUMENTS'}, 'Drag and drop PDF files': {'pt': 'Arraste e solte arquivos PDF', 'es': 'Arrastra y suelta archivos PDF', 'fr': 'Glissez-déposez des fichiers PDF'}, 'PDF only · Upload your documents to start': {'pt': 'Somente PDF · Envie documentos para começar', 'es': 'Solo PDF · Sube documentos para comenzar', 'fr': 'PDF uniquement · Importez vos documents pour commencer'}, 'Process Documents': {'pt': 'Processar documentos', 'es': 'Procesar documentos', 'fr': 'Traiter les documents'}, 'Select at least one PDF document.': {'pt': 'Selecione pelo menos um documento PDF.', 'es': 'Selecciona al menos un documento PDF.', 'fr': 'Sélectionnez au moins un document PDF.'}, 'YOUR DOCUMENTS': {'pt': 'SEUS DOCUMENTOS', 'es': 'TUS DOCUMENTOS', 'fr': 'VOS DOCUMENTS'}, 'No documents uploaded yet.': {'pt': 'Nenhum documento enviado ainda.', 'es': 'Aún no has subido documentos.', 'fr': 'Aucun document importé pour le moment.'}, 'documents': {'pt': 'documentos', 'es': 'documentos', 'fr': 'documents'}, 'text chunks': {'pt': 'trechos de texto', 'es': 'fragmentos de texto', 'fr': 'segments de texte'}, 'Documents processed · Ready to answer questions': {'pt': 'Documentos processados · Pronto para responder perguntas', 'es': 'Documentos procesados · Listo para responder preguntas', 'fr': 'Documents traités · Prêt à répondre aux questions'}, 'Upload documents to begin.': {'pt': 'Envie documentos para começar.', 'es': 'Sube documentos para comenzar.', 'fr': 'Importez des documents pour commencer.'}, 'Clear conversation': {'pt': 'Limpar conversa', 'es': 'Borrar conversación', 'fr': 'Effacer la conversation'}, 'Chat with your documents': {'pt': 'Converse com seus documentos', 'es': 'Chatea con tus documentos', 'fr': 'Discutez avec vos documents'}, '{tr("{tr("Get accurate answers from your PDFs using Retrieval-Augmented Generation.")}")}': {'pt': 'Obtenha respostas precisas dos seus PDFs com geração aumentada por recuperação.', 'es': 'Obtén respuestas precisas de tus PDF mediante generación aumentada por recuperación.', 'fr': 'Obtenez des réponses précises à partir de vos PDF grâce à la génération augmentée par récupération.'}, 'Find information': {'pt': 'Encontre informações', 'es': 'Encuentra información', 'fr': 'Trouver des informations'}, 'Search across your documents': {'pt': 'Pesquise em seus documentos', 'es': 'Busca en tus documentos', 'fr': 'Rechercher dans vos documents'}, 'Reliable answers': {'pt': 'Respostas confiáveis', 'es': 'Respuestas fiables', 'fr': 'Réponses fiables'}, 'Grounded in your content': {'pt': 'Baseadas no seu conteúdo', 'es': 'Basadas en tu contenido', 'fr': 'Fondées sur votre contenu'}, 'Cite sources': {'pt': 'Cite as fontes', 'es': 'Cita las fuentes', 'fr': 'Citer les sources'}, 'See document and page references': {'pt': 'Veja referências de documentos e páginas', 'es': 'Consulta referencias de documentos y páginas', 'fr': 'Consultez les références des documents et des pages'}, 'Select documents to search': {'pt': 'Selecione os documentos para pesquisar', 'es': 'Selecciona los documentos para buscar', 'fr': 'Sélectionnez les documents à rechercher'}, 'Documents': {'pt': 'Documentos', 'es': 'Documentos', 'fr': 'Documents'}, 'Upload and process a PDF document in the sidebar to start.': {'pt': 'Envie e processe um PDF na barra lateral para começar.', 'es': 'Sube y procesa un PDF en la barra lateral para comenzar.', 'fr': 'Importez et traitez un PDF dans la barre latérale pour commencer.'}, 'Suggested questions': {'pt': 'Perguntas sugeridas', 'es': 'Preguntas sugeridas', 'fr': 'Questions suggérées'}, 'Summarize this document': {'pt': 'Resuma este documento', 'es': 'Resume este documento', 'fr': 'Résumer ce document'}, 'Summarize the selected documents.': {'pt': 'Resuma os documentos selecionados.', 'es': 'Resume los documentos seleccionados.', 'fr': 'Résumez les documents sélectionnés.'}, 'What are the main topics?': {'pt': 'Quais são os principais tópicos?', 'es': '¿Cuáles son los temas principales?', 'fr': 'Quels sont les principaux sujets ?'}, 'What are the main topics covered in the selected documents?': {'pt': 'Quais são os principais tópicos abordados nos documentos selecionados?', 'es': '¿Cuáles son los temas principales de los documentos seleccionados?', 'fr': 'Quels sont les principaux sujets abordés dans les documents sélectionnés ?'}, 'Find important information': {'pt': 'Encontre informações importantes', 'es': 'Encuentra información importante', 'fr': 'Trouver les informations importantes'}, 'What are the most important pieces of information?': {'pt': 'Quais são as informações mais importantes?', 'es': '¿Cuáles son las informaciones más importantes?', 'fr': 'Quelles sont les informations les plus importantes ?'}, 'Ask a question about your documents...': {'pt': 'Faça uma pergunta sobre seus documentos...', 'es': 'Haz una pregunta sobre tus documentos...', 'fr': 'Posez une question sur vos documents...'}, 'Upload and select at least one document.': {'pt': 'Envie e selecione pelo menos um documento.', 'es': 'Sube y selecciona al menos un documento.', 'fr': 'Importez et sélectionnez au moins un document.'}, 'Analyzing your documents...': {'pt': 'Analisando seus documentos...', 'es': 'Analizando tus documentos...', 'fr': 'Analyse de vos documents...'}, 'Sources and references': {'pt': 'Fontes e referências', 'es': 'Fuentes y referencias', 'fr': 'Sources et références'}, 'Document': {'pt': 'Documento', 'es': 'Documento', 'fr': 'Document'}, 'Page': {'pt': 'Página', 'es': 'Página', 'fr': 'Page'}, 'An error occurred:': {'pt': 'Ocorreu um erro:', 'es': 'Ocurrió un error:', 'fr': 'Une erreur s’est produite :'}, 'MontenAI uses the content of your uploaded documents to generate answers.': {'pt': 'O MontenAI utiliza o conteúdo dos documentos enviados para gerar respostas.', 'es': 'MontenAI utiliza el contenido de los documentos que subes para generar respuestas.', 'fr': 'MontenAI utilise le contenu des documents importés pour générer des réponses.'}, 'Manage the PDF documents stored in MontenAI.': {'pt': 'Gerencie os documentos PDF armazenados no MontenAI.', 'es': 'Administra los documentos PDF almacenados en MontenAI.', 'fr': 'Gérez les documents PDF stockés dans MontenAI.'}, 'Delete': {'pt': 'Excluir', 'es': 'Eliminar', 'fr': 'Supprimer'}, 'Your document library is empty.': {'pt': 'Sua biblioteca de documentos está vazia.', 'es': 'Tu biblioteca de documentos está vacía.', 'fr': 'Votre bibliothèque de documents est vide.'}, 'Monitor the performance of your RAG system.': {'pt': 'Acompanhe o desempenho do seu sistema RAG.', 'es': 'Supervisa el rendimiento de tu sistema RAG.', 'fr': 'Suivez les performances de votre système RAG.'}, 'The evaluation dashboard is available in the separate dashboard.py application.': {'pt': 'O painel de avaliação está disponível no aplicativo separado dashboard.py.', 'es': 'El panel de evaluación está disponible en la aplicación independiente dashboard.py.', 'fr': 'Le tableau d’évaluation est disponible dans l’application séparée dashboard.py.'}, 'MontenAI application information.': {'pt': 'Informações sobre o aplicativo MontenAI.', 'es': 'Información sobre la aplicación MontenAI.', 'fr': 'Informations sur l’application MontenAI.'}, 'INTELLIGENT DOCUMENT ASSISTANT': {'pt': 'ASSISTENTE INTELIGENTE DE DOCUMENTOS', 'es': 'ASISTENTE INTELIGENTE DE DOCUMENTOS', 'fr': 'ASSISTANT INTELLIGENT DE DOCUMENTS'}, 'Processing': {'pt': 'Processando', 'es': 'Procesando', 'fr': 'Traitement'}, 'is already indexed.': {'pt': 'já está indexado.', 'es': 'ya está indexado.', 'fr': 'est déjà indexé.'}, 'No text extracted from': {'pt': 'Nenhum texto extraído de', 'es': 'No se extrajo texto de', 'fr': 'Aucun texte extrait de'}, 'No chunks generated from': {'pt': 'Nenhum trecho gerado para', 'es': 'No se generaron fragmentos para', 'fr': 'Aucun segment généré pour'}, 'chunks saved.': {'pt': 'trechos salvos.', 'es': 'fragmentos guardados.', 'fr': 'segments enregistrés.'}, 'No chunks were inserted.': {'pt': 'Nenhum trecho foi inserido.', 'es': 'No se insertaron fragmentos.', 'fr': 'Aucun segment n’a été inséré.'}, 'Error processing': {'pt': 'Erro ao processar', 'es': 'Error al procesar', 'fr': 'Erreur lors du traitement de'}, 'Processing finished.': {'pt': 'Processamento concluído.', 'es': 'Procesamiento finalizado.', 'fr': 'Traitement terminé.'}, 'Documents added:': {'pt': 'Documentos adicionados:', 'es': 'Documentos añadidos:', 'fr': 'Documents ajoutés :'}, 'Total chunks in database:': {'pt': 'Total de trechos no banco de dados:', 'es': 'Total de fragmentos en la base de datos:', 'fr': 'Nombre total de segments dans la base de données :'}, 'chunks': {'pt': 'trechos', 'es': 'fragmentos', 'fr': 'segments'}, 'Chunks:': {'pt': 'Trechos:', 'es': 'Fragmentos:', 'fr': 'Segments :'}}


TRANSLATIONS.update({
    "Delete document": {
        "pt": "Excluir documento",
        "es": "Eliminar documento",
        "fr": "Supprimer le document"
    }
})

TRANSLATIONS.update({
    "Get accurate answers from your PDFs using Retrieval-Augmented Generation.": {
        "pt": "Obtenha respostas precisas dos seus PDFs com geração aumentada por recuperação.",
        "es": "Obtén respuestas precisas de tus PDF mediante generación aumentada por recuperación.",
        "fr": "Obtenez des réponses précises à partir de vos PDF grâce à la génération augmentée par récupération."
    },
    "Online": {"pt": "Online", "es": "En línea", "fr": "En ligne"},
    "Find information": {"pt": "Encontre informações", "es": "Encuentra información", "fr": "Trouver des informations"},
    "Reliable answers": {"pt": "Respostas confiáveis", "es": "Respuestas fiables", "fr": "Réponses fiables"},
    "Cite sources": {"pt": "Cite as fontes", "es": "Cita las fuentes", "fr": "Citer les sources"},
    "Select documents to search": {"pt": "Selecione os documentos para pesquisar", "es": "Selecciona los documentos para buscar", "fr": "Sélectionnez les documents à rechercher"},
    "Suggested questions": {"pt": "Perguntas sugeridas", "es": "Preguntas sugeridas", "fr": "Questions suggérées"},
    "Search across your documents": {"pt": "Pesquise em seus documentos", "es": "Busca en tus documentos", "fr": "Rechercher dans vos documents"},
    "Grounded in your content": {"pt": "Baseadas no seu conteúdo", "es": "Basadas en tu contenido", "fr": "Fondées sur votre contenu"},
    "See document and page references": {"pt": "Veja referências de documentos e páginas", "es": "Consulta referencias de documentos y páginas", "fr": "Consultez les références des documents et des pages"},
    "Upload documents to begin.": {"pt": "Envie documentos para começar.", "es": "Sube documentos para comenzar.", "fr": "Importez des documents pour commencer."},
    "UPLOAD DOCUMENTS": {"pt": "ENVIAR DOCUMENTOS", "es": "SUBIR DOCUMENTOS", "fr": "IMPORTER DES DOCUMENTS"},
    "YOUR DOCUMENTS": {"pt": "SEUS DOCUMENTOS", "es": "TUS DOCUMENTOS", "fr": "VOS DOCUMENTS"},
    "NAVIGATION": {"pt": "NAVEGAÇÃO", "es": "NAVEGACIÓN", "fr": "NAVIGATION"},
})

TRANSLATIONS.update({
    "Documents processed": {
        "pt": "Documentos processados",
        "es": "Documentos procesados",
        "fr": "Documents traités"
    },
    "Text chunks": {
        "pt": "Trechos de texto",
        "es": "Fragmentos de texto",
        "fr": "Segments de texte"
    }
})

def tr(text):
    code = LANGUAGES[st.session_state.language_choice]
    return TRANSLATIONS.get(text, {}).get(code, text)

if "messages" not in st.session_state:

          st.session_state.messages = []





# ==================================================

# IDENTIDADE VISUAL

# ==================================================



st.markdown("""

<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');



html, body, [class*="css"] {

          font-family: 'DM Sans', sans-serif;

          color: #171638;

}



.stApp {

          background: #FAF9FC;

}



.block-container {

          padding-top: 1.5rem;

          padding-bottom: 2rem;

          max-width: 1500px;

}



#MainMenu, footer {

          visibility: hidden;

}



header[data-testid="stHeader"] {

          background: transparent;

}



/* SIDEBAR */



section[data-testid="stSidebar"] {

          background: linear-gradient(180deg, #FBF8FD 0%, #F5F0FA 100%);

          border-right: 1px solid #EEE5F5;

}



section[data-testid="stSidebar"] > div {

          padding: 1.2rem 1rem;

}



section[data-testid="stSidebar"] p,

section[data-testid="stSidebar"] label,

section[data-testid="stSidebar"] span {

          color: #252044;

}



.sidebar-section {

          color: #31264D;

          font-size: 13px;

          font-weight: 700;

          margin: 18px 0 10px 4px;

}



/* TÍTULOS */



h1, h2, h3 {

          color: #171638 !important;

}



/* BOTÕES */



.stButton > button {

          border-radius: 10px;

          border: 1px solid #E7D8F1;

          background: white;

          color: #6635A0;

          font-weight: 600;

          transition: 0.2s;

}



.stButton > button:hover {

          background: #F3EAF9;

          border-color: #A66BD0;

          color: #51217E;

}



.stButton > button[kind="primary"] {

          background: linear-gradient(135deg, #A64AC7, #8142B5);

          color: white;

          border: none;

}



/* UPLOAD */



[data-testid="stFileUploader"] {

          background: #FCFAFE;

          border: 1px dashed #D9C5E8;

          border-radius: 12px;

          padding: 10px;

}



/* CAMPOS */



.stTextInput input,

.stTextArea textarea {

          background: white;

          color: #252044;

          border-color: #DCCBEA;

          border-radius: 10px;

}



/* CARDS */



.info-card {

          background: white;

          border: 1px solid #EEE5F5;

          border-radius: 15px;

          padding: 20px;

}



.metric-card {

          background: white;

          border: 1px solid #EDE3F4;

          border-radius: 13px;

          padding: 15px;

          text-align: center;

}



.metric-number {

          color: #342052;

          font-size: 25px;

          font-weight: 700;

}



.metric-label {

          color: #817494;

          font-size: 12px;

}



/* CABEÇALHO */



.hero {

          background:

                    radial-gradient(circle at 90% 10%, #F1DDF5 0%, transparent 30%),

                    linear-gradient(115deg, #FFFCFE 0%, #F8F0FA 65%, #F1E7F7 100%);

          border: 1px solid #F0E5F5;

          border-radius: 17px;

          padding: 34px 30px 27px 30px;

          margin-bottom: 22px;

}



.hero-title {

          font-family: 'Playfair Display', serif;

          font-size: 35px;

          font-weight: 700;

          color: #171638;

          line-height: 1.2;

}



.hero-subtitle {

          color: #655B83;

          font-size: 14px;

          margin-top: 7px;

}



.feature-title {

          font-size: 13px;

          font-weight: 700;

          color: #272044;

}



.feature-description {

          font-size: 12px;

          color: #776B91;

}



/* CHAT */





/* CARTÕES DE CONVERSA */



[data-testid="stChatMessage"] {

          border-radius: 15px;

          padding: 18px;

          margin-bottom: 15px;

          border: 1px solid #EEE5F5;

          box-shadow: 0 2px 8px rgba(65, 35, 90, 0.03);

}



/* PERGUNTA DO USUÁRIO */



[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {

          background: linear-gradient(110deg, #F8EFFA, #F4EAF8);

          border-color: #EEDDF3;

}



/* RESPOSTA DA MONTENAI */



[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {

          background: #FFFFFF;

          border-color: #E9DDF3;

}



/* TEXTO DAS MENSAGENS */



[data-testid="stChatMessage"] p {

          color: #252044;

          font-size: 14px;

          line-height: 1.75;

}



/* FONTES */



[data-testid="stExpander"] {

          border: 1px solid #E9DDF3;

          border-radius: 10px;

          background: #FCFAFE;

}





[data-testid="stChatInput"] {

          border: 1px solid #CDA9E6;

          border-radius: 13px;

          background: white;

}



/* FONTES */



.source-box {

          background: #FAF7FC;

          border: 1px solid #EDE2F4;

          padding: 10px 13px;

          border-radius: 9px;

          color: #51406A;

          font-size: 12px;

          margin-bottom: 7px;

}



/* STATUS */



.status-online {

          color: #238D70;

          background: #E8F7F1;

          border-radius: 20px;

          padding: 6px 12px;

          font-size: 12px;

          font-weight: 600;

}



hr {

          border-color: #EEE5F3;

}



@media (max-width: 768px) {

          .hero-title {

                    font-size: 27px;

          }



          .hero {

                    padding: 23px 18px;

          }

}

</style>

""", unsafe_allow_html=True)





# ==================================================

# FUNÇÕES AUXILIARES

# ==================================================



def get_documents():

          """Retorna os documentos usando os campos do vector_store.py."""

          return list_documents()





def show_sources(sources):

          """Exibe as fontes utilizadas na resposta."""



          if not sources:

                    return



          with st.expander(tr("Sources and references")):



                    for source in sources:



                              name = (

                                        source.get("document_name")

                                        or source.get("source")

                                        or tr("Document")

                              )



                              page = source.get("page", "N/A")



                              st.markdown(

                                        f"""

                                        <div class="source-box">

                                                  <b>{name}</b> · {tr("Page")} {page}

                                        </div>

                                        """,

                                        unsafe_allow_html=True

                              )





# ==================================================

# SIDEBAR

# ==================================================



with st.sidebar:



          # LOGOTIPO



          if LOGO_PATH.exists():

                    st.image(str(LOGO_PATH), use_container_width=True)



          else:

                    st.markdown("""

                    <div style="text-align:center;padding:15px;">

                              <div style="font-family:'Playfair Display';

                                                            font-size:36px;color:#171638;">

                                        Monten<span style="color:#A17ACB;">AI</span>

                              </div>

                              <div style="font-size:9px;letter-spacing:3px;

                                                            color:#62577C;">

                                        INTELLIGENT DOCUMENT ASSISTANT

                              </div>

                    </div>

                    """, unsafe_allow_html=True)



          # NAVEGAÇÃO



          st.markdown(

                    '<div class="sidebar-section">NAVIGATION</div>',

                    unsafe_allow_html=True

          )



          st.markdown(f"**{tr('Language')}**")
          st.selectbox(
                    tr("Choose your language"),
                    options=list(LANGUAGES.keys()),
                    key="language_choice",
                    on_change=save_language,
                    label_visibility="collapsed"
          )

          st.markdown(f'<div class="sidebar-section">{tr("Navigation").upper()}</div>', unsafe_allow_html=True)
          page = st.radio(
                    tr("Navigation"),
                    [tr("Chat"), tr("Document Library"), tr("Evaluation Dashboard"), tr("Settings")],
                    label_visibility="collapsed"
          )



          st.divider()



          # UPLOAD



          st.markdown(

                    f'<div class="sidebar-section">{tr("UPLOAD DOCUMENTS")}</div>',

                    unsafe_allow_html=True

          )



          uploaded_files = st.file_uploader(

                    tr("Drag and drop PDF files"),

                    type=["pdf"],

                    accept_multiple_files=True,

                    label_visibility="collapsed",

                    key="pdf_uploader"

          )



          st.caption("PDF · Texto selecionável, páginas digitalizadas, fotos e tabelas (OCR/visão)")



          # PROCESSAMENTO DOS DOCUMENTOS



          if st.button(

                    tr("Process Documents"),

                    use_container_width=True,

                    type="primary"

          ):



                    if not uploaded_files:



                              st.warning(tr("Select at least one PDF document."))



                    else:



                              progress = st.progress(0)

                              status = st.empty()



                              existing_documents = get_documents()



                              existing_ids = {

                                        doc["document_id"]

                                        for doc in existing_documents

                              }



                              processed_count = 0

                              total_files = len(uploaded_files)



                              for index, uploaded_file in enumerate(uploaded_files):





                                        try:

                                                  status.info(f"{tr('Processing')} {uploaded_file.name}...")



                                                  # Salvar ou localizar o PDF existente

                                                  file_result = save_uploaded_file(uploaded_file)



                                                  file_path = file_result["path"]

                                                  document_id = file_result["hash"]



                                                  # Verificar se já está indexado no ChromaDB

                                                  existing_ids = {

                                                            doc["document_id"] for doc in get_documents()

                                                  }



                                                  if document_id in existing_ids:

                                                            st.warning(

                                                                      f"{uploaded_file.name} {tr('is already indexed.')}"

                                                            )



                                                  else:

                                                            # Extrair texto

                                                            ocr_progress = st.progress(0)
                                                            ocr_status = st.empty()

                                                            def update_ocr_progress(current, total, message):
                                                                      ocr_progress.progress(current / max(total, 1))
                                                                      ocr_status.caption(message)

                                                            documents_content = load_pdf(
                                                                      str(file_path),
                                                                      progress_callback=update_ocr_progress
                                                            )
                                                            ocr_status.empty()
                                                            ocr_progress.empty()



                                                            if not documents_content:

                                                                      st.error(

                                                                                f"{tr('No text extracted from')} {uploaded_file.name}."

                                                                      )

                                                                      continue



                                                            # Dividir em chunks

                                                            chunks = split_documents(documents_content)



                                                            if not chunks:

                                                                      st.error(

                                                                                f"{tr('No chunks generated from')} {uploaded_file.name}."

                                                                      )

                                                                      continue



                                                            # Salvar no ChromaDB

                                                            inserted = add_documents(

                                                                      chunks=chunks,

                                                                      document_id=document_id,

                                                                      document_name=uploaded_file.name

                                                            )



                                                            if inserted > 0:

                                                                      st.success(

                                                                                f"{uploaded_file.name}: {inserted} {tr('chunks saved.')}"

                                                                      )

                                                            else:

                                                                      st.error(tr("No chunks were inserted."))



                                                  progress.progress((index + 1) / total_files)



                                        except Exception as error:

                                                  st.error(

                                                            f"Error processing {uploaded_file.name}: {error}"

                                                  )





                                        finally:



                                                  progress.progress((index + 1) / total_files)



                              status.success(tr("Processing finished."))



                              st.write(

                                        f"{tr('Documents added:')} {processed_count}"

                              )



                              st.write(

                                        f"{tr('Total chunks in database:')} {get_collection_count()}"

                              )



          st.divider()



          # BIBLIOTECA NA SIDEBAR



          st.markdown(

                    f'<div class="sidebar-section">{tr("YOUR DOCUMENTS")}</div>',

                    unsafe_allow_html=True

          )



          documents = get_documents()



          if documents:



                    for doc in documents:



                              document_id = doc["document_id"]

                              document_name = doc["name"]

                              chunk_count = doc["chunks"]



                              col1, col2 = st.columns([5, 1])



                              with col1:



                                        st.markdown(f"**{document_name}**")
                                        st.caption(f"{chunk_count} {tr('text chunks')}")



                              with col2:



                                        if st.button(

                                                  "×",

                                                  key=f"delete_sidebar_{document_id}"

                                        ):



                                                  delete_document(document_id)

                                                  st.rerun()



          else:



                    st.caption(tr("No documents uploaded yet."))



          st.divider()



          # MÉTRICAS



          total_documents = len(documents)
          total_chunks = get_collection_count()

          col1, col2 = st.columns(2)

          with col1:
                    st.metric(
                              label=tr("Documents processed"),
                              value=total_documents
                    )

          with col2:
                    st.metric(
                              label=tr("Text chunks"),
                              value=total_chunks
                    )

          st.markdown("")



          if total_documents > 0:

                    st.success(tr("Documents processed · Ready to answer questions"))



          else:

                    st.info(tr("Upload documents to begin."))



          if st.button(tr("Clear conversation"), use_container_width=True):



                    st.session_state.messages = []

                    st.rerun()





# ==================================================

# CHAT PAGE

# ==================================================



if page == tr("Chat"):







          hero_html = (
                    f'<div class="hero">'
                    f'<div class="hero-title">{tr("Chat with your documents")}</div>'
                    f'<div class="hero-subtitle">{tr("Get accurate answers from your PDFs using Retrieval-Augmented Generation.")}</div>'
                    f'<div style="text-align:right;"><span class="status-online">● {tr("Online")}</span></div>'
                    f'</div>'
          )
          st.markdown(hero_html, unsafe_allow_html=True)



          st.markdown("")



          col1, col2, col3 = st.columns(3)



          with col1:

                    st.markdown(f"**⌕ {tr('Find information')}**")

                    st.caption(tr("Search across your documents"))



          with col2:

                    st.markdown(f"**♢ {tr('Reliable answers')}**")

                    st.caption(tr("Grounded in your content"))



          with col3:

                    st.markdown(f"**▤ {tr('Cite sources')}**")

                    st.caption(tr("See document and page references"))





          documents = get_documents()



          # SELEÇÃO DE DOCUMENTOS



          if documents:



                    st.markdown("**Select documents to search**")



                    selected_documents = st.multiselect(

                              tr("Documents"),

                              options=documents,

                              default=documents,

                              format_func=lambda doc: doc["name"],

                              key="selected_documents",

                              label_visibility="collapsed"

                    )



                    selected_ids = [

                              doc["document_id"]

                              for doc in selected_documents

                    ]



          else:



                    selected_ids = []



                    st.info(

                              tr("Upload and process a PDF document in the sidebar to start.")

                    )



          # HISTÓRICO



          for message in st.session_state.messages:



                    with st.chat_message(message["role"]):



                              st.markdown(message["content"])



                              if message["role"] == "assistant":



                                        show_sources(message.get("sources", []))



          # PERGUNTAS SUGERIDAS



          if not st.session_state.messages and documents:



                    st.markdown("**✦ Suggested questions**")



                    col1, col2, col3 = st.columns(3)



                    with col1:



                              if st.button(

                                        tr("Summarize this document"),

                                        use_container_width=True

                              ):



                                        st.session_state.pending_question = (

                                                  tr("Summarize the selected documents.")

                                        )

                                        st.rerun()



                    with col2:



                              if st.button(

                                        tr("What are the main topics?"),

                                        use_container_width=True

                              ):



                                        st.session_state.pending_question = (

                                                  tr("What are the main topics covered in the selected documents?")

                                        )

                                        st.rerun()



                    with col3:



                              if st.button(

                                        tr("Find important information"),

                                        use_container_width=True

                              ):



                                        st.session_state.pending_question = (

                                                  tr("What are the most important pieces of information?")

                                        )

                                        st.rerun()



          # CAMPO DE PERGUNTA



          question = st.chat_input(

                    tr("Ask a question about your documents...")

          )



          if "pending_question" in st.session_state:



                    question = st.session_state.pop("pending_question")



          if question:



                    if not selected_ids:



                              st.warning(

                                        tr("Upload and select at least one document.")

                              )



                    else:



                              st.session_state.messages.append({

                                        "role": "user",

                                        "content": question

                              })



                              with st.chat_message("user"):

                                        st.markdown(question)



                              with st.chat_message("assistant"):



                                        with st.spinner(tr("Analyzing your documents...")):



                                                  try:



                                                            question_for_ai = (
                                                                      f"{question}\\n\\n"
                                                                      f"IMPORTANT: Answer in {LANGUAGE_INSTRUCTIONS[LANGUAGES[st.session_state.language_choice]]}. If the user asks to translate a page or document, translate the extracted content faithfully into that language. "
                                                                      "Keep the answer grounded in the retrieved document context."
                                                            )
                                                            response = ask_question(
                                                                      question=question_for_ai,
                                                                      document_ids=selected_ids,
                                                                      chat_history=st.session_state.messages[:-1]
                                                            )



                                                            answer = response["answer"]

                                                            sources = response.get("sources", [])



                                                            st.markdown(answer)



                                                            show_sources(sources)



                                                            st.session_state.messages.append({

                                                                      "role": "assistant",

                                                                      "content": answer,

                                                                      "sources": sources

                                                            })



                                                  except Exception as error:



                                                            st.error(

                                                                      f"{tr('An error occurred:')} {error}"

                                                            )



                                                            st.session_state.messages.append({

                                                                      "role": "assistant",

                                                                      "content": f"Error: {error}",

                                                                      "sources": []

                                                            })



                              st.rerun()



          st.caption(

                    "MontenAI uses the content of your uploaded documents "

                    "to generate answers."

          )





# ==================================================

# DOCUMENT LIBRARY

# ==================================================



elif page == tr("Document Library"):



          st.title(tr("Document Library"))



          st.caption(

                    tr("Manage the PDF documents stored in MontenAI.")

          )



          documents = get_documents()



          if documents:



                    for doc in documents:



                              document_id = doc["document_id"]



                              with st.container(border=True):



                                        col1, col2 = st.columns([5, 1])



                                        with col1:



                                                  st.markdown(f"**{doc['name']}**")



                                                  st.caption(

                                                            f"ID do documento: {document_id}" if LANGUAGES[st.session_state.language_choice] == "pt" else f"Document ID: {document_id}"

                                                  )



                                                  st.caption(

                                                            f"{tr('Chunks:')} {doc['chunks']}"

                                                  )



                                        with col2:



                                                  if st.button(

                                                            tr("Delete"),

                                                            key=f"library_delete_{document_id}"

                                                  ):



                                                            delete_document(document_id)

                                                            st.rerun()



          else:



                    st.info(tr("Your document library is empty."))





# ==================================================

# EVALUATION DASHBOARD

# ==================================================



elif page == tr("Evaluation Dashboard"):



          st.title(tr("Evaluation Dashboard"))



          st.caption(

                    tr("Monitor the performance of your RAG system.")

          )



          st.info(

                    "The evaluation dashboard is available in the separate "

                    "dashboard.py application."

          )



          st.code(

                    r".\\.venv\Scripts\python.exe -m streamlit run dashboard.py --server.port 8502",

                    language="powershell"

          )





# ==================================================

# SETTINGS

# ==================================================



elif page == tr("Settings"):



          st.title(tr("Settings"))



          st.caption(

                    tr("MontenAI application information.")

          )



          st.markdown("""

          <div class="info-card">



                    <h3>MontenAI</h3>



                    <p>Intelligent Document Assistant</p>



                    <hr>



                    <b>Technology stack</b>



                    <p>

                              Python · Streamlit · Groq · ChromaDB ·

                              Retrieval-Augmented Generation

                    </p>



                    <b>Embedding model</b>



                    <p>Multilingual MiniLM</p>



          </div>

          """, unsafe_allow_html=True)
