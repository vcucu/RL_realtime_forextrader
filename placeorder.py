import oandapyV20
import oandapyV20.endpoints.orders as orders

access_token = '82957cd1a8234cf899f729284c094d27-e31e01c267351992774813f5e64c8b43'
accountID = "101-004-12401398-001"
client = oandapyV20.API(access_token=access_token)



data = {
  "order": {
    "price": "1.2",
    "stopLossOnFill": {
      "timeInForce": "GTC",
      "price": "1.22"
    },
    "timeInForce": "GTC",
    "instrument": "EUR_USD",
    "units": "-100",
    "type": "LIMIT",
    "positionFill": "DEFAULT"
  }
}
r = orders.OrderCreate(accountID, data=data)
client.request(r)
print(r.response)
