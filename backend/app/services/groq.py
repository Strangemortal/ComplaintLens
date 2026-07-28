import os
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """
    Initializes and returns the ChatLLM client based on configured environment variables.
    Supports Groq (default) and Google Gemini (fallback).
    """
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if groq_key:
        return ChatGroq(
            temperature=0,
            model="llama-3.3-70b-versatile",
            groq_api_key=groq_key
        )
    elif gemini_key:
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            google_api_key=gemini_key
        )
    else:
        # Return a dummy class or raise ValueError. 
        # Let's raise ValueError to guide the user to fill the .env.
        raise ValueError("Missing API Keys! Please configure GROQ_API_KEY or GEMINI_API_KEY in backend/.env")
