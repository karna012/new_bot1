import streamlit as st
import pandas as pd
from binance.client import Client
import base64
import pytz

# Binance API credentials
API_KEY = 'Xfh7L86PTI39vFaJNdcHsNoMw5J6qu8W6el4oTsLZtRbUNadJYmCcRFF8pOHhv9f'
API_SECRET = '3fb5dqB2GxIIKCpHpu3TCPHQmBOl8KcugdDnYvRbSImsBawoVQdRZVJtRTqBYocy'

# Initialize Binance client
client = Client(API_KEY, API_SECRET)

class FuturesApp:
    def fetch_data(self, symbol, interval, limit):
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time',
                                           'Quote asset volume', 'Number of trades', 'Taker buy base asset volume',
                                           'Taker buy quote asset volume', 'Ignore'])
        df[['Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
            'Taker buy base asset volume', 'Taker buy quote asset volume']] = df[
            ['Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
             'Taker buy base asset volume', 'Taker buy quote asset volume']].apply(pd.to_numeric)
        
        # Convert time to IST and remove timezone offset
        df['Open time'] = pd.to_datetime(df['Open time'], unit='ms').dt.tz_localize(pytz.utc).dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
        df['Close time'] = pd.to_datetime(df['Close time'], unit='ms').dt.tz_localize(pytz.utc).dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
        
        df = df.sort_values('Open time', ascending=False)
        df = df.reindex(columns=['Open time', 'Open', 'Close', 'High', 'Low', 'Number of trades', 'Volume',
                                 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Quote asset volume'])

        return df

    def run(self):
        st.title('Welcome to Futures Trading')
        st.markdown('Future of trading')
        st.markdown('---')

        st.markdown('<h1 class="header-title">Get the Pair Data for Data Modelling</h1>', unsafe_allow_html=True)
        st.markdown('<p class="header-subtitle">Select the time frame and pair you are interested in:</p>',
                    unsafe_allow_html=True)

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
                st.markdown(
                    '<div class="download-csv"><a href="data:text/csv;base64,{0}" download="{1}.csv">Download CSV</a></div>'.format(
                        base64.b64encode(csv.encode()).decode(), pr), unsafe_allow_html=True)

                st.markdown('---')

                # st.subheader('BTCUSDT Prices')

            else:
                st.warning('No data available for the selected pair and time frame.')
        except Exception as e:
            st.error(f'Error occurred: {str(e)}')

if __name__ == '__main__':
    bot = FuturesApp()
    bot.run()