import streamlit as st
import pandas as pd
import requests
import os
import matplotlib.pyplot as plt
import pytz
import base64
from io import BytesIO



# Set Streamlit app-wide configuration
st.set_page_config(
    page_title="Futures Trading",
    page_icon="💹",
    layout="wide"
)

# Custom CSS styles
st.markdown(
    """
    <style>
    .header-title {
        font-size: 36px;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .header-subtitle {
        font-size: 18px;
        color: #757575;
        margin-bottom: 2rem;
    }
    .data-preview {
        margin-top: 2rem;
    }
    .chart {
        margin-top: 3rem;
        padding: 2rem;
        background-color: #F5F5F5;
        border-radius: 5px;
    }
    .download-csv {
        margin-top: 2rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

class FuturesApp:
    def __init__(self):
        self.api_key = os.environ.get('Xfh7L86PTI39vFaJNdcHsNoMw5J6qu8W6el4oTsLZtRbUNadJYmCcRFF8pOHhv9f')
        self.api_secret = os.environ.get('3fb5dqB2GxIIKCpHpu3TCPHQmBOl8KcugdDnYvRbSImsBawoVQdRZVJtRTqBYocy')
        self.endpoint = 'https://fapi.binance.com/fapi/v1/klines'
    
    def fetch_data(self, symbol, interval, limit):
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        response = requests.get(self.endpoint, params=params)
        klines = response.json()
        df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
        df[['Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Taker buy base asset volume', 'Taker buy quote asset volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Taker buy base asset volume', 'Taker buy quote asset volume']].apply(pd.to_numeric)
        df['Open time'] = pd.to_datetime(df['Open time'], unit='ms') 
        df['Close time'] = pd.to_datetime(df['Close time'], unit='ms')
        df['Taker sell_quote_asset_volume'] = df['Quote asset volume'] - df['Taker buy quote asset volume']
        df = df.reindex(columns=['Open time', 'Open', 'Close', 'High', 'Low', 'Number of trades', 'Volume', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Taker sell_quote_asset_volume', 'Quote asset volume'])
        
        # Convert time to IST
        ist_tz = pytz.timezone("Asia/Kolkata")
        utc_time_col = pd.to_datetime(df['Open time']).dt.tz_localize('UTC')
        ist_time_col = utc_time_col.dt.tz_convert(ist_tz)
        df['Open time'] = ist_time_col.dt.strftime('%Y-%m-%d %H:%M:%S')
        df = df.sort_values('Open time', ascending=False)
        
        return df
    
    def generate_chart(self, df):
        fig, ax = plt.subplots(figsize=(16, 9))
        df['Close'].plot(ax=ax, kind='line')
        ax.set_title('BTCUSDT Prices', fontweight='bold')
        ax.set_xlabel('Date', fontweight='bold')
        ax.set_ylabel('Price', fontweight='bold')
        plt.close(fig)  # Close the figure to avoid displaying it immediately in Streamlit
        
        return fig
    
    def run(self):
        st.title('Welcome to Futures Trading')
        st.markdown('Future of trading')
        st.markdown('---')
        
        st.markdown('<h1 class="header-title">Get the Pair Data for Data Modelling</h1>', unsafe_allow_html=True)
        st.markdown('<p class="header-subtitle">Select the time frame and pair you are interested in:</p>', unsafe_allow_html=True)
        
        tf = st.radio('Time frame for trading', ('1m', '3m', '5m', '30m', '1h'))
        pr = st.text_input('Which pair are you interested in?', autocomplete='off', key='pair_input')
        
        limit = st.number_input('Number of rows to fetch', min_value=1, max_value=1440, value=60)
        
        st.markdown('---')
        
        try:
            df = self.fetch_data(pr, tf, int(limit))
            
            if not df.empty:
                st.success('Data fetched successfully!')
                
                st.subheader('Data Preview')
                st.dataframe(df.head(limit), height=400)
                
                csv = df.to_csv(index=False)
                st.markdown('<div class="download-csv"><a href="data:text/csv;base64,{0}" download="{1}.csv">Download CSV</a></div>'.format(
                    base64.b64encode(csv.encode()).decode(), pr), unsafe_allow_html=True)

                st.markdown('---')
                
                #st.subheader('BTCUSDT Prices')
               
                
            else:
                st.warning('No data available for the selected pair and time frame.')
        except Exception as e:
            st.error(f'Error occurred: {str(e)}')

if __name__ == '__main__':
    bot = FuturesApp()
    bot.run()
