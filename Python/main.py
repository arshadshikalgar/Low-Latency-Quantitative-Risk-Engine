import yfinance as yf
import numpy as np
from scipy.stats import t
import google.generativeai as genai
import smtplib
from email.message import EmailMessage
import os

# --- PART 1: The Deterministic Tool (Same as before) ---
def run_fat_tail_simulation(ticker="SPY", days=252, simulations=10000):
    data = yf.download(ticker, start='2018-01-01', end='2023-01-01', progress=False)
    prices = data['Close'].squeeze()
    log_returns = np.log(prices / prices.shift(1)).dropna()

    degrees_of_freedom, empirical_drift, empirical_scale = t.fit(log_returns)
    
    random_shocks = np.random.standard_t(df=degrees_of_freedom, size=(days, simulations))
    daily_multipliers = np.exp(empirical_drift + (empirical_scale * random_shocks))
    
    price_paths = np.zeros_like(daily_multipliers)
    price_paths[0] = prices.iloc[-1]
    
    for day in range(1, days):
        price_paths[day] = price_paths[day-1] * daily_multipliers[day]
        
    final_prices = price_paths[-1]
    
    return {
        "Ticker": ticker,
        "Current_Price": round(prices.iloc[-1], 2),
        "Expected_1Yr_Price": round(np.mean(final_prices), 2),
        "VaR_5_Percent": round(np.percentile(final_prices, 5), 2),
        "Black_Swan_VaR_1_Percent": round(np.percentile(final_prices, 1), 2),
        "Market_Chaos_Index": round(degrees_of_freedom, 2)
    }

# --- PART 2: The Secure Email Dispatcher ---
def dispatch_email(report_text, target_email):
    # Retrieve secure credentials from the cloud environment
    sender_email = os.environ.get("SENDER_EMAIL")
    app_password = os.environ.get("EMAIL_APP_PASSWORD")
    
    # Construct the logical payload
    msg = EmailMessage()
    msg.set_content(report_text)
    msg['Subject'] = "Morning Risk Briefing: SPY Quantitative Analysis"
    msg['From'] = sender_email
    msg['To'] = target_email

    # Open a secure socket and transmit
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        return "Transmission successful."
    except Exception as e:
        return f"Transmission failed: {e}"

# --- PART 3: The Cloud Function Entry Point ---
def main_trigger(request):
    """This is the function Google Cloud Scheduler will trigger at 6:00 AM"""
    
    # 1. Initialize API Keys from Secret Manager
    api_key = os.environ.get("GEMINI_API_KEY")
    target_email = os.environ.get("SENDER_EMAIL") # Sending to yourself
    genai.configure(api_key=api_key)
    
    # 2. Run the Engine
    risk_data = run_fat_tail_simulation("SPY")
    
    # 3. Synthesize the Intelligence
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    You are a Senior Quantitative Risk Officer. 
    Review this Monte Carlo simulation data: {risk_data}.
    Write a concise, highly professional morning risk briefing.
    Structure: Executive Summary, Upside vs Downside, Black Swan Exposure, Market Chaos Note.
    """
    response = model.generate_content(prompt)
    
    # 4. Dispatch the Report
    delivery_status = dispatch_email(response.text, target_email)
    
    # Cloud Functions require a return response for logging
    return f"Pipeline executed. {delivery_status}"
