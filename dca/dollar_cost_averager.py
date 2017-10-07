from kivy.app import App
from kivy.clock import Clock
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput

from kivy.properties import ListProperty
from kivy.properties import StringProperty

from decimal import Decimal
import re, math, time
from coinbase.wallet.client import Client
import gdax


class ScreenManagement(ScreenManager):
    pass


class DCAApp(App):
    gdax_auth = ""
    coinbase_auth = ""
    gdax_recycle_view_data = ""
    gdax_currencies = ""
    gdax_products = ""
    gdax_trade_pairs = []
    trade_symbol = ""
    trade_details = ""
    App.title = "Crypto Dollar Cost Averager"

    def build(self):
        return ScreenManagement()


class GdaxApiScreen(Screen):
    def __init__(self, **kwargs):
        super(GdaxApiScreen, self).__init__(**kwargs)

    def fetch_data_from_gdax(self):
        app = App.get_running_app()
        key = self.ids.gkey.text
        b64secret = self.ids.gsecret.text
        passphrase = self.ids.gpassphrase.text

        try:
            app.gdax_auth = gdax.AuthenticatedClient(key, b64secret, passphrase)
            accounts = self.gdax_format_account(app.gdax_auth)
            self.recycle_view.data = [{'text': "{}".format(accounts)}]
            app.gdax_recycle_view_data = [{'text': "{}".format(accounts)}]
            app.gdax_currencies = app.gdax_auth.get_currencies()
            app.gdax_products = app.gdax_auth.get_products()
        except:
            Alert('GDAX Authentication Error', 'Please check that you have configured\nyour GDAX API correctly and that\nyou have internet connectivity.')

    def gdax_format_account(self, auth):
        accounts = auth.get_accounts()
        account_rv = ""
        for account in accounts:
            account_rv += "\n" + account['currency'] + " Total: " + str(round(Decimal(account['balance']), 3))
        return account_rv

    def remove_rv_and_input_text(self):
        self.text_gdax_key.text = ""
        self.text_gdax_secret.text = ""
        self.text_gdax_passphrase.text = ""
        self.recycle_view.data = ""


class CoinbaseApiScreen(Screen):
    gdax_rv = ListProperty()

    def fetch_data_from_coinbase(self):
        app = App.get_running_app()
        api_key = self.ids.ckey.text
        api_secret = self.ids.csecret.text

        try:
            app.coinbase_auth = Client(api_key, api_secret)
            self.recycle_view_coinbase.data = [{'text': "{}".format(self.coinbase_format_account(app.coinbase_auth))}]
        except:
            Alert('Coinbase Authentication Error', 'Please check that you have configured\nyour Coinbase API correctly and\nthat you have internet connectivity.')

    def coinbase_format_account(self, auth):
        accounts = auth.get_accounts()
        account_rv = ""
        for account in accounts['data']:
            account_rv += "\n" + account['balance']['currency'] + " Total: " + str(round(Decimal(account['balance']['amount']), 3))
        return account_rv

    def remove_rv_and_input_text(self):
        self.text_coinbase_key.text = ""
        self.text_coinbase_secret.text = ""
        self.recycle_view_coinbase.data = ""


class LabelWithBackground(Label):
    pass


class GdaxCurrencyScreen(Screen):
    def on_enter(self, *args):
        self.gdax_currencies_list()

    def gdax_currencies_list(self):
        app = App.get_running_app()
        gdax_trade_currencies = []

        for currency in app.gdax_currencies:
            if currency['id'] not in ["USD", "EUR", "GBP"]:
                pair = {"text": currency['id']}
                gdax_trade_currencies.append(pair.copy())
                app.gdax_trade_pairs.append(currency["id"] + "-USD")
        self.ids.gdax_currency_rv.data = gdax_trade_currencies


class GdaxCurrencyRecycleView(RecycleView):
    pass


