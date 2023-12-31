import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt


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

    def forecast(self, series):
        model = ARIMA(series, order=(1, 0, 0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=1)[0]
        return forecast

    def predict_action(self, current_price, future_price):
        if future_price > current_price:
            return 'Buy'
        else:
            return 'Sell'

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

                # Forecast and prediction
                series = df['Close'].values
                current_price = series[-1]
                forecast = self.forecast(series)
                action = self.predict_action(current_price, forecast)

                st.markdown('---')
                st.subheader('Forecast and Action')
                st.write('Current Price:', current_price)
                st.write('Forecasted Price:', forecast)
                st.write('Action:', action)

                # Line chart of forecasted price and actual price
                df_chart = df[['Date', 'Time', 'Close']].copy()
                df_chart['DateTime'] = pd.to_datetime(df_chart['Date'].astype(str) + ' ' + df_chart['Time'].astype(str))
                df_chart = df_chart.set_index('DateTime')

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(df_chart.index, df_chart['Close'], label='Actual Price')
                ax.plot(df_chart.index[-1], forecast, 'ro', label='Forecasted Price')
                ax.set_title('Price Chart')
                ax.set_xlabel('DateTime')
                ax.set_ylabel('Price')
                ax.legend()
                ax.tick_params(axis='x', rotation=45)
                st.pyplot(fig)


                csv = df.to_csv(index=False)
                st.markdown('<div class="download-csv"><a href="data:text/csv;base64,{0}" download="{1}.csv">Download CSV</a></div>'.format(
                    base64.b64encode(csv.encode()).decode(), pr), unsafe_allow_html=True)

                st.markdown('---')

            else:
                st.warning('No data available for the selected pair and time frame.')
        except Exception as e:
            st.error(f'Error occurred: {str(e)}')


if __name__ == '__main__':
    bot = FuturesApp()
    bot.run()
