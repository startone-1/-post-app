import streamlit as st
import requests
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from groq import Groq
import random
import json
import time

# ====================== 設定 ======================
st.set_page_config(
    page_title="X投稿支援アプリ",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded"
)

PASSWORD = "hajix2026"   # ← ここだけ変更すればOK！

SAFE_FALLBACK_TOPICS = [
    "今日の感謝", "おすすめのカフェ", "朝のルーティン", "面白い本",
    "散歩の楽しみ", "家族の時間", "新しい挑戦", "笑顔の魔法",
    "おいしいご飯", "未来への一歩", "AIの可能性", "健康Tips"
]

# ====================== Session State ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""
if "available_trends" not in st.session_state:
    st.session_state.available_trends = []
if "selected_trends" not in st.session_state:
    st.session_state.selected_trends = []
if "generated_posts" not in st.session_state:
    st.session_state.generated_posts = []

# ====================== ヘルパー関数 ======================
def get_google_trends():
    try:
        pytrends = TrendReq(hl='ja-JP', tz=540)
        df = pytrends.trending_searches(pn='japan')
        return df[0].head(20).tolist()
    except:
        st.toast("Googleトレンド取得失敗 → 安全話題を使います", icon="⚠️")
        return random.sample(SAFE_FALLBACK_TOPICS, 12)

def get_x_trends():
    try:
        url = "https://getdaytrends.com/japan/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        trends = []
        for a in soup.find_all("a", href=True):
            if "/japan/trend/" in a["href"]:
                trend = a.get_text(strip=True)
                if trend and len(trend) > 1 and trend not in trends:
                    trends.append(trend)
                    if len(trends) >= 20:
                        break
        return trends[:15]
    except Exception as e:
        st.toast(f"Xトレンド取得失敗 → 安全話題を使います", icon="⚠️")
        return random.sample(SAFE_FALLBACK_TOPICS, 12)

def generate_posts(topics, api_key):
    if not api_key:
        time.sleep(1.0)
        templates = [
            "みんな！ {t1} が熱すぎる🔥 {t2} しながら {t3} も絶対チェックして！✨ #今日のトレンド",
            "今日のハイライトは {t1}！ {t2} の影響で {t3} が一気に好きになった😂❤️",
            "最近ハマってる {t1}。 {t2} と合わせると {t3} が最高に楽しいよ〜🌟",
            "{t1} 見てる？ {t2} のおかげで {t3} がもっと面白くなった！誰か語ろう👀",
            "朝イチで {t1} チェックした人いる？ {t2} と {t3} の組み合わせ神すぎる✨"
        ]
        posts = []
        for _ in range(3):
            t1, t2, t3 = random.sample(topics, 3)
            post = random.choice(templates).format(t1=t1, t2=t2, t3=t3)
            if len(post) > 140:
                post = post[:137] + "…"
            posts.append(post)
        return posts

    try:
        client = Groq(api_key=api_key)
        prompt = f"""あなたはXでバズる投稿のプロです。
話題「{topics[0]}」「{topics[1]}」「{topics[2]}」を使って、**自然で魅力的な日本語投稿文をちょうど3つ**作ってください。

【厳守ルール】
・各投稿 140文字以内（絵文字含む）
・絵文字は自然に2〜4個
・呼びかけ・質問でエンゲージメント高め
・ハッシュタグは1〜2個（話題から自然に）
・3つは**完全に違う表現・角度**にする
・親しみやすくポジティブ

出力は厳密にこのJSONのみ：
["投稿1", "投稿2", "投稿3"]"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        posts = json.loads(content)
        if isinstance(posts, list) and len(posts) == 3:
            return [p[:138] + "…" if len(p) > 140 else p for p in posts]
    except Exception as e:
        st.toast(f"Groqエラー → モックで生成します", icon="⚠️")
    return generate_posts(topics, None)

# ====================== UI ======================
if not st.session_state.logged_in:
    st.title("🔒 ログイン")
    st.markdown("**X投稿支援アプリ**（はじめさん専用）")
    pw = st.text_input("パスワード", type="password")
    if st.button("ログイン", type="primary", use_container_width=True):
        if pw == PASSWORD:
            st.session_state.logged_in = True
            st.success("ようこそ！🚀")
            st.rerun()
        else:
            st.error("パスワードが違います😢")
    st.stop()

# メイン画面
st.title("🚀 X投稿支援アプリ")
st.caption("リアルタイムトレンド → AIが自然な140文字投稿を即生成")

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    key_input = st.text_input(
        "Groq APIキー（任意）",
        value=st.session_state.groq_key,
        type="password",
        help="console.groq.com で無料取得可能"
    )
    if key_input != st.session_state.groq_key:
        st.session_state.groq_key = key_input
        st.success("APIキー更新！")
    st.divider()
    if st.button("🚪 ログアウト"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# トレンド選択
col1, col2 = st.columns([3, 1])
with col1:
    source = st.radio("トレンド取得元", ["🟢 Googleトレンド", "🔵 Xトレンド"], horizontal=True)
with col2:
    if st.button("🔄 最新トレンドを取ってくる", type="primary", use_container_width=True):
        with st.spinner("リアルタイム取得中…"):
            if "Google" in source:
                trends = get_google_trends()
            else:
                trends = get_x_trends()
            st.session_state.available_trends = trends
            st.success(f"{len(trends)}件取得完了！")

# 話題選択（最大3つ）
if st.session_state.available_trends:
    st.subheader("📌 3つ選んでね")
    selected = st.multiselect(
        "興味がある話題を**最大3つ**選択",
        options=st.session_state.available_trends,
        default=st.session_state.selected_trends,
        max_selections=3,
        key="multi_select"
    )
    st.session_state.selected_trends = selected

# 生成ボタン
if len(st.session_state.selected_trends) == 3:
    if st.button("🧠 Groqで3投稿を生成！", type="primary", use_container_width=True):
        with st.spinner("🧠 Groqががんばって考えてます..."):
            new_posts = generate_posts(st.session_state.selected_trends, st.session_state.groq_key)
            st.session_state.generated_posts.extend(new_posts)
            st.toast("生成完了！ コピーしてXに投稿しよう🚀", icon="🎉")

# 生成済み投稿表示
if st.session_state.generated_posts:
    st.subheader("✍️ 生成された投稿（新しい順）")
    for i, post in enumerate(reversed(st.session_state.generated_posts)):
        with st.container(border=True):
            st.markdown(f"**投稿 {len(st.session_state.generated_posts)-i}**")
            st.code(post, language=None)
            
            copy_html = f"""
            <button style="background:#4CAF50;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:14px;"
                    onclick="navigator.clipboard.writeText(`{post.replace('`','\\`')}`);">
                📋 コピー
            </button>
            """
            st.components.v1.html(copy_html, height=45)

    if st.button("🔄 さらに3つ新しい投稿を作る", use_container_width=True):
        with st.spinner("🧠 さらに考えてます..."):
            new_posts = generate_posts(st.session_state.selected_trends, st.session_state.groq_key)
            st.session_state.generated_posts.extend(new_posts)
            st.rerun()

# フッター
st.markdown("---")
st.markdown("**使い方**：トレンド取得 → 3つ選択 → 生成 → コピー → X投稿！ 140文字・絵文字入り・毎回違う内容を保証します✨")
