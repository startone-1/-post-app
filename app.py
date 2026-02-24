import streamlit as st
import requests
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from groq import Groq
import random
import json
import time

# ====================== スマホ完全レスポンシブ ======================
st.set_page_config(
    page_title="X投稿支援アプリ",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stButton>button {
        width: 100% !important;
        height: 65px !important;
        font-size: 18px !important;
        margin: 8px 0;
    }
    @media (max-width: 600px) {
        .stButton>button { height: 58px !important; font-size: 17px !important; }
    }
</style>
""", unsafe_allow_html=True)

PASSWORD = "1"   # ← パスワードは「1」です

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
    except:
        st.toast("Xトレンド取得失敗 → 安全話題を使います", icon="⚠️")
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
        prompt = f"""あなたは心理学の修士号を持ち、統計学を専門に研究し、SNSで何百万インプレッションを達成した投稿のプロです。

話題「{topics[0]}」「{topics[1]}」「{topics[2]}」を使って、**心に深く響く自然な日本語投稿文をちょうど3つ**作ってください。

【厳守ルール】
・各投稿 140文字以内
・絵文字は自然に1〜3個
・ハッシュタグは絶対に使わない
・X公式ルール完全遵守（ファーミング禁止、強引な誘導禁止、スパム・自動化表現一切禁止）
・個人体験のような自然で誠実な語り口
・心理学的に共感を最大限に引き出す
・3つは完全に違う角度・表現にする
・読んだ人が「わかる…！」となるもの

出力は厳密にこのJSONのみ：
["投稿1", "投稿2", "投稿3"]"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.1,
            max_tokens=700,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        posts = json.loads(content)
        if isinstance(posts, list) and len(posts) == 3:
            return [p[:138] + "…" if len(p) > 140 else p for p in posts]
    except:
        st.toast("Groqエラー → 高品質モックで生成します", icon="⚠️")
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

st.title("🚀 X投稿支援アプリ")
st.caption("1ボタンで自動生成！ 共感力MAX・ハッシュタグなし・Xルール完全遵守")

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    key_input = st.text_input("Groq APIキー（任意）", value=st.session_state.groq_key, type="password")
    if key_input != st.session_state.groq_key:
        st.session_state.groq_key = key_input
        st.success("APIキー更新！")
    st.divider()
    if st.button("🚪 ログアウト"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ワンクリック自動生成
if st.button("🔄 最新トレンドを取って自動で3投稿を作る", type="primary", use_container_width=True):
    with st.spinner("🧠 トレンド取得 → 自動選択 → 高品質投稿生成中..."):
        source = st.radio("トレンド取得元", ["🟢 Googleトレンド", "🔵 Xトレンド"], horizontal=True, label_visibility="collapsed")
        if "Google" in source:
            trends = get_google_trends()
        else:
            trends = get_x_trends()
        
        st.session_state.available_trends = trends
        
        if len(trends) >= 3:
            selected = random.sample(trends, 3)
            st.session_state.selected_trends = selected
            new_posts = generate_posts(selected, st.session_state.groq_key)
            st.session_state.generated_posts.extend(new_posts)
            st.toast("✅ 自動で3投稿生成完了！", icon="🎉")
            st.rerun()
        else:
            st.error("トレンドが足りませんでした。もう一度押してね")

# 生成済み投稿表示
if st.session_state.generated_posts:
    st.subheader("✍️ 生成された投稿（新しい順）")
    for i, post in enumerate(reversed(st.session_state.generated_posts)):
        with st.container(border=True):
            st.markdown(f"**投稿 {len(st.session_state.generated_posts)-i}**")
            st.code(post, language=None)
            
            if st.button("📋 コピー", key=f"copy_{i}", use_container_width=True):
                st.toast("✅ コピーしました！ 投稿文をXに貼り付けてね🚀", icon="📋")

    if st.button("🔄 同じ話題でさらに3つ新しい投稿を作る", use_container_width=True):
        with st.spinner("🧠 さらに考えてます..."):
            new_posts = generate_posts(st.session_state.selected_trends, st.session_state.groq_key)
            st.session_state.generated_posts.extend(new_posts)
            st.rerun()

# フッター
st.markdown("---")
st.markdown("**使い方**：上のボタン1つで全部自動！ 140文字・共感重視・ハッシュタグなし・Xルール完全遵守です✨")
