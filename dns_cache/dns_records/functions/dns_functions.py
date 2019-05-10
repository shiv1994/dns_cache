import os, requests, json, socket
import dns.resolver, dns.zone, dns.query

def inDepthLookup(domain_name):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ['8.8.8.8']
    name_servers = []
    mx_answers = []
    try:
        ns_answers = resolver.query(domain_name, 'NS')
        for rr in ns_answers:
            name_server = rr.target
            ip_address = dns.resolver.query(rr.target, 'A')[0].address
            name_servers.append({'name_server':name_server, 'ip_address':ip_address})
    except:
        name_servers = None
    try:
        a_answers = resolver.query(domain_name, 'A')
    except:
        a_answers = None
    try:
        mx_ans = resolver.query(domain_name, 'MX')
        for mx in mx_ans:
            mx_answers.append({'priority':mx.preference, 'host':mx.exchange})
    except:
        mx_answers = None
    try:
        ipv6 = resolver.query(domain_name, 'AAAA')
    except:
        ipv6 = None
    # Returns nameservers, ipv4 address, mx servers, ipv6 address ...
    return [name_servers, a_answers, mx_answers, ipv6]


def determineLocalIPAddressCountry(domain_name):
    key = os.environ.get('IPINFODB_API_KEY')
    headers = {'content-type': 'application/json'}
    url = "http://api.ipinfodb.com/v3/ip-country/"
    params = {'key':key, 'format':'json', 'ip':domain_name}
    if key is not None:
        response = requests.post(url, params = params, headers=headers)
        json_response = json.loads(response.text)
        return json_response
    else:
        return None

# determineLocalIPAddress('sta.uwi.edu')