class GdaxCurrencyViewClass(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty("")
    index = None

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super(GdaxCurrencyViewClass, self).refresh_view_attrs(rv, index, data)

    def set_trade_symbol(self, symbol):
        app = App.get_running_app()
        app.trade_symbol = symbol


class GdaxTradeScreen(Screen):
    min_crypto_size = ""
    crypto_ask_price = ""
    trade_config = ""

    def on_enter(self, *args):
        app = App.get_running_app()
        trade_pair = self.ids.trade_symbol.text + "-USD"

        try:
            self.crypto_ask_price = app.gdax_auth.get_product_order_book(trade_pair, level=1)['asks'][0][0]
            for product in app.gdax_products:
                if product['id'] == self.ids.trade_symbol.text + "-USD":
                    self.min_crypto_size = product['base_min_size']
        except:
            Alert('GDAX Order Book Retrieval', 'Please ensure your GDAX API is correct\nand that you have an internet connection.')

    def generate_investment_options(self, daily_amount):
        hourly_option_dict = {}
        hourly_option_list = []
        min_buy_amount = Decimal(self.crypto_ask_price) * Decimal(self.min_crypto_size)

        for i in range(24):
            hour = i + 1
            if (24 % hour) == 0:
                by_hour_investment = float("{0:.2f}".format(Decimal(daily_amount) * Decimal(hour) / Decimal(24)))
                if by_hour_investment > min_buy_amount:
                    hourly_option_dict[str(hour)] = by_hour_investment

        for hourly_option in hourly_option_dict:
            pair = {"text": "$" + str(hourly_option_dict[str(hourly_option)]) + " every " + str(hourly_option) + " hour(s)"}
            hourly_option_list.append(pair.copy())

        self.ids.gdax_trade_rv.data = hourly_option_list


class GdaxTradeRecycleView(LayoutSelectionBehavior, RecycleView):
    pass


class GdaxTradeViewClass(RecycleDataViewBehavior, GridLayout):
    text = StringProperty("")
    index = None

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super(GdaxTradeViewClass, self).refresh_view_attrs(rv, index, data)

    def set_trade_details(self, trade):
        app = App.get_running_app()
        app.trade_details = trade


class GdaxTradeConfirmationScreen(Screen):
    trade_pair = ""
    trade_amount_usd = ""
    trade_frequency = ""
    txn_dict = ""
    app_mode = "buy"

    def __init__(self, **kwargs):
        super(GdaxTradeConfirmationScreen, self).__init__(**kwargs)
        self.master_event = ""
        self.trade_event = ""
        self.txn_id = ""
        self.order_exists = False

    def on_enter(self, *args):
        app = App.get_running_app()
        trade = app.trade_details.split(' ')
        second_minute_convert = 3600
        self.trade_amount_usd = float(trade[0].replace("$", ""))
        self.trade_frequency = Decimal(trade[2])
        master_trade_frequency_seconds = second_minute_convert * self.trade_frequency
        self.trade_pair = app.trade_symbol + "-USD"
        self.ids.gdax_trade_confirmation_label.text = "Trading $" + str(self.trade_amount_usd) + " of "+ app.trade_symbol + " every " + str(self.trade_frequency) + " hour(s)."
        Clock.schedule_once(self.trade_till_fill, 0)
        self.master_event = Clock.schedule_interval(self.trade_till_fill, master_trade_frequency_seconds)

    def trade_till_fill(self, gt):
        app = App.get_running_app()
        if self.trade_event != "":
            self.trade_event.cancel()
        if self.txn_dict is None:
            self.txn_dict = ""
        if self.txn_dict != "":    # not self.txn_settled(self.txn_dict):
            app.gdax_auth.cancel_order(self.txn_dict['id'])
            self.order_exists = False
            self.txn_dict = ""
        Clock.schedule_once(lambda dt: self.gdax_clock_buy(self.app_mode), 0)
        self.trade_event = Clock.schedule_interval(lambda dt: self.gdax_clock_buy(self.app_mode), 30)

    def gdax_accounts(self):
        app = App.get_running_app()
        accounts = app.gdax_auth.get_accounts()
        return accounts

    def gdax_usd_available(self):
        for account in self.gdax_accounts():
            if account['currency'] == 'USD':
                return float("{0:.2f}".format(Decimal(account['available'])))

    def gdax_limit(self, ask_dict, order_limit=1):
        limit_price = math.floor((float(Decimal(ask_dict['price'])) - float(Decimal(0.005))) * 100) / 100
        tradeable_usd = float(Decimal(self.gdax_usd_available()) - Decimal(1.5))
        if tradeable_usd > order_limit:
            limit_quantity = float("{0:.8f}".format(order_limit / limit_price))
        else:
            limit_quantity = float("{0:.8f}".format(tradeable_usd / limit_price))
        return limit_price, limit_quantity

    def gdax_order_book(self, trade_pair):
        app = App.get_running_app()
        book_dict = app.gdax_auth.get_product_order_book(trade_pair, level=1)
        return book_dict

    def gdax_bid_ask(self, book_dict):
        bid_dict = {'price': book_dict['bids'][0][0], 'size': book_dict['bids'][0][1], 'orders': book_dict['bids'][0][2]}
        ask_dict = {'price': book_dict['asks'][0][0], 'size': book_dict['asks'][0][1], 'orders': book_dict['asks'][0][2]}
        return bid_dict, ask_dict

    def gdax_buy(self, trade_pair, trade_action="print", limit_order_amt=1, order_exists=False, txn_dict=""):
        app = App.get_running_app()

        if trade_pair in app.gdax_trade_pairs:
            order_book = self.gdax_order_book(trade_pair)
            bid, ask = self.gdax_bid_ask(order_book)
            order_price, order_quantity = self.gdax_limit(ask, limit_order_amt)
            if trade_action.upper() == "BUY":
                order_filled = self.txn_settled(txn_dict)
                if order_exists and not order_filled and order_price != float(txn_dict['price']):
                    app.gdax_auth.cancel_order(txn_dict['id'])
                    order_data = app.gdax_auth.buy(price=order_price, size=order_quantity, product_id=trade_pair)
                    self.order_exists = True
                    self.ids.gdax_order_label.text = app.trade_symbol + " order placed!\nOrder Quantity: " \
                                                     + str(order_quantity) + "\nCost Basis: $" + str(order_price)
                    return order_data
                elif order_exists and not order_filled and order_price == float(txn_dict['price']):
                    self.order_exists = True
                    self.ids.gdax_order_label.text = app.trade_symbol + " order placed!\nOrder Quantity: " \
                                                     + str(order_quantity) + "\nCost Basis: $" + str(order_price)
                    return txn_dict
                elif not order_exists and not order_filled:
                    order_data = app.gdax_auth.buy(price=order_price, size=order_quantity, product_id=trade_pair)
                    self.order_exists = True
                    self.ids.gdax_order_label.text = app.trade_symbol + " order placed!\nOrder Quantity: " \
                                                     + str(order_quantity) + "\nCost Basis: $" + str(order_price)
                    return order_data
                else:
                    return ""
            else:
                self.ids.gdax_order_label.text = app.trade_symbol + " order placed!\nOrder Quantity: " \
                                                 + str(order_quantity) + "\nCost Basis: $" + str(order_price)
        else:
            Alert("Invalid Trade Pair", "Please enter a valid trade pair ('BTC-USD', 'ETH-USD', 'LTC-USD') ->", trade_pair, "<- is not valid.")

    def txn_settled(self, txn):
        app = App.get_running_app()

        if txn != "":
            try:
                if app.gdax_auth.get_order(txn['id'])['settled']:
                    self.txn_dict = ""
                    self.trade_event.cancel()
                    self.order_exists = False
                    self.ids.gdax_order_label.text = "order fill size: " + str(txn['id']['filled_size']) \
                                                     + "\norder fill fees: " + str(txn['id']['fill_fees']) \
                                                     + "\norder fill value: " + str(txn['id']['executed_value'])
                    return True
                else:
                    return False
            except:
                txn_fill = app.gdax_auth.get_fills(order_id=txn['id'])
                if txn_fill[0][0]['settled']:
                    self.txn_dict = ""
                    self.trade_event.cancel()
                    self.order_exists = False
                    self.ids.gdax_order_label.text = "order fill size: " + str(txn_fill[0][0]['size']) \
                                                     + "\norder fill fees: " + str(txn_fill[0][0]['fee']) \
                                                     + "\norder fill price: " + str(txn_fill[0][0]['price'])
                    return True
                else:
                    Alert("Failed to Retrieve Order!", "An attempt was made to check an existing order\nplease check your internet connection!")
        else:
            return False

    def gdax_clock_buy(self, buy_mode="test"):
        self.txn_dict = self.gdax_buy(self.trade_pair, trade_action=buy_mode, limit_order_amt=self.trade_amount_usd, order_exists=self.order_exists, txn_dict=self.txn_dict)


class FloatInput(TextInput):
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            if len(self.text.split('.', 1)[1]) < 2:
                s = re.sub(pat, '', substring)
            else:
                s = ""
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


class Alert(Popup):
    def __init__(self, title, text):
        super(Alert, self).__init__()
        content = AnchorLayout(anchor_x='center', anchor_y='bottom')
        content.add_widget(
            Label(text=text, halign='center', valign='top')
        )
        ok_button = Button(text='Ok', size_hint=(.7, .25))
        content.add_widget(ok_button)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(.6, .3),
            auto_dismiss=True,
        )
        ok_button.bind(on_press=popup.dismiss)
        popup.open()


class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)


if __name__ == "__main__":
    DCAApp().run()
