from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
load_dotenv()


tier1_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0.0,thinking_budget=1024,include_thoughts=False)
tier1_groq = init_chat_model("groq:llama-3.3-70b-versatile",temperature=0.0) # fallback
smart_llm = tier1_gemini.with_fallbacks([tier1_groq]) # choosing between models

tier2_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite",temperature=0.0,thinking_budget=1024)
tier2_groq = init_chat_model("groq:llama-3.3-70b-versatile",temperature=0.0) # fallback
fast_llm = tier2_gemini.with_fallbacks([tier2_groq])
