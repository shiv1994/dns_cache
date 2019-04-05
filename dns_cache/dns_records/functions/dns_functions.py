import os, requests, json, socket
import dns.resolver, dns.zone, dns.query

def inDepthLookup(domain_name):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ['8.8.8.8']
    ns_answers = resolver.query(domain_name, 'NS')
    name_servers = []
    a_answers = resolver.query(domain_name, 'A')
    hostnames = []
    for rr in ns_answers:
        name_server = rr.target
        ip_address = dns.resolver.query(rr.target, 'A')[0].address
        name_servers.append({'name_server':name_server, 'ip_address':ip_address})
    for hostname in a_answers:
        hostnames.append({'host':domain_name, 'ip_address':hostname})
    return [name_servers, hostnames]


def determineLocalIPAddressCountry(domain_name):
    key = os.environ.get('IPINFODB_API_KEY')
    headers = {'content-type': 'application/json'}
    url = "http://api.ipinfodb.com/v3/ip-country/"
    params = {'key':key, 'format':'json'}
    if key is not None:
        response = requests.post(url, params = params, headers=headers)
        json_response = json.loads(response.text)
        return json_response
    else:
        return None


# determineLocalIPAddress('sta.uwi.edu')