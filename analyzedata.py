import json

instrument, granularity = "EUR_USD", "M15"
filename = r'C:\Users\vcucu\Documents\KTH_Q1\II2202 Research Methodology and Scientific Writing\tmp\One_{}_{}.json'.format(instrument, granularity)
#with open(filename, 'r') as f:
#        data = json.load(f)





input_file = open (filename)
json_array = json.load(input_file)
candles_list = []

for item in json_array:
    candle_details = {"complete":None, "volume":None, "time":None}
    candle_details['complete'] = item['complete']
    candle_details['volume'] = item['volume']
    candle_details['time'] = item['time']
    candles_list.append(candle_details)

print(candles_list)
