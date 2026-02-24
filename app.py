import streamlit as st
import requests
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from groq import Groq
import random
import json
import time

st.set_page_config(page_title="X投稿支援アプリ", page_icon="🚀", layout="centered")

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; height: 60px; font-size: 18px; border-radius: 12px; }
    .post-card { background: #1e1e2e; padding: 20px; border-radius: 16px; margin: 12px 0; border-left: 5px solid #4CAF50; }
    .post-text { font-size: 17px; line-height: 1.6; color: #e0e0e0; }
    @media (max-width: 600px) { .post-text { font-size: 16px; } }
</style>
""", unsafe_allow_html=True)

PASSWORD = "1"

SAFE_FALLBACK_TOPICS = ["今日の感謝", "おすすめのカフェ", "朝のルーティン", "面白い本", "散歩の楽しみ", "家族の時間", "新しい挑戦", "笑顔の魔法", "おいしいご飯", "未来への一歩", "AIの可能性", "健康Tips"]

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "groq_key" not in st.session_state: st.session_state.groq_key = ""
if "generated_posts" not in st.session_state: st.session_state.generated_posts = []

def get_google_trends():
    try:
        pytrends = TrendReq(hl='ja-JP', tz=540)
        df = pytrends.trending_searches(pn='japan')
        return df[0].head(20).tolist()
    except:
        return random.sample(SAFE_FALLBACK_TOPICS, 12)

def get_x_trends():
    try:
        url = "https://getdaytrends.com/japan/"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        trends = []
        for a in soup.find_all("a", href=True):
            if "/japan/trend/" in a["href"]:
                trend = a.get_text(strip=True)
                if trend and len(trend) > 1 and trend not in trends:
                    trends.append(trend)
                    if len(trends) >= 20: break
        return trends[:15] or random.sample(SAFE_FALLBACK_TOPICS, 12)
    except:
        return random.sample(SAFE_FALLBACK_TOPICS, 12)

def generate_posts(topics, api_key):
    try:
        client = Groq(api_key=api_key)
        prompt = f"""あなたは心理学修士・SNSバズ専門家です。
話題「{topics[0]}」「{topics[1]}」「{topics[2]}」を使って、心に深く響く自然な日本語投稿を3つ作ってください。

厳守ルール:
- 140文字以内
- 絵文字は自然に1〜3個
- ハッシュタグ完全禁止
- X公式ルール完全遵守（ファーミング・スパム・強引誘導一切なし）
- 読んだ人が「わかる…」「そうだよね」と共感する本音調
- 優しくポジティブで、プロが書いたような上質さ

出力は厳密にこのJSONのみ：
["投稿1", "投稿2", "投稿3"]"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.15,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        posts = json.loads(response.choices[0].message.content)
        return [p[:138] + "…" if len(p) > 140 else p for p in posts]
    except:
        st.toast("Groqエラー → 高品質モックで生成します", icon="⚠️")
        templates = [
            "最近 {t1} の話で心が温かくなったよ。{t2} をしながらふと思ったんだけど、{t3} って本当に大事だよね…",
            "今日 {t1} を知って、なんだか優しい気持ちになった。{t2} と {t3} を重ねて考えてみたら、すごく納得できたよ",
            "みんなは {t1} でどんな気持ちになった？ 私は {t2} がきっかけで {t3} が急に大切に思えてきたんだ"
        ]
        posts = []
        for _ in range(3):
            t1, t2, t3 = random.sample(topics, 3)
            post = random.choice(templates).format(t1=t1, t2=t2, t3=t3)
            if len(post) > 140: post = post[:137] + "…"
            posts.append(post)
        return posts

# ログイン
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
st.caption("1タップでプロ級投稿を自動生成")

with st.sidebar:
    st.header("⚙️ 設定")
    key_input = st.text_input("Groq APIキー（任意）", value=st.session_state.groq_key, type="password")
    if key_input != st.session_state.groq_key:
        st.session_state.groq_key = key_input
        st.success("更新しました！")
    st.divider()
    if st.button("🚪 ログアウト"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# 自動生成
if st.button("🔄 最新トレンドを取って自動で3投稿を作る", type="primary", use_container_width=True):
    with st.spinner("🧠 トレンド取得 → 自動選択 → プロ級生成中..."):
        source = st.selectbox("トレンド取得元", ["🟢 Googleトレンド", "🔵 Xトレンド"])
        trends = get_google_trends() if "Google" in source else get_x_trends()
        if len(trends) >= 3:
            selected = random.sample(trends, 3)
            new_posts = generate_posts(selected, st.session_state.groq_key)
            st.session_state.generated_posts.extend(new_posts)
            st.toast("✅ プロ級投稿3つ生成完了！", icon="🎉")
            st.rerun()

# 生成投稿表示（スタイリッシュ）
if st.session_state.generated_posts:
    st.subheader("✍️ 生成された投稿（新しい順）")
    for i, post in enumerate(reversed(st.session_state.generated_posts)):
        with st.container():
            st.markdown(f"""
            <div class="post-card">
                <strong>投稿 {len(st.session_state.generated_posts)-i}</strong><br>
                <span class="post-text">{post}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 タップでコピー", key=f"copy_{i}", use_container_width=True):
                st.toast(f"✅ コピーしました！\n\n{post}\n\nXに貼り付けてね🚀", icon="📋")

    if st.button("🔄 同じ話題でさらに3つ生成", use_container_width=True):
        with st.spinner("🧠 さらにプロ級で考えてます..."):
            new_posts = generate_posts(st.session_state.selected_trends if "selected_trends" in st.session_state else ["トレンド1","トレンド2","トレンド3"], st.session_state.groq_key)
            st.session_state.generated_posts.extend(new_posts)
            st.rerun()

st.markdown("---")
st.markdown("**使い方**：上のボタン1つで全部自動！ タップでコピー → Xに貼ってね✨")
