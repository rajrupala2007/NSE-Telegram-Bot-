import requests
import os
from telegram import Bot
from datetime import datetime

# Configuration
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

def get_sectoral_data():
    """Fetch all sector indices with percentage changes"""
    url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)
        response = session.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Filter only sector indices
        sectors = [x for x in data['data'] 
                  if x['index'].startswith('NIFTY ') 
                  and not any(kw in x['index'] for kw in ['50', 'MIDCAP', 'SMLCAP'])]
        return sorted(sectors, key=lambda x: x['pChange'], reverse=True)
    
    except Exception as e:
        print(f"Error fetching sector data: {e}")
        return None

def get_oi_leaders(sector_name):
    """Get top 2 stocks by OI change and volume for a sector"""
    url = f"https://www.nseindia.com/api/liveEquity-derivatives?index={sector_name.replace(' ', '%20')}"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Sort by OI change then volume
        sorted_stocks = sorted(data['data'],
                             key=lambda x: (x['changeinOpenInterest'], x['totalTradedVolume']),
                             reverse=True)
        return sorted_stocks[:2]
    except Exception as e:
        print(f"Error fetching OI data for {sector_name}: {e}")
        return []

def generate_report():
    sectors = get_sectoral_data()
    if not sectors:
        return "⚠️ Failed to fetch sector data"
    
    timestamp = datetime.now().strftime('%H:%M %p, %d-%b-%Y')
    report = [f"📈 *NSE Sectoral Report - {timestamp}* 📉\n"]
    
    # 1. Top gainers/losers
    report.append("🏆 *Top 3 Gaining Sectors*")
    for i, sector in enumerate(sectors[:3], 1):
        report.append(f"{i}. {sector['index']} ▲ {sector['pChange']}%")
    
    report.append("\n💣 *Top 3 Losing Sectors*")
    for i, sector in enumerate(sectors[-3:][::-1], 1):
        report.append(f"{i}. {sector['index']} ▼ {abs(sector['pChange'])}%")
    
    # 2. All sectors
    report.append("\n📊 *All Sectoral Indices*")
    for sector in sectors:
        change = sector['pChange']
        arrow = "▲" if change > 0 else "▼" if change < 0 else "▬"
        report.append(f"• {sector['index']} {arrow} {abs(change)}%")
    
    # 3. OI leaders for top gainer/loser sectors
    top_gainer = sectors[0]['index']
    top_loser = sectors[-1]['index']
    
    oi_gainers = get_oi_leaders(top_gainer)
    if oi_gainers:
        report.append(f"\n🔥 *Top OI Gainers ({top_gainer.split()[-1]} Sector)*")
        for i, stock in enumerate(oi_gainers, 1):
            report.append(f"{i}. {stock['symbol']} - OI ▲ {stock['changeinOpenInterest']}%, Volume: {round(stock['totalTradedVolume']/1_000_000, 1)}M")
    
    oi_losers = get_oi_leaders(top_loser)
    if oi_losers:
        report.append(f"\n💀 *Top OI Gainers ({top_loser.split()[-1]} Sector)*")
        for i, stock in enumerate(oi_losers, 1):
            report.append(f"{i}. {stock['symbol']} - OI ▲ {stock['changeinOpenInterest']}%, Volume: {round(stock['totalTradedVolume']/1_000_000, 1)}M")
    
    return "\n".join(report)

if __name__ == "__main__":
    bot = Bot(token=TOKEN)
    report = generate_report()
    bot.send_message(chat_id=CHAT_ID, text=report, parse_mode="Markdown")
