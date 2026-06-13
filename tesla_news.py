import feedparser
import requests
from datetime import datetime
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yfinance as yf

# ==================== 설정 ====================
RSS_FEEDS = [
    "https://www.teslarati.com/feed/",
    "https://electrek.co/guides/tesla/feed/",
    "https://ir.tesla.com/rss/news-releases.xml",
]

EMAIL_SENDER = "mkswaton@gmail.com"      # ← 여기에 실제 Gmail 주소
EMAIL_PASSWORD = ""                        # Secrets에서 처리
EMAIL_RECEIVER = "ksg0879@naver.com"
# =============================================

def get_tsla_stock():
    try:
        tsla = yf.Ticker("TSLA")
        info = tsla.info
        current = info.get('currentPrice') or info.get('regularMarketPrice')
        previous = info.get('regularMarketPreviousClose')
        change = current - previous if current and previous else 0
        change_pct = (change / previous * 100) if previous else 0
        return {
            'price': round(current, 2) if current else "N/A",
            'change': round(change, 2),
            'change_pct': round(change_pct, 2)
        }
    except:
        return {'price': "N/A", 'change': 0, 'change_pct': 0}

def fetch_news():
    articles = []
    seen = set()
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:12]:
            title = entry.title
            link = entry.link
            summary = entry.get('summary', entry.get('description', ''))[:400]
            pub_date = entry.get('published_parsed') or entry.get('updated_parsed')
            title_hash = hashlib.md5(title.encode()).hexdigest()
            if title_hash in seen: continue
            seen.add(title_hash)
            articles.append({
                'title': title,
                'link': link,
                'summary': summary + '...' if len(summary) > 300 else summary,
                'date': datetime(*pub_date[:6]) if pub_date else datetime.now()
            })
    return sorted(articles, key=lambda x: x['date'], reverse=True)

def create_report(articles, stock):
    now = datetime.now()
    report = f"🚀 테슬라 오늘의 뉴스 & 주가 정리 ({now.strftime('%Y-%m-%d %H:%M')})\n\n"
    report += f"📈 TSLA 주가: ${stock['price']} "
    if stock['change'] >= 0:
        report += f"(▲ +{stock['change']} (+{stock['change_pct']}%) )\n\n"
    else:
        report += f"(▼ {stock['change']} ({stock['change_pct']}%) )\n\n"
    
    report += "📰 주요 뉴스\n"
    for i, art in enumerate(articles[:10], 1):
        report += f"{i}. {art['title']}\n"
        report += f"   {art['summary']}\n"
        report += f"   🔗 {art['link']}\n\n"
    return report

def send_email(report):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"🚀 테슬라 오늘의 뉴스 & 주가 ({datetime.now().strftime('%Y-%m-%d')})"
    msg.attach(MIMEText(report, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ 이메일 발송 성공!")
    except Exception as e:
        print("❌ 이메일 발송 실패:", str(e))

if __name__ == "__main__":
    stock = get_tsla_stock()
    news = fetch_news()
    report = create_report(news, stock)
    print(report)
    send_email(report)
