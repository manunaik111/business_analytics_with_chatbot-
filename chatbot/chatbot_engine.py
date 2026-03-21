# chatbot_engine.py
# Team 5 — Integration & Interface
# Fixed: all intents mapped, strict off-topic redirect, proper memory clear

import sys
import os
import streamlit as st
from groq import Groq

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
    analyzer.clean_data()
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
        df['Month'] = df['Order Date'].dt.to_period('M')
        monthly     = df.groupby('Month')['Sales'].sum().tail(12).to_dict()
        monthly_text = "\n".join([f"  - {str(m)}: ${s:,.0f}" for m, s in monthly.items()])
    else:
        monthly_text = "  - Monthly data not available"

    region_text   = "\n".join([f"  - {r}: ${s:,.0f}" for r, s in region_sales.items()])
    category_text = "\n".join([f"  - {c}: Sales ${s:,.0f}, Profit ${cat_profit[c]:,.0f}" for c, s in category_sales.items()])
    product_text  = "\n".join([f"  - {p}: ${s:,.0f}" for p, s in top_products.items()])
    segment_text  = "\n".join([f"  - {s}: ${v:,.0f}" for s, v in seg_sales.items()])

    return f"""You are an AI Sales Assistant for a company. You ONLY answer questions about the company sales data below. You MUST refuse any question not related to this sales data — including weather, general knowledge, coding, or any other topic. For off-topic questions respond with exactly: "I can only help with questions about the company sales data. Please ask me about sales, profits, regions, products, or trends."

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

RULES:
- Only answer questions about the sales data above
- Use conversation history for follow-up questions
- Always include specific numbers
- Keep answers concise and professional
- For off-topic questions use the exact refusal message above"""

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
            result = analyzer.product_analysis()
            return str(result)
        elif intent in ("Sales Query", "Profit Query"):
            result = analyzer.calculate_kpis()
            return str(result)
        elif intent in ("Comparison Query", "Regional Query"):
            result = analyzer.regional_analysis()
            return str(result)
        elif intent == "Category Query":
            result = analyzer.category_analysis()
            return str(result)
        elif intent == "Trend Query":
            df = analyzer.df
            if 'Order Date' in df.columns:
                df['Month'] = df['Order Date'].dt.to_period('M')
                monthly = df.groupby('Month')['Sales'].sum().tail(12)
                return f"Monthly sales trend:\n{monthly.to_string()}"
            return None
        elif intent == "Segment Query":
            result = analyzer.customer_analysis()
            return str(result)
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

        # Step 2 — NLP
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

        # Step 3 — Analytics
        try:
            analytics_data = get_analytics_for_intent(intent, analyzer)
        except Exception:
            analytics_data = None

        # Step 4 — Build message
        if analytics_data:
            full_message = (
                f"{user_message}\n\n"
                f"[Relevant Data]: {str(analytics_data)[:800]}"
            )
        else:
            full_message = user_message

        # Step 5 — Build messages list for Groq
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

        # Step 6 — Call Groq
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

# ── Clear memory completely ───────────────────────────────────────────
def clear_memory():
    st.session_state.conversation_history = []
    st.session_state.chat_messages        = []
    st.session_state.is_processing        = False