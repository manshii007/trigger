import http.client, urllib.parse

# **********************************************
# *** Update or verify the following values. ***
# **********************************************

# Replace the subscriptionKey string value with your valid subscription key.
subscriptionKey = '478373184b284fbabc3565b7028fd3f1'

host = 'api.microsofttranslator.com'
path = '/V2/Http.svc/Translate'


def get_suggestions():
    headers = {'Ocp-Apim-Subscription-Key': subscriptionKey}
    conn = http.client.HTTPSConnection(host)
    conn.request("GET", path + params, None, headers)
    response = conn.getresponse()
    return response.read()


while True:
    target = 'fr-fr'
    text = input("enter sentence : ")

    params = '?to=' + target + '&text=' + urllib.parse.quote (text)

    result = get_suggestions ()
    print (result.decode("utf-8"))