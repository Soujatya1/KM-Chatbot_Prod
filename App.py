import streamlit as st
import boto3
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import os
import json

st.title("Knowledge Management Chatbot")

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

aws_access_key = "YOUR_AWS_ACCESS_KEY"
aws_secret_key = "YOUR_AWS_SECRET_KEY"
region_name = "YOUR_AWS_REGION"


client = boto3.client(
    'bedrock-runtime',
    region_name=region_name,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

s3 = boto3.client('s3', region_name=region_name)
bucket_name = 'your-s3-bucket-name'
file_key = 'path/to/your/document.pdf'


def download_from_s3(bucket_name, file_key, download_path):
    try:
        s3.download_file(bucket_name, file_key, download_path)
        st.success(f"File {file_key} downloaded from S3 successfully!")
    except Exception as e:
        st.error(f"Error downloading file from S3: {e}")


download_path = "C:/Users/Documents"
download_from_s3(bucket_name, file_key, download_path)


if os.path.exists(download_path):

    loader = PyPDFLoader(download_path)
    docs = loader.load()


    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=15)
    documents = text_splitter.split_documents(docs)


    hf_embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")


    vector_db = FAISS.from_documents(documents, hf_embedding)


    def call_aws_llm(prompt, chat_history):
        try:
            response = client.invoke_model(
                modelId="your-aws-llm-model-id",
                body=json.dumps({
                    "input": prompt,
                    "chat_history": chat_history
                }),
                contentType="application/json"
            )
            result = json.loads(response['body'])
            return result['generated_text']
        except Exception as e:
            st.error(f"Error calling AWS LLM: {e}")
            return None


    user_question = st.text_input("Ask a question about the relevant document", key="input")

    if user_question:

        conversation_history = ""
        for chat in st.session_state['chat_history']:
            conversation_history += f"You: {chat['user']}\nBot: {chat['bot']}\n"


        prompt = f"Context: {docs}\nConversation History: {conversation_history}\nQuestion: {user_question}"


        response = call_aws_llm(prompt, conversation_history)

        if response:

            st.session_state.chat_history.append({"user": user_question, "bot": response})


    if st.session_state['chat_history']:
        for chat in st.session_state['chat_history']:
            st.markdown(f"<div style='padding: 10px; border-radius: 10px;'><strong>You:</strong> {chat['user']}<br/><strong>Bot:</strong> {chat['bot']}</div>", unsafe_allow_html=True)
