import oandapyV20
import oandapyV20.endpoints.accounts as accounts
client = oandapyV20.API(access_token='82957cd1a8234cf899f729284c094d27-e31e01c267351992774813f5e64c8b43')
r = accounts.AccountDetails("101-004-12401398-001")
client.request(r)
print(r.response)
