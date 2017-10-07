# Cryptocurrency Dollar Cost Averager

This is a tool to help automate the process of dollar cost averaging the purchase of cryptocurrencies.  It is designed to provide the user the ability to choose the amount to invest each day, the frequency of each purchase, and attempts to fill orders for the lowest fee each exchange allows.

__Disclaimer:__

*This is an alpha release and you assume all responsibility for using this version and should only use if you understand the consequences of executing these trades.  Cryptocurrencies are incredibly volatile and should be taken at your own risk, never invest more than you can afford to lose.  This alpha release offers basic/limited functionality and should be considered a proof of concept that is very bare bones with no consideration for UI design.*

## GDAX and Coinbase

At GDAX the lowest fee possible is free if you are able to be filled as a "market maker".  This tools first exchange to integrate with is GDAX since it offers the most liquid coins and has a robust API.  In the alpha release there is no functionality to reload the GDAX account to keep trading, this needs to be done manually.  This functionality will be added in a future release and is why the Coinbase API screen exists in this release.

* It is not required to enter the Coinbase API details in the Alpha release

### GDAX API Configuration

* [GDAX API Configuration](https://support.gdax.com/customer/en/portal/articles/2425383-how-can-i-create-an-api-key-for-gdax-)
  * Configure API with the ability to trade and permissions you feel comfortable with
  * You will need to enter the Key, Secret, and Passphrase
  * **Do not share your API Key!!**
