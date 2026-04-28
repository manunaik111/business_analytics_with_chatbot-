# chatbot_engine.py
# Team 5 — Integration & Interface
# AI Sales Chatbot using Groq API with Memory System

import sys
import os
import streamlit as st
from groq import Groq

# ── Fix import paths ──────────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from nlp.preprocessing import preprocess
from nlp.intent_classifier import predict_intent
from nlp.entity_extractor import extract_entities
from analytics.analysis import RetailDataAnalyzer

# ── Groq client ───────────────────────────────────────────────────────
client   = Groq(api_key=st.secrets["AI_API_KEY"])
AI_MODEL = "llama-3.1-8b-instant"

# ── Load dataset once ─────────────────────────────────────────────────
@st.cache_resource
def get_analyzer():
    analyzer = RetailDataAnalyzer(
        filepath=os.path.join(
            os.path.dirname(__file__), '..', 'data', 'SALES_DATA_SETT.csv'
        )
    )
    analyzer.load_and_validate_data()
    # Keep original dataset row count for dashboard totals.
    # main_app handles any lightweight normalization it needs.
    analyzer.calculate_features()
    return analyzer

# ── Build system prompt once ──────────────────────────────────────────
@st.cache_data
def build_system_prompt():
    analyzer = get_analyzer()
    df       = analyzer.df

    total_sales    = df['Sales'].sum()
    total_profit   = df['Profit'].sum()
    total_orders   = len(df)
    region_sales   = df.groupby('Region')['Sales'].sum().to_dict()
    category_sales = df.groupby('Category')['Sales'].sum().to_dict()
    cat_profit     = df.groupby('Category')['Profit'].sum().to_dict()
    top_products   = df.groupby('Product Name')['Sales'].sum().nlargest(5).to_dict()
    seg_sales      = df.groupby('Segment')['Sales'].sum().to_dict()

    # Monthly trend
    if 'Order Date' in df.columns:
        df['Month']  = df['Order Date'].dt.to_period('M')
        monthly      = df.groupby('Month')['Sales'].sum().tail(12).to_dict()
        monthly_text = "\n".join([f"  - {str(m)}: ${s:,.0f}" for m, s in monthly.items()])
    else:
        monthly_text = "  - Monthly data not available"

    region_text   = "\n".join([f"  - {r}: ${s:,.0f}" for r, s in region_sales.items()])
    category_text = "\n".join([f"  - {c}: Sales ${s:,.0f}, Profit ${cat_profit[c]:,.0f}" for c, s in category_sales.items()])
    product_text  = "\n".join([f"  - {p}: ${s:,.0f}" for p, s in top_products.items()])
    segment_text  = "\n".join([f"  - {s}: ${v:,.0f}" for s, v in seg_sales.items()])

    return f"""You are a friendly and knowledgeable AI Sales Assistant. Think of yourself as a helpful colleague who knows the company's sales data inside and out — approachable, clear, and always ready to help.

You have complete knowledge of the sales dataset below. Use it confidently to answer questions in a warm, conversational tone. Feel free to add a brief insight or helpful context when it adds value.

DATASET FACTS:
- Total Sales:  ${total_sales:,.0f}
- Total Profit: ${total_profit:,.0f}
- Total Orders: {total_orders:,}

SALES BY REGION:
{region_text}

SALES BY CATEGORY (Sales and Profit):
{category_text}

TOP 5 PRODUCTS BY SALES:
{product_text}

SALES BY CUSTOMER SEGMENT:
{segment_text}

MONTHLY SALES TREND (Last 12 Months):
{monthly_text}

GUIDELINES:
- Be warm, friendly, and conversational — like a helpful colleague, not a robot
- Always answer directly and confidently using the numbers above
- Never say you cannot find or see the data — it's all right here
- Lead with the actual answer, then add context or a quick insight if useful
- Use the full conversation history to handle follow-up questions naturally (e.g. "that region", "it", "there")
- Always include specific numbers, formatted with commas and dollar signs
- Keep answers clear and easy to read — avoid overly long or overly short replies
- If asked something outside of sales data, say: "I'm only set up to help with questions about the company's sales data — but feel free to ask me anything about that!" """

# ── Initialize memory ─────────────────────────────────────────────────
def initialize_memory():
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False

# ── Map intent to analytics ───────────────────────────────────────────
def get_analytics_for_intent(intent, analyzer):
    try:
        if intent == "Ranking Query":
            return str(analyzer.product_analysis())
        elif intent in ("Sales Query", "Profit Query"):
            return str(analyzer.calculate_kpis())
        elif intent in ("Comparison Query", "Regional Query"):
            return str(analyzer.regional_analysis())
        elif intent == "Category Query":
            return str(analyzer.category_analysis())
        elif intent == "Trend Query":
            df = analyzer.df
            if 'Order Date' in df.columns:
                df['Month'] = df['Order Date'].dt.to_period('M')
                monthly     = df.groupby('Month')['Sales'].sum().tail(12)
                return f"Monthly sales trend:\n{monthly.to_string()}"
            return None
        elif intent == "Segment Query":
            return str(analyzer.customer_analysis())
        else:
            return None
    except Exception:
        return None

# ── Main chat function ────────────────────────────────────────────────
def chat(user_message):
    initialize_memory()

    if st.session_state.is_processing:
        return None

    st.session_state.is_processing = True

    try:
        # Step 1 — Preprocess
        try:
            clean_text = preprocess(user_message)
        except Exception:
            clean_text = user_message

        # Step 2 — NLP intent and entities
        try:
            intent   = predict_intent(clean_text)
            analyzer = get_analyzer()
            entities = extract_entities(
                clean_text,
                analyzer.df['Product Name'].unique().tolist()
            )
        except Exception:
            intent   = None
            analyzer = get_analyzer()

        # Step 3 — Analytics data
        try:
            analytics_data = get_analytics_for_intent(intent, analyzer)
        except Exception:
            analytics_data = None

        # Step 4 — Build full message
        if analytics_data:
            full_message = (
                f"{user_message}\n\n"
                f"[Relevant Data from Dataset]: {str(analytics_data)[:800]}"
            )
        else:
            full_message = user_message

        # Step 5 — Build Groq messages list
        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]
        for msg in st.session_state.conversation_history:
            messages.append({
                "role":    msg['role'],
                "content": msg['content']
            })
        messages.append({
            "role":    "user",
            "content": full_message
        })

        # Step 6 — Call Groq API
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        )
        ai_reply = response.choices[0].message.content

        # Step 7 — Store in history
        st.session_state.conversation_history.append({
            'role': 'user', 'content': full_message
        })
        st.session_state.conversation_history.append({
            'role': 'assistant', 'content': ai_reply
        })

        return ai_reply

    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

    finally:
        st.session_state.is_processing = False

# ── Clear memory ──────────────────────────────────────────────────────
def clear_memory():
    st.session_state.conversation_history = []
    st.session_state.chat_messages        = []
    st.session_state.is_processing        = False