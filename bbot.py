import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz
import time

class FuturesApp:
    def fetch_data(self, symbol, interval, limit):
        endpoint = 'https://fapi.binance.com/fapi/v1/klines'
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        response = requests.get(endpoint, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time',
                                         'Quote asset volume', 'Number of trades', 'Taker buy base asset volume',
                                         'Taker buy quote asset volume', 'Ignore'])
        df[['Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
            'Taker buy base asset volume', 'Taker buy quote asset volume']] = df[
            ['Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
             'Taker buy base asset volume', 'Taker buy quote asset volume']].apply(pd.to_numeric)

        # Convert timestamps to local timezone (IST)
        ist_tz = pytz.timezone("Asia/Kolkata")
        df['Open time'] = pd.to_datetime(df['Open time'], unit='ms', utc=True).dt.tz_convert(ist_tz)

        # Separate date and time columns
        df['Date'] = df['Open time'].dt.date
        df['Time'] = df['Open time'].dt.time

        # Remove "+05:30" offset from time
        df['Time'] = df['Time'].apply(lambda x: x.replace(tzinfo=None))

        df = df.sort_values('Open time', ascending=False)
        df = df.reindex(columns=['Date', 'Time', 'Open', 'Close', 'High', 'Low', 'Number of trades', 'Volume',
                                 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Quote asset volume'])
        return df

    def calculate_middle_value(self, high_prices, low_prices):
        middle_value = (high_prices + low_prices) / 2
        return middle_value

    def predict_action(self, current_price, middle_value, high_prices, stop_loss, take_profit, custom_profit_loss):
        danger_threshold = middle_value + 0.7 * (high_prices - middle_value)

        if current_price > danger_threshold:
            return 'Danger'
        elif current_price > take_profit:
            return 'Sell (Take Profit)'
        elif current_price < stop_loss:
            return 'Sell (Stop Loss)'
        elif current_price > middle_value:
            return 'Sell'
        else:
            for pl in custom_profit_loss:
                if current_price > pl:
                    return f'Sell ({pl}% Profit)'
                elif current_price < -pl:
                    return f'Sell ({pl}% Loss)'
            return 'Buy'

    def run(self):
        st.title('Welcome to Futures Trading')
        st.markdown('Future of trading')
        st.markdown('---')

        st.markdown('<h1 class="header-title">Get the Pair Data for Data Modelling</h1>', unsafe_allow_html=True)
        st.markdown('<p class="header-subtitle">Select the time frame and pair you are interested in:</p>', unsafe_allow_html=True)

        tf = st.radio('Time frame for trading', ('1m', '3m', '5m', '30m', '1h'))
        pr = st.text_input('Which pair are you interested in?', autocomplete='off', key='pair_input')

        limit = st.number_input('Number of rows to fetch', min_value=1, max_value=1440, value=60)

        custom_profit_loss = list(range(10, 101, 10))  # Generate a list of percentages from 10% to 100% in steps of 10

        st.markdown('---')

        try:
            while True:
                df = self.fetch_data(pr, tf, int(limit))

                if not df.empty:
                    st.success('Data fetched successfully!')

                    st.subheader('Data Preview')
                    st.dataframe(df.head(limit), height=400)

                    high_prices = df['High'].max()
                    low_prices = df['Low'].min()
                    middle_value = self.calculate_middle_value(high_prices, low_prices)
                    current_price = df['Close'].iloc[-1]

                    for pl in custom_profit_loss:
                        stop_loss = current_price - (current_price * pl / 100)
                        take_profit = current_price + (current_price * pl / 100)
                        action = self.predict_action(current_price, middle_value, high_prices, stop_loss, take_profit, custom_profit_loss)

                        st.markdown('---')
                        st.subheader(f'Strategy (Profit/Loss: {pl}%)')
                        st.write('24-hour High Price:', high_prices)
                        st.write('24-hour Low Price:', low_prices)
                        st.write('Middle Value:', middle_value)
                        st.write('Current Price:', current_price)
                        st.write('Stop Loss:', stop_loss)
                        st.write('Take Profit:', take_profit)
                        st.write('Action:', action)

                else:
                    st.warning('No data available for the selected pair and time frame.')

                time.sleep(100000000)

        except Exception as e:
            st.error(f'Error occurred: {str(e)}')

if __name__ == '__main__':
    bot = FuturesApp()
    bot.run()
