import base64
import os
from IPython.display import display, HTML

# ==========================================
# 1. 音声ファイルの読み込み設定
# ==========================================
files = {
    "start": "sounds/試合開始のゴング.mp3",
    "end":   "sounds/zikangire.mp3",#試合終了のゴング.mp3",
    "count": "sounds/決定ボタンを押す1.mp3",
    "hit":   "sounds/決定ボタンを押す52.mp3"
}

def load_sound(key, filename):
    defaults = {
        "start": "../sounds/crowd_whistle.ogg",
        "end":   "../sounds/alarm_clock.ogg",
        "count": "../sounds/beep_short.ogg",
        "hit":   "../sounds/pop.ogg"
    }
    if os.path.exists(filename):
        try:
            with open(filename, "rb") as f:
                data = f.read()
                b64_str = base64.b64encode(data).decode('utf-8')
                print(f"✅ 読み込み成功: {filename}")
                return f"data:audio/mp3;base64,{b64_str}"
        except Exception as e:
            print(f"❌ 読み込みエラー: {filename} ({e})")
    else:
        print(f"⚠️ ファイルが見つかりません: {filename} (デフォルト音を使用します)")
    return defaults[key]

print("--- 音声ファイルの準備中 ---")
src_start = load_sound("start", files["start"])
src_end   = load_sound("end",   files["end"])
src_count = load_sound("count", files["count"])
src_hit   = load_sound("hit",   files["hit"])
print("----------------------------")

# ==========================================
# 2. アプリ本体 (終了ゴング判定復活版)
# ==========================================
app_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Target Game v12 (Fixed Gong)</title>
<style>
    body {{ font-family: 'Segoe UI', sans-serif; text-align: center; background: #222; color: white; margin: 0; padding: 20px; }}
    .container {{ max-width: 800px; margin: 0 auto; background: #333; padding: 30px; border-radius: 15px; border: 1px solid #555; }}

    .game-area {{ display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px; }}
    .left-panel {{ flex: 1; min-width: 300px; }}
    .right-panel {{ flex: 1; min-width: 250px; }}

    .score-box {{ background: #444; padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #888; position: relative; }}
    .score-value {{ font-size: 6rem; font-weight: bold; color: #00ffcc; margin: 0; line-height: 1; text-shadow: 0 0 20px #00ffcc; }}

    .msg-overlay {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 4rem; font-weight: bold; color: #ffcc00; text-shadow: 3px 3px 0 #000; display: none; width: 100%; pointer-events: none; white-space: nowrap; }}

    .log-box {{ background: #000; color: #0f0; font-family: monospace; padding: 10px; height: 100px; overflow-y: scroll; text-align: left; border-radius: 5px; border: 1px solid #555; font-size: 12px; }}

    /* ランキング用 */
    .ranking-box {{ background: #2a2a2a; padding: 15px; border-radius: 10px; border: 2px solid #d4af37; text-align: left; }}
    .ranking-title {{ color: #d4af37; text-align: center; margin: 0 0 10px 0; border-bottom: 1px solid #555; padding-bottom: 5px; }}
    #rankingList {{ list-style: none; padding: 0; margin: 0; }}
    #rankingList li {{ padding: 8px; border-bottom: 1px solid #444; display: flex; justify-content: space-between; font-size: 1.1rem; }}

    button {{ padding: 10px 20px; cursor: pointer; border: none; border-radius: 5px; margin: 5px; font-weight: bold; color: white; transition: 0.2s; }}
    .btn-connect {{ background: #007bff; font-size: 16px; padding: 12px 24px; }}

    .btn-start {{ background: #28a745; font-size: 18px; padding: 15px 30px; width: 45%; }}
    .btn-start:hover {{ background: #218838; }}
    .btn-start:disabled {{ background: #555; cursor: not-allowed; }}

    .btn-reset {{ background: #dc3545; font-size: 18px; padding: 15px 30px; width: 45%; }}
    .btn-reset:hover {{ background: #c82333; }}
    .btn-reset:disabled {{ background: #555; cursor: not-allowed; }}

    .btn-test {{ background: #555; font-size: 12px; border: 1px solid #777; }}
    .btn-test:hover {{ background: #777; }}

    .hit-anim {{ animation: flash 0.1s; }}
    @keyframes flash {{ 0% {{ background: #333; }} 50% {{ background: #fff; }} 100% {{ background: #333; }} }}
</style>
</head>
<body>
<div class="container" id="mainContainer">
    <h2>🎯 ターゲットゲーム (v12 修正版)</h2>

    <div class="game-area">
        <div class="left-panel">
            <div style="margin-bottom:10px;">
                <button class="btn-test" onclick="playSound('count')">🎵 カウント</button>
                <button class="btn-test" onclick="playSound('start')">🎵 スタート</button>
                <button class="btn-test" onclick="playSound('hit')">🎵 検知音</button>
                <button class="btn-test" onclick="playSound('end')">🎵 終了音</button>
            </div>

            <div style="margin-bottom: 15px;">
                <button id="connectBtn" class="btn-connect">Arduinoと接続</button>
            </div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <button id="startBtn" class="btn-start" disabled>GAME START</button>
                <button id="resetBtn" class="btn-reset" disabled>RESET</button>
            </div>

            <div class="score-box" id="scoreBox">
                <div class="score-value" id="scoreDisp">0</div>
                <div class="msg-overlay" id="msgDisp">READY</div>
            </div>
        </div>

        <div class="right-panel">
            <div class="ranking-box">
                <h3 class="ranking-title">🏆 RANKING</h3>
                <ul id="rankingList"></ul>
                <div style="text-align:center; margin-top:10px;">
                    <button onclick="clearRanking()" style="background:#555; font-size:10px;">履歴削除</button>
                </div>
            </div>
        </div>
    </div>

    <div class="log-box" id="logArea">ファイル読み込み完了</div>
</div>

<script>
const srcStart = "{src_start}";
const srcEnd   = "{src_end}";
const srcCount = "{src_count}";
const srcHit   = "{src_hit}";

const sounds = {{
    hit: new Audio(srcHit),
    count: new Audio(srcCount),
    start: new Audio(srcStart),
    end: new Audio(srcEnd)
}};
Object.values(sounds).forEach(s => s.load());

const connectBtn = document.getElementById('connectBtn');
const startBtn = document.getElementById('startBtn');
const resetBtn = document.getElementById('resetBtn');
const scoreDisp = document.getElementById('scoreDisp');
const msgDisp = document.getElementById('msgDisp');
const logArea = document.getElementById('logArea');
const container = document.getElementById('mainContainer');
const rankingList = document.getElementById('rankingList');

let port, writer;

// --- ランキング ---
let highScores = JSON.parse(localStorage.getItem('targetGameRanking')) || [
    {{ name: "CPU", score: 15 }}, {{ name: "CPU", score: 10 }}, {{ name: "CPU", score: 5 }}, {{ name: "CPU", score: 2 }}, {{ name: "CPU", score: 1 }}
];

function updateRankingDisplay() {{
    rankingList.innerHTML = "";
    highScores.sort((a, b) => b.score - a.score);
    highScores.slice(0, 5).forEach((entry, index) => {{
        const li = document.createElement('li');
        li.innerHTML = `<span>${{index + 1}}. ${{entry.name}}</span> <span>${{entry.score}}</span>`;
        rankingList.appendChild(li);
    }});
    localStorage.setItem('targetGameRanking', JSON.stringify(highScores));
}}

function checkHighScore(finalScore) {{
    const lowestScore = highScores.length < 5 ? 0 : highScores[Math.min(highScores.length, 5) - 1].score;
    if (finalScore > lowestScore) {{
        setTimeout(() => {{
            const name = prompt(`🎉 ランクイン！(Score: ${{finalScore}})\\n名前を入力:`, "Guest");
            if (name) {{
                highScores.push({{ name: name, score: parseInt(finalScore) }});
                updateRankingDisplay();
                addLog("🏆 ランキング更新");
            }}
        }}, 500);
    }}
}}
window.clearRanking = () => {{
    if(confirm("リセットしますか？")) {{ localStorage.removeItem('targetGameRanking'); highScores = []; updateRankingDisplay(); }}
}};
updateRankingDisplay();

// --- 通信 & UI ---
function addLog(msg) {{
    const div = document.createElement('div');
    div.textContent = msg;
    logArea.appendChild(div);
    logArea.scrollTop = logArea.scrollHeight;
}}

function showMsg(text, color="#ffcc00") {{
    msgDisp.innerText = text;
    msgDisp.style.color = color;
    msgDisp.style.display = "block";
    scoreDisp.style.opacity = "0.3";
    setTimeout(() => {{
        msgDisp.style.display = "none";
        scoreDisp.style.opacity = "1";
    }}, 900);
}}

window.playSound = (type) => {{
    sounds[type].currentTime = 0;
    sounds[type].play().then(() => {{}}).catch(e => console.log(e));
}};

startBtn.addEventListener('click', async () => {{
    if (writer) {{
        try {{
            await writer.write("s");
            addLog("📤 START信号送信");
            scoreDisp.textContent = "0";
            startBtn.disabled = true;
            resetBtn.disabled = false;
        }} catch (e) {{ addLog("❌ エラー: " + e); }}
    }}
}});

resetBtn.addEventListener('click', async () => {{
    if (writer) {{
        try {{
            await writer.write("r");
            addLog("📤 RESET信号送信");
            sounds.end.currentTime = 0;
            sounds.end.play().catch(()=>{{}});
            showMsg("STOP", "#dc3545");
            scoreDisp.textContent = "0";
            startBtn.disabled = false;
        }} catch (e) {{ addLog("❌ エラー: " + e); }}
    }}
}});

connectBtn.addEventListener('click', async () => {{
    if (!navigator.serial) return alert("PC版 Chrome/Edge を使用してください");
    try {{
        port = await navigator.serial.requestPort();
        await port.open({{ baudRate: 115200 }});

        const textEncoder = new TextEncoderStream();
        const writableStreamClosed = textEncoder.readable.pipeTo(port.writable);
        writer = textEncoder.writable.getWriter();

        connectBtn.disabled = true;
        connectBtn.textContent = "接続済み";
        startBtn.disabled = false;
        resetBtn.disabled = false;
        addLog("✅ 接続完了");

        const decoder = new TextDecoderStream();
        port.readable.pipeTo(decoder.writable);
        const reader = decoder.readable.getReader();

        let buffer = "";
        while (true) {{
            const {{ value, done }} = await reader.read();
            if (done) break;
            if (value) {{
                buffer += value;
                let lines = buffer.split('\\n');
                buffer = lines.pop();

                for (let line of lines) {{
                    line = line.trim();
                    if (line.length === 0) continue;

                    // ここが復活した部分です！
                    if (line.includes("PLAY_END")) {{
                        sounds.end.currentTime = 0;
                        sounds.end.play().catch(()=>{{}});
                        showMsg("FINISH!", "#ffcc00");
                        addLog("🔔 試合終了");

                        // ランキング判定
                        let currentScore = parseInt(scoreDisp.textContent);
                        checkHighScore(currentScore);
                    }}
                    else if (line.includes("COUNT_")) {{
                        playSound('count');
                        let num = line.split("_")[1];
                        showMsg(num, "#00ccff");
                    }}
                    else if (line.includes("PLAY_START")) {{
                        playSound('start');
                        showMsg("FIGHT!", "#e94560");
                        scoreDisp.textContent = "0";
                        addLog("🔔 試合開始");
                        startBtn.disabled = true;
                    }}
                    else if (line.includes("PLAY_HIT")) {{
                        let clone = sounds.hit.cloneNode();
                        clone.play().catch(()=>{{}});
                        container.classList.remove("hit-anim");
                        void container.offsetWidth;
                        container.classList.add("hit-anim");
                    }}
                    else if (line.includes("RESET_DONE")) {{
                        addLog("🛑 ボタン待機");
                        startBtn.disabled = false;
                    }}
                    else if (line.includes("スコア")) {{
                        let match = line.match(/スコア[:：]\\s*(\\d+)/);
                        if (match) scoreDisp.textContent = match[1];
                    }}
                }}
            }}
        }}
    }} catch (e) {{ addLog("❌ エラー: " + e); }}
}});
</script>
</body>
</html>
"""

b64_html = base64.b64encode(app_html.encode('utf-8')).decode('utf-8')

launcher_html = f"""
<div style="background:#222; padding:20px; border-radius:10px; text-align:center; border:2px solid #00ffcc; color:white; font-family:sans-serif;">
    <h3 style="margin-top:0;">🎮 コントローラー v12</h3>
    <p>「終了ゴング」と「ランキング」が確実に動く修正版です。</p>
    <button onclick="openApp()" style="background:#00ffcc; color:black; border:none; padding:15px 30px; font-size:18px; border-radius:8px; cursor:pointer; font-weight:bold;">
        🚀 コントローラーを開く
    </button>
</div>
<script>
function openApp() {{
    const b64 = "{b64_html}";
    const binaryString = atob(b64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {{
        bytes[i] = binaryString.charCodeAt(i);
    }}
    const decoder = new TextDecoder('utf-8');
    const html = decoder.decode(bytes);
    const blob = new Blob([html], {{ type: 'text/html' }});
    window.open(URL.createObjectURL(blob), '_blank');
}}
</script>
"""

#display(HTML(launcher_html))


with open("controller.html", "w", encoding="utf-8") as f:
    f.write(launcher_html)
